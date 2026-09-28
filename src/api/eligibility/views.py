from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event, EventStatus
from events.views import OrganizerView
from projects.models import Project, ProjectMembership
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from . import services
from .models import (
    EligibilityFinding,
    EligibilityReview,
    EligibilityRules,
    FindingSeverity,
    FindingState,
    ReviewStatus,
)


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict) and data.keys() - self.fields.keys():
            raise ValidationError({"non_field_errors": ["Unknown fields."]})
        return super().to_internal_value(data)


class RulesInput(StrictInput):
    min_team_size = serializers.IntegerField(min_value=1, max_value=100, allow_null=True)
    max_team_size = serializers.IntegerField(min_value=1, max_value=100, allow_null=True)
    required_artifact_kinds = serializers.ListField(child=serializers.CharField(), max_length=20)
    require_finalized_submission = serializers.BooleanField()
    require_track = serializers.BooleanField()
    require_clearance = serializers.BooleanField()


class RulesOutput(RulesInput):
    updated_at = serializers.DateTimeField(allow_null=True)


class FindingInput(StrictInput):
    message = serializers.CharField(max_length=500)
    severity = serializers.ChoiceField(choices=FindingSeverity.choices, default="blocking")


class RespondInput(StrictInput):
    response = serializers.CharField(max_length=1000)


class CloseInput(StrictInput):
    state = serializers.ChoiceField(choices=[FindingState.RESOLVED, FindingState.WAIVED])
    note = serializers.CharField(max_length=500, allow_blank=True, default="")


class DecisionInput(StrictInput):
    decision = serializers.ChoiceField(choices=ReviewStatus.choices)
    note = serializers.CharField(max_length=1000, allow_blank=True, default="")


class FindingOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    code = serializers.CharField()
    automated = serializers.BooleanField()
    severity = serializers.CharField()
    message = serializers.CharField()
    state = serializers.CharField()
    participant_response = serializers.CharField()
    resolution_note = serializers.CharField()
    opened_at = serializers.DateTimeField()
    addressed_at = serializers.DateTimeField(allow_null=True)
    closed_at = serializers.DateTimeField(allow_null=True)


class ReviewOutput(serializers.Serializer):
    project = serializers.UUIDField()
    status = serializers.CharField()
    decision_note = serializers.CharField()
    revision = serializers.IntegerField()
    decided_at = serializers.DateTimeField(allow_null=True)
    findings = FindingOutput(many=True)


class ReviewSummaryOutput(serializers.Serializer):
    project = serializers.UUIDField()
    project_name = serializers.CharField()
    status = serializers.CharField()
    open_findings = serializers.IntegerField()
    addressed_findings = serializers.IntegerField()
    revision = serializers.IntegerField()


def _errors(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


def _review_data(review):
    return {
        "project": review.project.public_id,
        "status": review.status,
        "decision_note": review.decision_note,
        "revision": review.revision,
        "decided_at": review.decided_at,
        "findings": list(review.findings.all()),
    }


class RulesView(OrganizerView):
    @extend_schema(responses=RulesOutput)
    def get(self, request, workspace_public_id, event_public_id):
        rules = services.get_rules(self.get_event())
        return Response(RulesOutput(rules).data)

    @extend_schema(request=RulesInput, responses=RulesOutput)
    def put(self, request, workspace_public_id, event_public_id):
        data = RulesInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            rules = EligibilityRules.objects.filter(event=event).first() or EligibilityRules(
                event=event
            )
            before = RulesInput(rules).data
            for name, value in data.validated_data.items():
                setattr(rules, name, value)
            try:
                rules.full_clean()
            except ModelValidationError as exc:
                raise _errors(exc) from exc
            rules.save()
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="eligibility.rules_saved",
                target=rules,
                metadata={"event_id": str(event.public_id), "before": before, "after": data.data},
            )
        return Response(RulesOutput(rules).data)


class ReviewListView(OrganizerView):
    @extend_schema(
        parameters=[OpenApiParameter("status", str, enum=ReviewStatus.values)],
        responses=ReviewSummaryOutput(many=True),
    )
    def get(self, request, workspace_public_id, event_public_id):
        reviews = EligibilityReview.objects.filter(project__event=self.get_event()).select_related(
            "project"
        )
        if request.query_params.get("status"):
            if request.query_params["status"] not in ReviewStatus.values:
                raise ValidationError({"status": "Unknown status."})
            reviews = reviews.filter(status=request.query_params["status"])
        rows = []
        for review in reviews.order_by("project__name", "pk"):
            states = list(review.findings.values_list("state", flat=True))
            rows.append(
                {
                    "project": review.project.public_id,
                    "project_name": review.project.name,
                    "status": review.status,
                    "open_findings": states.count(FindingState.OPEN),
                    "addressed_findings": states.count(FindingState.ADDRESSED),
                    "revision": review.revision,
                }
            )
        return Response(ReviewSummaryOutput(rows, many=True).data)


class ProjectEligibilityBase(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_event(self):
        return get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )

    def is_organizer(self, request, workspace):
        return has_any_role(request.user, workspace, Role.ORGANIZER, Role.ADMIN)

    def get_project(self, request, *, organizer_only=False):
        event = self.get_event()
        project = get_object_or_404(
            Project, event=event, public_id=self.kwargs["project_public_id"]
        )
        organizer = self.is_organizer(request, event.workspace)
        member = ProjectMembership.objects.filter(project=project, user=request.user).exists()
        if organizer_only and not organizer:
            raise NotFound()
        if not organizer and not member:
            raise NotFound()
        return project, organizer

    def ensure_open(self, project):
        if project.event.status == EventStatus.ARCHIVED:
            raise ValidationError("Archived events cannot change eligibility reviews.")


class OrganizerProjectView(ProjectEligibilityBase):
    def get_project(self, request):
        project, _ = super().get_project(request, organizer_only=True)
        self.ensure_open(project)
        return project


class ProjectEligibilityView(ProjectEligibilityBase):
    @extend_schema(responses=ReviewOutput)
    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project, _ = self.get_project(request)
        review = EligibilityReview.objects.filter(project=project).first()
        if review is None:
            return Response(
                ReviewOutput(
                    {
                        "project": project.public_id,
                        "status": ReviewStatus.PENDING,
                        "decision_note": "",
                        "revision": 0,
                        "decided_at": None,
                        "findings": [],
                    }
                ).data
            )
        return Response(ReviewOutput(_review_data(review)).data)


class RunChecksView(OrganizerProjectView):
    @extend_schema(request=None, responses=ReviewOutput)
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project(request)
        return Response(
            ReviewOutput(_review_data(services.sync_checks(project, request.user))).data
        )


class RaiseFindingView(OrganizerProjectView):
    @extend_schema(request=FindingInput, responses={201: FindingOutput})
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project(request)
        data = FindingInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            finding = services.raise_finding(project, request.user, **data.validated_data)
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(FindingOutput(finding).data, status=201)


class FindingMixin:
    def get_finding(self, project):
        return get_object_or_404(
            EligibilityFinding,
            review__project=project,
            public_id=self.kwargs["finding_public_id"],
        )


class CloseFindingView(FindingMixin, OrganizerProjectView):
    @extend_schema(request=CloseInput, responses=FindingOutput)
    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, finding_public_id
    ):
        project = self.get_project(request)
        finding = self.get_finding(project)
        data = CloseInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            finding = services.close_finding(
                finding,
                request.user,
                state=data.validated_data["state"],
                note=data.validated_data["note"],
            )
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(FindingOutput(finding).data)


class DecisionView(OrganizerProjectView):
    @extend_schema(request=DecisionInput, responses=ReviewOutput)
    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project(request)
        data = DecisionInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            review = services.decide(project, request.user, **data.validated_data)
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(ReviewOutput(_review_data(review)).data)


class RespondView(FindingMixin, ProjectEligibilityBase):
    @extend_schema(request=RespondInput, responses=FindingOutput)
    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, finding_public_id
    ):
        project, _ = self.get_project(request)
        if ProjectMembership.objects.filter(project=project, user=request.user).exists() is False:
            raise NotFound()
        self.ensure_open(project)
        finding = self.get_finding(project)
        data = RespondInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            finding = services.respond(finding, request.user, data.validated_data["response"])
        except ModelValidationError as exc:
            raise _errors(exc) from exc
        return Response(FindingOutput(finding).data)
