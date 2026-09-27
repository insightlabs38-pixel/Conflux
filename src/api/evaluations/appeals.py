"""VS20: structured post-result appeals. A participant on a project may
dispute a published result once it's actually visible to them (the same
`published_normalization_run`/`results_visible_to_participants` gate
`ResultsView` already enforces); an organizer records a verdict. Neither
step ever mutates a Ballot/NormalizationRun -- see `models.Appeal`.
"""

from audit.services import record_mutation
from core.authz import has_any_role
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from projects.models import Project, ProjectMembership
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from workspaces.models import Role

from .models import Appeal, AppealStatus
from .schema import AppealDecisionInputSchema, AppealInputSchema, AppealSchema
from .views import PlanMixin


def _appeal_data(appeal):
    return {
        "public_id": str(appeal.public_id),
        "project": str(appeal.project.public_id),
        "project_name": appeal.project.name,
        "submitted_by": str(appeal.submitted_by.public_id),
        "submitted_by_username": appeal.submitted_by.username,
        "body": appeal.body,
        "status": appeal.status,
        "decision_note": appeal.decision_note,
        "decided_by": appeal.decided_by.username if appeal.decided_by_id else None,
        "decided_at": appeal.decided_at,
        "created_at": appeal.created_at,
    }


class AppealListCreateView(PlanMixin):
    permission_classes = [require_roles(Role.PARTICIPANT, Role.ORGANIZER, Role.ADMIN)]

    def _is_organizer(self, request):
        return has_any_role(request.user, self.get_workspace(), Role.ORGANIZER, Role.ADMIN)

    @extend_schema(responses=AppealSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        appeals = Appeal.objects.filter(plan=plan).select_related("project", "submitted_by")
        if not self._is_organizer(request):
            appeals = appeals.filter(submitted_by=request.user)
        return Response([_appeal_data(item) for item in appeals])

    @extend_schema(request=AppealInputSchema, responses={201: AppealSchema})
    def post(self, request, workspace_public_id, event_public_id, stage_public_id, plan_public_id):
        plan = self.get_plan()
        event = self.get_event()
        if not has_any_role(request.user, self.get_workspace(), Role.PARTICIPANT):
            raise PermissionDenied("Only a participant may file an appeal.")
        if plan.published_normalization_run_id is None or not plan.results_visible_to_participants:
            raise ValidationError({"detail": "Results are not yet visible to participants."})
        serializer = AppealInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = get_object_or_404(
            Project,
            event=event,
            memberships__user=request.user,
            public_id=serializer.validated_data["project"],
        )
        if not ProjectMembership.objects.filter(project=project, user=request.user).exists():
            raise PermissionDenied("You are not a member of this project.")
        appeal = Appeal(
            plan=plan,
            project=project,
            submitted_by=request.user,
            body=serializer.validated_data["body"],
        )
        try:
            appeal.full_clean()
            appeal.save()
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="appeal.filed",
            target=appeal,
            event_type="appeal.filed",
            payload={"plan": str(plan.public_id), "project": str(project.public_id)},
        )
        return Response(_appeal_data(appeal), status=201)


class AppealDecisionView(PlanMixin):
    @extend_schema(request=AppealDecisionInputSchema, responses=AppealSchema)
    def post(
        self,
        request,
        workspace_public_id,
        event_public_id,
        stage_public_id,
        plan_public_id,
        appeal_public_id,
    ):
        serializer = AppealDecisionInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            appeal = get_object_or_404(
                Appeal.objects.select_for_update(of=("self",)),
                plan=self.get_plan(),
                public_id=appeal_public_id,
            )
            if appeal.status != AppealStatus.PENDING:
                raise ValidationError({"detail": "This appeal has already been decided."})
            appeal.status = serializer.validated_data["status"]
            appeal.decision_note = serializer.validated_data.get("decision_note", "")
            appeal.decided_by = request.user
            appeal.decided_at = timezone.now()
            appeal.save(
                update_fields=["status", "decision_note", "decided_by", "decided_at", "updated_at"]
            )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="appeal.decided",
                target=appeal,
                event_type="appeal.decided",
                payload={"appeal": str(appeal.public_id), "status": appeal.status},
            )
        return Response(_appeal_data(appeal))
