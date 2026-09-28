"""PVS11 endpoints. Participant-facing reads are scoped to the caller's own
projects and assignments; organizer surfaces carry the decision powers."""

from accounts.authentication import CookieSessionAuthentication
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember, require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from evaluations.models import Assignment, EvaluationPlan
from events.models import Event
from projects.models import Project, SubmissionVersion
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

from . import services
from .models import (
    AssignmentResponse,
    DeadlineExceptionRequest,
    GovernanceSettings,
    PublicationRequest,
    RequestStatus,
    ResultCorrection,
    RulesAcknowledgement,
)
from .schema import (
    AssignmentResponseInput,
    CsvPreviewInput,
    DecisionNoteInput,
    ExceptionApprovalInput,
    ExceptionRequestInput,
    MaintenanceInput,
    ParticipantRulesInput,
    PublicationRequestInput,
    RulesAcknowledgeInput,
    SettingsInput,
    VisibilityInput,
)


def guarded(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ModelValidationError as exc:
            raise ValidationError(exc.messages) from exc

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


class EventView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        if not hasattr(self, "_workspace"):
            self._workspace = get_object_or_404(
                Workspace, public_id=self.kwargs["workspace_public_id"]
            )
        return self._workspace

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    def is_organizer(self, request):
        return has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)

    def get_project(self):
        return get_object_or_404(
            Project, event=self.get_event(), public_id=self.kwargs["project_public_id"]
        )

    def member_project(self, request):
        """A project the caller belongs to (or any project, for organizers). Anything else
        is a 404 so project existence is not disclosed across teams."""
        project = self.get_project()
        if not (
            self.is_organizer(request) or project.memberships.filter(user=request.user).exists()
        ):
            from django.http import Http404

            raise Http404
        return project

    def get_plan(self):
        stage = get_object_or_404(
            Stage, event=self.get_event(), public_id=self.kwargs["stage_public_id"]
        )
        return get_object_or_404(
            EvaluationPlan, stage=stage, public_id=self.kwargs["plan_public_id"]
        )


class OrganizerEventView(EventView):
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]


def _iso(value):
    return value.isoformat() if value else None


# Settings


class GovernanceSettingsView(OrganizerEventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        row = GovernanceSettings.objects.filter(event=self.get_event()).first()
        return Response(
            {"require_publication_approval": bool(row and row.require_publication_approval)}
        )

    @extend_schema(request=SettingsInput, responses=None)
    @guarded
    def put(self, request, workspace_public_id, event_public_id):
        value = request.data.get("require_publication_approval")
        if not isinstance(value, bool):
            raise ValidationError({"require_publication_approval": "Must be a boolean."})
        row = services.set_settings(
            self.get_event(), request.user, require_publication_approval=value
        )
        return Response({"require_publication_approval": row.require_publication_approval})


# Rules


def _rules_data(version, *, include_body=True):
    data = {
        "number": version.number,
        "title": version.title,
        "published_at": _iso(version.created_at),
    }
    if include_body:
        data["body"] = version.body
    return data


class RulesView(EventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        current = services.current_rules(event)
        acknowledged = bool(
            current
            and RulesAcknowledgement.objects.filter(version=current, user=request.user).exists()
        )
        return Response(
            {
                "current": _rules_data(current) if current else None,
                "acknowledged": acknowledged,
                "versions": [
                    _rules_data(v, include_body=False) for v in event.rules_versions.all()
                ],
            }
        )

    @extend_schema(request=ParticipantRulesInput, responses=None)
    @guarded
    def post(self, request, workspace_public_id, event_public_id):
        if not self.is_organizer(request):
            self.permission_denied(request)
        version = services.publish_rules(
            self.get_event(),
            request.user,
            title=str(request.data.get("title", "")),
            body=str(request.data.get("body", "")),
        )
        return Response(_rules_data(version), status=201)


class RulesVersionView(EventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id, number):
        version = get_object_or_404(self.get_event().rules_versions, number=number)
        return Response(_rules_data(version))


class RulesAcknowledgeView(EventView):
    @extend_schema(request=RulesAcknowledgeInput, responses=None)
    @guarded
    def post(self, request, workspace_public_id, event_public_id):
        number = request.data.get("number")
        if number is not None and (not isinstance(number, int) or isinstance(number, bool)):
            raise ValidationError({"number": "Must be an integer."})
        ack, created = services.acknowledge_rules(self.get_event(), request.user, number=number)
        return Response(
            {"number": ack.version.number, "acknowledged_at": _iso(ack.created_at)},
            status=201 if created else 200,
        )


class RulesAcknowledgementListView(OrganizerEventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        current = services.current_rules(event)
        if current is None:
            return Response({"number": None, "acknowledged": [], "pending": []})
        acks = list(current.acks.select_related("user").order_by("created_at"))
        acked_ids = {a.user_id for a in acks}
        pending = (
            Membership.objects.filter(workspace=event.workspace, role=Role.PARTICIPANT)
            .exclude(user_id__in=acked_ids)
            .select_related("user")
            .order_by("user__username")
        )
        return Response(
            {
                "number": current.number,
                "acknowledged": [
                    {"user": a.user.username, "acknowledged_at": _iso(a.created_at)} for a in acks
                ],
                "pending": [m.user.username for m in pending],
            }
        )


# Publication approval and corrections


def _publication_data(item):
    return {
        "public_id": str(item.public_id),
        "plan": str(item.plan.public_id),
        "normalization_run": str(item.normalization_run.public_id),
        "normalization_run_number": item.normalization_run.number,
        "status": item.status,
        "reason": item.reason,
        "requested_by": item.requested_by.username,
        "decided_by": item.decided_by.username if item.decided_by else None,
        "decision_note": item.decision_note,
        "created_at": _iso(item.created_at),
        "decided_at": _iso(item.decided_at),
    }


class PublicationRequestListView(OrganizerEventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        items = PublicationRequest.objects.filter(
            plan__stage__event=self.get_event()
        ).select_related("plan", "normalization_run", "requested_by", "decided_by")
        return Response([_publication_data(i) for i in items])

    @extend_schema(request=PublicationRequestInput, responses=None)
    @guarded
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        plan = get_object_or_404(
            EvaluationPlan, stage__event=event, public_id=request.data.get("plan")
        )
        run = services.normalization_run_or_none(plan, request.data.get("normalization_run"))
        if run is None:
            raise ValidationError({"normalization_run": "Unknown normalization run for this plan."})
        item = services.request_publication(
            plan,
            request.user,
            run=run,
            tie_breaks=request.data.get("tie_breaks", {}),
            reason=str(request.data.get("reason", "")),
        )
        return Response(_publication_data(item), status=201)


class PublicationRequestActionView(OrganizerEventView):
    action = ""

    def get_request(self):
        return get_object_or_404(
            PublicationRequest.objects.select_related(
                "plan", "normalization_run", "requested_by", "decided_by"
            ),
            plan__stage__event=self.get_event(),
            public_id=self.kwargs["request_public_id"],
        )

    @extend_schema(request=DecisionNoteInput, responses=None)
    @guarded
    def post(self, request, workspace_public_id, event_public_id, request_public_id):
        item = self.get_request()
        if self.action == "cancel":
            item = services.cancel_publication(item, request.user)
        else:
            item = services.decide_publication(
                item,
                request.user,
                approve=self.action == "approve",
                note=str(request.data.get("note", "")),
            )
        item.refresh_from_db()
        return Response(_publication_data(item))


def _correction_data(item):
    return {
        "public_id": str(item.public_id),
        "plan": item.plan.name,
        "plan_id": str(item.plan.public_id),
        "previous_run": item.previous_run.number if item.previous_run else None,
        "run": item.run.number,
        "reason": item.reason,
        "corrected_at": _iso(item.created_at),
    }


class ResultCorrectionListView(EventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        items = ResultCorrection.objects.filter(plan__stage__event=self.get_event()).select_related(
            "plan", "run", "previous_run"
        )
        if not self.is_organizer(request):
            items = items.filter(plan__results_visible_to_participants=True)
        return Response([_correction_data(i) for i in items])


class PublicResultCorrectionListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: {"type": "array", "items": {"type": "object"}}})
    def get(self, request, event_public_id):
        event = get_object_or_404(Event, public_id=event_public_id, is_public=True)
        items = ResultCorrection.objects.filter(
            plan__stage__event=event, plan__results_visible_to_participants=True
        ).select_related("plan", "run", "previous_run")
        return Response([_correction_data(i) for i in items])


# Receipts


class SubmissionReceiptView(EventView):
    @extend_schema(request=None, responses=None)
    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, stage_public_id
    ):
        project = self.member_project(request)
        stage = get_object_or_404(Stage, event=project.event, public_id=stage_public_id)
        versions = SubmissionVersion.objects.filter(
            submission__project=project, submission__stage=stage
        )
        number = request.query_params.get("version")
        if number is not None:
            if not number.isdigit():
                raise ValidationError({"version": "Must be a version number."})
            versions = versions.filter(number=int(number))
        version = versions.order_by("-number").first()
        if version is None:
            return Response({"detail": "No finalized version."}, status=404)
        receipt = services.issue_receipt(version)
        from presentation.records import verify_record

        return Response(
            {
                "token": receipt.token,
                "claims": verify_record(receipt.token),
                "issued_at": _iso(receipt.issued_at),
            }
        )


# Judge assignment accept/decline


class MyAssignmentsView(EventView):
    permission_classes = [require_roles(Role.JUDGE)]

    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        version = plan.active_assignment_version
        rows = []
        if version:
            for a in Assignment.objects.filter(version=version, judge=request.user).select_related(
                "project"
            ):
                response = AssignmentResponse.objects.filter(assignment=a).first()
                rows.append(
                    {
                        "project": str(a.project.public_id),
                        "name": a.project.name,
                        "status": response.status if response else "pending",
                        "reason": response.reason if response else "",
                    }
                )
        return Response(rows)


class AssignmentRespondView(EventView):
    permission_classes = [require_roles(Role.JUDGE)]

    @extend_schema(request=AssignmentResponseInput, responses=None)
    @guarded
    def post(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        project_public_id,
    ):
        plan = self.get_plan()
        project = self.get_project()
        decision = request.data.get("status")
        if decision not in ("accepted", "declined"):
            raise ValidationError({"status": "Must be 'accepted' or 'declined'."})
        response = services.respond_to_assignment(
            plan,
            request.user,
            project,
            accept=decision == "accepted",
            reason=str(request.data.get("reason", "")),
        )
        return Response({"project": str(project.public_id), "status": response.status})


class AssignmentResponseSummaryView(OrganizerEventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        version = plan.active_assignment_version
        counts = {"pending": 0, "accepted": 0, "declined": 0}
        declined = []
        if version:
            assignments = Assignment.objects.filter(version=version).select_related(
                "judge", "project"
            )
            responses = {
                r.assignment_id: r
                for r in AssignmentResponse.objects.filter(assignment__version=version)
            }
            for a in assignments:
                r = responses.get(a.id)
                counts[r.status if r else "pending"] += 1
                if r and r.status == "declined":
                    declined.append(
                        {
                            "judge": a.judge.username,
                            "project": str(a.project.public_id),
                            "name": a.project.name,
                            "reason": r.reason,
                        }
                    )
        return Response({"counts": counts, "declined": declined})


# Deadline-exception requests


def _exception_data(item):
    return {
        "public_id": str(item.public_id),
        "project": str(item.project.public_id),
        "action": item.action,
        "reason": item.reason,
        "status": item.status,
        "requested_by": item.requested_by.username,
        "decision_note": item.decision_note,
        "grant_expires_at": _iso(item.grant.expires_at) if item.grant else None,
        "created_at": _iso(item.created_at),
        "decided_at": _iso(item.decided_at),
    }


class ProjectExceptionRequestView(EventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        items = project.deadline_exception_requests.select_related("requested_by", "grant")
        return Response([_exception_data(i) for i in items])

    @extend_schema(request=ExceptionRequestInput, responses=None)
    @guarded
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        item = services.request_exception(
            project, request.user, reason=str(request.data.get("reason", ""))
        )
        return Response(_exception_data(item), status=201)


class ExceptionRequestListView(OrganizerEventView):
    @extend_schema(request=None, responses=None)
    def get(self, request, workspace_public_id, event_public_id):
        items = DeadlineExceptionRequest.objects.filter(event=self.get_event()).select_related(
            "project", "requested_by", "grant"
        )
        status = request.query_params.get("status")
        if status in RequestStatus.values:
            items = items.filter(status=status)
        return Response([_exception_data(i) for i in items])


class ExceptionRequestActionView(EventView):
    action = ""

    @extend_schema(request=ExceptionApprovalInput, responses=None)
    @guarded
    def post(self, request, workspace_public_id, event_public_id, request_public_id):
        item = get_object_or_404(
            DeadlineExceptionRequest.objects.select_related("project", "requested_by", "grant"),
            event=self.get_event(),
            public_id=request_public_id,
        )
        if self.action == "cancel":
            if item.requested_by_id != request.user.pk:
                from django.http import Http404

                raise Http404
            item = services.cancel_exception(item, request.user)
        else:
            if not self.is_organizer(request):
                self.permission_denied(request)
            expires_at = None
            if self.action == "approve":
                raw = request.data.get("expires_at")
                expires_at = parse_datetime(raw) if isinstance(raw, str) else None
                if expires_at is None or expires_at.tzinfo is None:
                    raise ValidationError(
                        {"expires_at": "A timezone-aware ISO datetime is required."}
                    )
            item = services.decide_exception(
                item,
                request.user,
                approve=self.action == "approve",
                note=str(request.data.get("note", "")),
                expires_at=expires_at,
            )
        item.refresh_from_db()
        return Response(_exception_data(item))


class MaintenanceView(EventView):
    @extend_schema(responses={200: {"type": "object"}})
    def get(self, request, workspace_public_id, event_public_id):
        row = GovernanceSettings.objects.filter(event=self.get_event()).first()
        return Response(
            {
                "read_only": bool(row and row.read_only),
                "message": row.read_only_message if row and row.read_only else "",
            }
        )

    @extend_schema(request=MaintenanceInput, responses={200: {"type": "object"}})
    @guarded
    def put(self, request, workspace_public_id, event_public_id):
        if not self.is_organizer(request):
            self.permission_denied(request)
        flag = request.data.get("read_only")
        message = request.data.get("message", "")
        if not isinstance(flag, bool) or not isinstance(message, str):
            raise ValidationError({"read_only": "Must be a boolean; message must be text."})
        row = services.set_read_only(
            self.get_event(), request.user, read_only=flag, message=message
        )
        return Response({"read_only": row.read_only, "message": row.read_only_message})


class ProjectVisibilityView(EventView):
    def state(self, project, request):
        data = {"gallery_visible": project.gallery_visible}
        if project.gallery_blocked:
            data["blocked_by_organizer"] = True
        return data

    @extend_schema(responses={200: {"type": "object"}})
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        return Response(self.state(self.member_project(request), request))

    @extend_schema(request=VisibilityInput, responses={200: {"type": "object"}})
    @guarded
    def put(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.member_project(request)
        gallery_visible = request.data.get("gallery_visible")
        blocked = request.data.get("blocked")
        for name, value in (("gallery_visible", gallery_visible), ("blocked", blocked)):
            if value is not None and not isinstance(value, bool):
                raise ValidationError({name: "Must be a boolean."})
        if gallery_visible is None and blocked is None:
            raise ValidationError({"gallery_visible": "Provide gallery_visible or blocked."})
        project = services.set_visibility(
            project,
            request.user,
            gallery_visible=gallery_visible,
            blocked=blocked,
            reason=str(request.data.get("reason", "")),
        )
        return Response(self.state(project, request))


class CsvPreviewView(OrganizerEventView):
    @extend_schema(request=CsvPreviewInput, responses={200: {"type": "object"}})
    @guarded
    def post(self, request, workspace_public_id, event_public_id):
        from .csv_preview import preview

        return Response(
            preview(self.get_event(), request.data.get("csv_text"), request.data.get("mapping"))
        )


class MyDataExportView(EventView):
    @extend_schema(responses={200: {"type": "object"}})
    def get(self, request, workspace_public_id, event_public_id):
        from integrations.privacy import export_subject, subject_exists

        event = self.get_event()
        if not subject_exists(event, request.user):
            return Response({"detail": "You have no data in this event."}, status=404)
        return Response(export_subject(event, request.user, actor=request.user))
