"""Deterministic synthetic events for training, testing and demos (VS48).

A scenario is built in its own workspace through the real API, so every
invariant, audit row and permission applies. The workspace carries a
`DemoScenario` marker: purge refuses anything without it, and synthetic
accounts are only removed when they belong to no other workspace.
"""

import random
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from accounts.models import Session, User
from django.apps import apps
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.test import Client
from events.models import EventStatus, RegistrationStatus
from workspaces.models import Membership, Role, Workspace

from .archive import import_archive
from .final_archive import DEFERRED
from .models import DemoScenario

FIXED_AT = datetime(2026, 1, 10, 12, tzinfo=UTC)
MAX_PARTICIPANTS = 40
MAX_JUDGES = 12

TRACKS = ["AI for Good", "Developer Tools", "Open Data"]
ADJECTIVES = "Swift Quiet Bright Rugged Curious Modular Gentle Lucid Nimble Patient".split()
NOUNS = "Compass Beacon Ledger Lantern Harbor Atlas Loom Relay Signal Garden".split()
CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 2, "min_score": 1, "max_score": 10},
    {"id": "technical", "name": "Technical depth", "weight": 2, "min_score": 1, "max_score": 10},
    {"id": "design", "name": "Design and clarity", "weight": 1, "min_score": 1, "max_score": 10},
]


def scenario_archive(key, *, at):
    if key != "hackathon":
        raise ValidationError({"scenario": f"Unknown scenario {key!r}."})
    return {
        "format_version": 1,
        "mode": "config",
        "event": {
            "name": "Demo Hackathon",
            "slug": "demo-hackathon",
            "description": "Synthetic event generated for training and demos.",
            "timezone": "UTC",
            "starts_at": (at - timedelta(days=1)).isoformat(),
            "ends_at": (at + timedelta(days=1)).isoformat(),
            "status": "draft",
            "is_public": False,
        },
        "tracks": [
            {"ref": f"track-{i}", "name": name, "description": "", "position": i}
            for i, name in enumerate(TRACKS)
        ],
        "base_prizes": [],
        "stages": [
            {
                "ref": "build",
                "name": "Build",
                "position": 0,
                "is_initial": True,
                "participation_mode": "team_formation",
            }
        ],
        "stage_transitions": [],
        "forms": [],
        "policies": [],
        "temporal_gates": [],
        "policy_bindings": [],
        "awards": [
            {
                "ref": "grand",
                "name": "Grand Prize",
                "description": "Highest normalized score overall.",
                "eligibility_track_ref": None,
                "require_finalized_submission": True,
                "selection_source": "evaluation",
                "evaluation_plan_name": "Main judging",
                "winner_count": 1,
                "allow_stacking": True,
                "conflict_group": "",
                "components": [
                    {
                        "kind": "cash",
                        "name": "Cash prize",
                        "description": "",
                        "quantity": 1,
                        "amount": "1000.00",
                        "currency": "USD",
                        "position": 0,
                    }
                ],
            },
            *[
                {
                    "ref": f"best-{i}",
                    "name": f"Best in {name}",
                    "description": "",
                    "eligibility_track_ref": f"track-{i}",
                    "require_finalized_submission": True,
                    "selection_source": "evaluation",
                    "evaluation_plan_name": "Main judging",
                    "winner_count": 1,
                    "allow_stacking": True,
                    "conflict_group": "",
                    "components": [],
                }
                for i, name in enumerate(TRACKS)
            ],
        ],
        "evaluation_plans": [
            {
                "ref": "plan",
                "stage_ref": "build",
                "name": "Main judging",
                "candidate_type": "project",
                "pool_strategy": "all_judges",
                "results_visible_to_participants": True,
                "rubric_versions": [{"number": 1, "criteria": CRITERIA}],
            }
        ],
        "pages": [
            {
                "theme": "default",
                "blocks": [
                    {
                        "kind": "hero",
                        "position": 0,
                        "config": {"title": "Demo Hackathon", "subtitle": "Synthetic data"},
                    }
                ],
            }
        ],
    }


def _host():
    return next(
        (h.lstrip(".") for h in django_settings.ALLOWED_HOSTS if h and h != "*"), "localhost"
    )


class _Replay:
    def __init__(self, event):
        self.event = event
        self.prefix = f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"

    def client(self, user):
        client = Client(HTTP_HOST=_host())
        client.cookies["session"] = Session.issue(user).token
        return client

    def call(self, client, method, path, data=None, *, expected=200):
        response = getattr(client, method)(
            self.prefix + path, data=data or {}, content_type="application/json"
        )
        if response.status_code != expected:
            raise ValidationError(
                {
                    "scenario": f"{method.upper()} {path} returned {response.status_code}: "
                    f"{response.content[:200].decode(errors='replace')}"
                }
            )
        return response.json()


def _score(rng, quality, bias, low, high):
    return max(low, min(high, round(quality + bias + rng.gauss(0, 0.7))))


@transaction.atomic
def generate_demo_event(
    *, scenario="hackathon", seed=1, participants=8, judges=4, password=None, public=False, at=None
):
    if not 3 <= participants <= MAX_PARTICIPANTS or not 2 <= judges <= MAX_JUDGES:
        raise ValidationError(
            {"scenario": f"Use 3-{MAX_PARTICIPANTS} participants and 2-{MAX_JUDGES} judges."}
        )
    at = at or FIXED_AT
    if at.tzinfo is None:
        raise ValidationError({"at": "Include a timezone."})
    slug = f"demo-{scenario}-{seed}"
    if Workspace.objects.filter(slug=slug).exists():
        raise ValidationError({"scenario": f"{slug} already exists; purge it first."})
    rng = random.Random(f"{scenario}:{seed}")
    workspace = Workspace.objects.create(name=f"Demo {scenario} #{seed}", slug=slug)
    DemoScenario.objects.create(
        workspace=workspace, scenario=scenario, seed=seed, participants=participants, judges=judges
    )
    prefix = f"demo-{scenario}-{seed}"

    def account(label, role):
        user = User.objects.create_user(username=f"{prefix}-{label}", password=password)
        Membership.objects.create(workspace=workspace, user=user, role=role)
        return user

    with patch("django.utils.timezone.now", return_value=at):
        event = import_archive(
            workspace=workspace, archive=scenario_archive(scenario, at=at), name="Demo", slug="demo"
        )
        event.status = EventStatus.OPEN
        event.save(update_fields=["status", "updated_at"])
        replay = _Replay(event)
        organizer = account("organizer", Role.ORGANIZER)
        organizer_client = replay.client(organizer)
        plan = event.stages.get().evaluation_plans.get()
        plan_path = f"stages/{plan.stage.public_id}/evaluation-plans/{plan.public_id}/"
        track_ids = [str(t.public_id) for t in event.tracks.order_by("position")]
        names = [f"{a} {n}" for a in ADJECTIVES for n in NOUNS]
        rng.shuffle(names)
        projects = []
        for index in range(participants):
            user = account(f"participant-{index + 1:02d}", Role.PARTICIPANT)
            client = replay.client(user)
            application = replay.call(client, "post", "my-application/", expected=201)
            if application["status"] == RegistrationStatus.PENDING:
                application = replay.call(
                    organizer_client,
                    "post",
                    f"applications/{application['public_id']}/decide/",
                    {"decision": RegistrationStatus.APPROVED},
                )
            team = replay.call(
                client, "post", "my-team/", {"name": f"Team {names[index]}"}, expected=201
            )
            project = replay.call(
                client,
                "post",
                "projects/",
                {
                    "name": names[index],
                    "description": f"{names[index]} explores {rng.choice(TRACKS).lower()}.",
                    "team": team["public_id"],
                    "track": track_ids[index % len(track_ids)],
                },
                expected=201,
            )
            submission = f"projects/{project['public_id']}/submissions/{plan.stage.public_id}/"
            draft = replay.call(
                client,
                "put",
                submission,
                {"draft_payload": {"notes": f"Notes for {names[index]}"}, "draft_revision": 0},
            )
            replay.call(
                client,
                "post",
                submission + "finalize/",
                {"draft_revision": draft["draft_revision"]},
                expected=201,
            )
            projects.append({"id": project["public_id"], "quality": rng.uniform(3.5, 8.5)})
        for index in range(judges):
            judge = account(f"judge-{index + 1:02d}", Role.JUDGE)
            client, bias = replay.client(judge), rng.uniform(-1.5, 1.5)
            for project in projects:
                replay.call(
                    client,
                    "post",
                    plan_path + "ballots/",
                    {
                        "project": project["id"],
                        "responses": [
                            {
                                "criterion_id": criterion["id"],
                                "score": _score(
                                    rng,
                                    project["quality"],
                                    bias,
                                    criterion["min_score"],
                                    criterion["max_score"],
                                ),
                            }
                            for criterion in CRITERIA
                        ],
                    },
                    expected=201,
                )
        run = replay.call(organizer_client, "post", plan_path + "normalization-runs/", expected=201)
        replay.call(
            organizer_client,
            "post",
            plan_path + "publish-results/",
            {"normalization_run": run["public_id"]},
        )
        ranking = replay.call(organizer_client, "get", plan_path + "results/")
        track_of = {
            str(p.public_id): str(p.track.public_id) for p in event.projects.select_related("track")
        }
        for award in replay.call(organizer_client, "get", "awards/"):
            eligible = (award["eligibility_track"] and str(award["eligibility_track"])) or None
            winner = next(
                row["project"]
                for row in ranking
                if eligible is None or track_of[str(row["project"])] == eligible
            )
            base = f"awards/{award['public_id']}/"
            replay.call(
                organizer_client, "post", base + "winners/", {"project": str(winner)}, expected=201
            )
            replay.call(organizer_client, "post", base + "publish/")
        event.refresh_from_db()
        event.status = EventStatus.CLOSED
        event.is_public = public
        event.save(update_fields=["status", "is_public", "updated_at"])
    Session.objects.filter(user__username__startswith=prefix + "-").delete()
    return event


def _delete_with_dependents(instance, *, budget=10000):
    """Peel PROTECT references (results, ballots, submissions) that only exist
    inside the synthetic workspace being purged; the marker gates every caller.
    """
    while budget:
        try:
            # Queryset deletion bypasses the per-row immutability guards on purpose.
            type(instance)._default_manager.filter(pk=instance.pk).delete()
            return budget
        except ProtectedError as exc:
            for dependent in list(exc.protected_objects):
                budget = _delete_with_dependents(dependent, budget=budget - 1)
    raise ValidationError({"scenario": "Purge exceeded its dependency budget."})


def purge_demo_scenario(slug):
    marker = DemoScenario.objects.filter(workspace__slug=slug).select_related("workspace").first()
    if marker is None:
        raise ValidationError({"scenario": "Only generated demo scenarios can be purged."})
    prefix = f"demo-{marker.scenario}-{marker.seed}-"
    with transaction.atomic():
        accounts = User.objects.filter(username__startswith=prefix)
        shared = Membership.objects.filter(user__in=accounts).exclude(workspace=marker.workspace)
        removable = accounts.exclude(pk__in=shared.values("user"))
        for label, field in DEFERRED:
            model = apps.get_model(label)
            event_path = "project__event" if label == "projects.submission" else "stage__event"
            model.objects.filter(**{f"{event_path}__workspace": marker.workspace}).update(
                **{field: None}
            )
        _delete_with_dependents(marker.workspace)
        removable.delete()
