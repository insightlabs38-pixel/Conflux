from accounts.authentication import CookieSessionAuthentication
from accounts.models import User
from audit.services import record_mutation
from core.mixins import WorkspaceLookupMixin
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Membership, Role

from .models import EvaluationPool, JudgeInvitation, PoolMembership
from .schema import (
    JudgeDirectorySchema,
    JudgeInvitationDecisionSchema,
    JudgeInvitationInputSchema,
    JudgeInvitationSchema,
)


def _serialize(invitation):
    return {
        "public_id": str(invitation.public_id),
        "event": str(invitation.pool.event.public_id),
        "event_name": invitation.pool.event.name,
        "pool": str(invitation.pool.public_id),
        "pool_name": invitation.pool.name,
        "judge": str(invitation.judge.public_id),
        "judge_username": invitation.judge.username,
        "status": invitation.status,
        "created_at": invitation.created_at,
        "responded_at": invitation.responded_at,
    }


class JudgeDirectoryView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    @extend_schema(responses=JudgeDirectorySchema(many=True))
    def get(self, request, workspace_public_id):
        judges = (
            User.objects.filter(
                memberships__workspace=self.get_workspace(), memberships__role=Role.JUDGE
            )
            .distinct()
            .order_by("username", "id")
        )
        return Response(
            [{"judge": str(user.public_id), "username": user.username} for user in judges]
        )


class JudgeInvitationListView(OrganizerView):
    @extend_schema(responses=JudgeInvitationSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id):
        invitations = (
            JudgeInvitation.objects.filter(pool__event=self.get_event())
            .select_related("pool__event", "judge")
            .order_by("-created_at", "-id")
        )
        return Response([_serialize(invitation) for invitation in invitations])

    @extend_schema(request=JudgeInvitationInputSchema, responses={201: JudgeInvitationSchema})
    def post(self, request, workspace_public_id, event_public_id):
        serializer = JudgeInvitationInputSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = self.get_event()
        self.ensure_mutable(event)
        pool = get_object_or_404(
            EvaluationPool, event=event, public_id=serializer.validated_data["pool"]
        )
        judge = get_object_or_404(User, public_id=serializer.validated_data["judge"])
        if not Membership.objects.filter(
            workspace=self.get_workspace(), user=judge, role=Role.JUDGE
        ).exists():
            raise ValidationError({"judge": "Judge is not in this workspace directory."})
        if PoolMembership.objects.filter(pool=pool, judge=judge).exists():
            raise ValidationError({"judge": "Judge is already in this event pool."})
        with transaction.atomic():
            invitation, created = JudgeInvitation.objects.select_for_update().get_or_create(
                pool=pool, judge=judge, defaults={"invited_by": request.user}
            )
            if not created and invitation.status == JudgeInvitation.Status.PENDING:
                raise ValidationError({"judge": "An invitation is already pending."})
            if not created:
                invitation.status = JudgeInvitation.Status.PENDING
                invitation.invited_by = request.user
                invitation.created_at = timezone.now()
                invitation.responded_at = None
                invitation.save(
                    update_fields=["status", "invited_by", "created_at", "responded_at"]
                )
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="judge_invitation.sent",
                target=invitation,
                metadata={"event": str(event.public_id), "pool": str(pool.public_id)},
            )
        return Response(_serialize(invitation), status=201)


class MyJudgeInvitationView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE)]

    @extend_schema(responses=JudgeInvitationSchema(many=True))
    def get(self, request, workspace_public_id):
        invitations = (
            JudgeInvitation.objects.filter(
                pool__event__workspace=self.get_workspace(), judge=request.user
            )
            .select_related("pool__event", "judge")
            .order_by("-created_at", "-id")
        )
        return Response([_serialize(invitation) for invitation in invitations])


class JudgeInvitationDetailView(WorkspaceLookupMixin, APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.JUDGE)]

    @extend_schema(request=JudgeInvitationDecisionSchema, responses={200: JudgeInvitationSchema})
    def post(self, request, workspace_public_id, invitation_public_id):
        serializer = JudgeInvitationDecisionSchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        with transaction.atomic():
            invitation = get_object_or_404(
                JudgeInvitation.objects.select_for_update(of=("self",)).select_related(
                    "pool__event", "judge"
                ),
                public_id=invitation_public_id,
                pool__event__workspace=self.get_workspace(),
                judge=request.user,
            )
            if invitation.status != JudgeInvitation.Status.PENDING:
                raise ValidationError({"detail": "This invitation is no longer pending."})
            if decision == "accept":
                membership = PoolMembership(pool=invitation.pool, judge=request.user)
                if PoolMembership.objects.filter(pool=invitation.pool, judge=request.user).exists():
                    raise ValidationError({"detail": "You are already in this event pool."})
                try:
                    membership.full_clean()
                    membership.save()
                except ModelValidationError as exc:
                    raise ValidationError(
                        exc.message_dict if hasattr(exc, "message_dict") else exc.messages
                    ) from exc
                except IntegrityError as exc:
                    raise ValidationError(
                        {"detail": "You are already in this event pool."}
                    ) from exc
                invitation.status = JudgeInvitation.Status.ACCEPTED
            else:
                invitation.status = JudgeInvitation.Status.DECLINED
            invitation.responded_at = timezone.now()
            invitation.save(update_fields=["status", "responded_at"])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action=f"judge_invitation.{invitation.status}",
                target=invitation,
                metadata={"event": str(invitation.pool.event.public_id)},
            )
        return Response(_serialize(invitation))


class JudgeInvitationRevokeView(OrganizerView):
    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, event_public_id, invitation_public_id):
        with transaction.atomic():
            invitation = get_object_or_404(
                JudgeInvitation.objects.select_for_update(of=("self",)).select_related(
                    "pool__event"
                ),
                public_id=invitation_public_id,
                pool__event=self.get_event(),
            )
            if invitation.status != JudgeInvitation.Status.PENDING:
                raise ValidationError({"detail": "Only pending invitations can be revoked."})
            invitation.status = JudgeInvitation.Status.REVOKED
            invitation.responded_at = timezone.now()
            invitation.save(update_fields=["status", "responded_at"])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="judge_invitation.revoked",
                target=invitation,
                metadata={"event": str(invitation.pool.event.public_id)},
            )
        return Response(status=204)
