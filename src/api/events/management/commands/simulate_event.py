import json
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from accounts.models import Session, User
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.test import Client
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from evaluations.models import (
    EvaluationMode,
    EvaluationPlan,
    EvaluationPoolStrategy,
    PoolMembership,
)
from workspaces.models import Membership, Role

from events.models import Event, EventStatus, RegistrationMode, RegistrationStatus
from events.registration import get_settings


class SimulationBlocked(Exception):
    pass


def simulate_event(event_id, plan_id, *, participants=2, judges=2, at=None):
    if not 1 <= participants <= 10 or not 1 <= judges <= 10:
        raise ValueError("Participant and judge counts must each be between 1 and 10.")
    report = {"passed": False, "persisted": False, "steps": [], "overlays": []}
    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(public_id=event_id)
            plan = EvaluationPlan.objects.select_for_update().get(
                public_id=plan_id, stage__event=event
            )
            if event.status != EventStatus.DRAFT or event.projects.exists():
                raise SimulationBlocked("Use a draft event without operational projects.")
            if (
                plan.mode != EvaluationMode.RUBRIC
                or plan.pool_strategy != EvaluationPoolStrategy.ALL_JUDGES
                or plan.prize_judging
                or plan.calibration_required
            ):
                raise SimulationBlocked(
                    "This simulator supports standard all-judge rubric plans only."
                )
            instant = at or max(timezone.now(), event.starts_at or timezone.now()) + timedelta(
                seconds=1
            )
            if timezone.is_naive(instant):
                raise ValueError("Simulation time must include a timezone.")
            report["at"] = instant.isoformat()
            report["overlays"] = [
                "event status: open",
                "synthetic participants and judges",
                "isolated process clock",
            ]
            # Only this standalone process uses the simulated clock. No HTTP
            # endpoint exposes it; rollback discards records and on-commit work.
            with patch("django.utils.timezone.now", return_value=instant):
                event.status = EventStatus.OPEN
                event.save(update_fields=["status", "updated_at"])
                prefix = f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"
                plan_prefix = (
                    prefix + f"stages/{plan.stage.public_id}/evaluation-plans/{plan.public_id}/"
                )
                run_id = uuid4().hex

                def actor(label, role=None):
                    user = User.objects.create_user(username=f"sim-{run_id}-{label}")
                    if role:
                        Membership.objects.create(workspace=event.workspace, user=user, role=role)
                    host = next(
                        (
                            host.lstrip(".")
                            for host in django_settings.ALLOWED_HOSTS
                            if host and host != "*"
                        ),
                        "localhost",
                    )
                    client = Client(HTTP_HOST=host)
                    client.cookies["session"] = Session.issue(user).token
                    return user, client

                def call(client, method, path, data=None, *, expected=200, step):
                    response = getattr(client, method)(
                        path, data=data or {}, content_type="application/json"
                    )
                    try:
                        payload = response.json()
                    except ValueError:
                        payload = {"detail": "Endpoint returned a non-JSON response."}
                    report["steps"].append({"step": step, "status": response.status_code})
                    if response.status_code != expected:
                        report["failure"] = {
                            "step": step,
                            "status": response.status_code,
                            "detail": payload,
                        }
                        raise SimulationBlocked(f"{step} failed ({response.status_code}).")
                    return payload

                _, organizer = actor("organizer", Role.ORGANIZER)
                settings = get_settings(event)
                invite = None
                if settings.mode == RegistrationMode.INVITE_ONLY:
                    invite = call(
                        organizer,
                        "post",
                        prefix + "registration-invite-codes/",
                        {"max_uses": participants},
                        expected=201,
                        step="create invitation",
                    )["code"]
                projects = []
                for index in range(participants):
                    _, client = actor(f"participant-{index}")
                    application = call(
                        client,
                        "post",
                        prefix + "my-application/",
                        {"code": invite} if invite else {},
                        expected=201,
                        step=f"register participant {index + 1}",
                    )
                    if application["status"] == RegistrationStatus.PENDING:
                        application = call(
                            organizer,
                            "post",
                            prefix + f"applications/{application['public_id']}/decide/",
                            {"decision": RegistrationStatus.APPROVED},
                            step=f"approve participant {index + 1}",
                        )
                    if application["status"] != RegistrationStatus.APPROVED:
                        raise SimulationBlocked(
                            f"Participant {index + 1} is {application['status']}."
                        )
                    project = call(
                        client,
                        "post",
                        prefix + "projects/",
                        {"name": f"Synthetic project {index + 1}"},
                        expected=201,
                        step=f"create project {index + 1}",
                    )
                    submission = (
                        prefix
                        + f"projects/{project['public_id']}/submissions/{plan.stage.public_id}/"
                    )
                    draft = call(
                        client,
                        "put",
                        submission,
                        {"draft_payload": {"notes": "Synthetic rehearsal"}, "draft_revision": 0},
                        step=f"draft submission {index + 1}",
                    )
                    call(
                        client,
                        "post",
                        submission + "finalize/",
                        {"draft_revision": draft["draft_revision"]},
                        expected=201,
                        step=f"finalize submission {index + 1}",
                    )
                    projects.append(project["public_id"])
                if plan.current_rubric_version is None:
                    call(
                        organizer,
                        "post",
                        plan_prefix + "publish-rubric/",
                        expected=201,
                        step="publish rubric",
                    )
                criteria = plan.current_rubric_version.criteria
                for index in range(judges):
                    user, client = actor(f"judge-{index}", Role.JUDGE)
                    if plan.pool_id:
                        PoolMembership.objects.create(pool=plan.pool, judge=user)
                    for project_id in projects:
                        call(
                            client,
                            "post",
                            plan_prefix + "ballots/",
                            {
                                "project": project_id,
                                "responses": [
                                    {
                                        "criterion_id": criterion["id"],
                                        "score": (criterion["min_score"] + criterion["max_score"])
                                        / 2,
                                    }
                                    for criterion in criteria
                                ],
                            },
                            expected=201,
                            step=f"judge {index + 1} project {projects.index(project_id) + 1}",
                        )
                run = call(
                    organizer,
                    "post",
                    plan_prefix + "normalization-runs/",
                    expected=201,
                    step="normalize results",
                )
                call(
                    organizer,
                    "post",
                    plan_prefix + "publish-results/",
                    {"normalization_run": run["public_id"]},
                    step="publish results",
                )
                results = call(
                    organizer, "get", plan_prefix + "results/", step="read published results"
                )
                if (
                    not isinstance(results, list)
                    or len(results) != len(projects)
                    or {row.get("project") for row in results} != set(projects)
                ):
                    raise SimulationBlocked(
                        "Published ranking does not cover the synthetic projects."
                    )
                report["result"] = results
                report["passed"] = True
        except SimulationBlocked as exc:
            report.setdefault("failure", {"detail": str(exc)})
        finally:
            transaction.set_rollback(True)
    return report


class Command(BaseCommand):
    help = "Rehearse a draft rubric event through the real API; always roll back synthetic data."

    def add_arguments(self, parser):
        parser.add_argument("event_id")
        parser.add_argument("plan_id")
        parser.add_argument("--participants", type=int, default=2)
        parser.add_argument("--judges", type=int, default=2)
        parser.add_argument(
            "--at", help="Timezone-aware ISO timestamp; defaults to now or just after event start."
        )

    def handle(self, *args, **options):
        try:
            at = parse_datetime(options["at"]) if options["at"] else None
            if options["at"] and at is None:
                raise ValueError("Use a valid ISO timestamp for --at.")
            report = simulate_event(
                options["event_id"],
                options["plan_id"],
                participants=options["participants"],
                judges=options["judges"],
                at=at,
            )
        except (
            ValueError,
            ValidationError,
            Event.DoesNotExist,
            EvaluationPlan.DoesNotExist,
        ) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(report, indent=2))
        if not report["passed"]:
            raise CommandError(
                "Simulation blocked; see the JSON report. No synthetic data retained."
            )
