from datetime import timedelta

from accounts.authentication import CookieSessionAuthentication
from audit.models import AuditEvent
from audit.services import record_mutation
from core.authz import has_any_role, is_workspace_member
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from events.models import Event
from events.views import OrganizerView
from presentation.public import public_projects
from projects.models import Project
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Role, Workspace

from . import abuse, voting
from .models import AbuseSignal, Comment, CommentVisibility, VoteIdentityMode, VoteToken, VotingPlan
from .ordering import ordered_candidates
from .results import results_visible_to, tally
from .serializers import CommentSerializer, VoteTokenSerializer, VotingPlanSerializer


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class VotingPlanMixin(OrganizerView):
    def get_plan(self, *, create=False):
        event = self.get_event()
        if create:
            now = timezone.now()
            plan, _ = VotingPlan.objects.get_or_create(
                event=event, defaults={"opens_at": now, "closes_at": now + timedelta(days=7)}
            )
            return plan
        return get_object_or_404(VotingPlan, event=event)


class VotingPlanDetailView(VotingPlanMixin):
    def get(self, request, workspace_public_id, event_public_id):
        return Response(VotingPlanSerializer(self.get_plan(create=True)).data)

    def patch(self, request, workspace_public_id, event_public_id):
        plan = self.get_plan(create=True)
        serializer = VotingPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                plan = serializer.save()
                plan.full_clean()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="voting_plan.updated",
                    target=plan,
                    metadata={"event_id": str(plan.event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(VotingPlanSerializer(plan).data)


class VoteTokenBatchView(VotingPlanMixin):
    def get(self, request, workspace_public_id, event_public_id):
        tokens = self.get_plan().vote_tokens.all()
        return Response(VoteTokenSerializer(tokens, many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        plan = self.get_plan()
        count = request.data.get("count", 1)
        if not isinstance(count, int) or isinstance(count, bool) or not (1 <= count <= 500):
            raise ValidationError({"count": "Must be an integer from 1 to 500."})
        with transaction.atomic():
            tokens = VoteToken.objects.bulk_create([VoteToken(plan=plan) for _ in range(count)])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="vote_tokens.issued",
                target=plan,
                metadata={"event_id": str(plan.event.public_id), "count": count},
            )
        return Response(VoteTokenSerializer(tokens, many=True).data, status=201)


class PublicVotingMixin(APIView):
    """Community voting is deliberately open to non-workspace-members under
    email_link/token identity modes -- an audience choice award isn't
    limited to people with a platform account, and in particular has no
    reason to know the event's workspace id, so `get_event` resolves purely
    by Event.public_id (globally unique) and these routes are reachable
    both workspace-nested (community.urls' original shape) and under the
    workspace-free `public/events/<event>/...` prefix a shared voting link
    would actually use. Authenticated-mode casting still requires a real
    session (checked inline, not via permission classes, since the same
    view serves all three identity modes).
    """

    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [AllowAny]

    def get_event(self):
        query = {"public_id": self.kwargs["event_public_id"]}
        if self.kwargs.get("workspace_public_id"):
            query["workspace__public_id"] = self.kwargs["workspace_public_id"]
        return get_object_or_404(Event, **query)

    def get_plan(self):
        return get_object_or_404(VotingPlan, event=self.get_event())


class PublicVotingStatusView(PublicVotingMixin):
    """Enough for a public voting UI to render the right form (which
    identity mode, whether the window is currently open) without exposing
    anything organizer-only.
    """

    def get(self, request, event_public_id, workspace_public_id=None):
        plan = VotingPlan.objects.filter(event=self.get_event()).first()
        if plan is None:
            return JsonResponse(None, safe=False)
        return Response(
            {
                "identity_mode": plan.identity_mode,
                "opens_at": plan.opens_at,
                "closes_at": plan.closes_at,
                "is_open": plan.is_open(),
                "allow_comments": plan.allow_comments,
            }
        )


class CandidateOrderView(PublicVotingMixin):
    def get(self, request, event_public_id, workspace_public_id=None):
        event = self.get_event()
        voter_key = request.GET.get("token") or (
            str(request.user.public_id) if request.user.is_authenticated else "anonymous"
        )
        candidates = ordered_candidates(list(public_projects(event)), voter_key)
        return Response([{"project": str(p.public_id), "name": p.name} for p in candidates])


class VoteCreateView(PublicVotingMixin):
    def post(self, request, event_public_id, workspace_public_id=None):
        plan = self.get_plan()
        project = get_object_or_404(
            Project, event=self.get_event(), public_id=request.data.get("project")
        )
        client_ip = abuse.client_identifier(request)
        try:
            if plan.identity_mode == VoteIdentityMode.AUTHENTICATED:
                if not request.user.is_authenticated:
                    raise PermissionDenied("Sign in to vote in this event.")
                if not is_workspace_member(request.user, plan.event.workspace):
                    raise PermissionDenied("You are not a member of this event's workspace.")
                vote = voting.cast_authenticated_vote(
                    plan, request.user, project, client_ip=client_ip
                )
            elif plan.identity_mode == VoteIdentityMode.EMAIL_LINK:
                vote = voting.cast_email_vote(
                    plan, request.data.get("token", ""), project, client_ip=client_ip
                )
            else:
                vote = voting.cast_token_vote(
                    plan, request.data.get("token", ""), project, client_ip=client_ip
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response({"public_id": str(vote.public_id)}, status=201)


class RequestEmailVoteTokenView(PublicVotingMixin):
    def post(self, request, event_public_id, workspace_public_id=None):
        plan = self.get_plan()
        email = request.data.get("email", "")
        client_ip = abuse.client_identifier(request)
        try:
            if plan.identity_mode != VoteIdentityMode.EMAIL_LINK:
                raise ModelValidationError("This event does not use email-link voting.")
            voting.require_open(plan)
            email = voting.normalize_vote_email(email)
            voting.enforce_email_request_limits(plan, email, client_ip)
            with transaction.atomic():
                token = voting.request_email_vote_token(plan, email, limits_checked=True)
                record_mutation(
                    actor=request.user,
                    workspace=self.get_event().workspace,
                    action="email_vote_token.requested",
                    target=plan,
                    metadata={"event_id": str(plan.event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        # No email transport is configured in this project (see
        # EmailVoteToken's docstring): returning the token directly is the
        # explicit, documented stand-in for "and then we email it to them".
        return Response({"token": token.token, "expires_at": token.expires_at}, status=201)


class ResultsView(PublicVotingMixin):
    def get(self, request, event_public_id, workspace_public_id=None):
        plan = self.get_plan()
        is_organizer = has_any_role(
            request.user, self.get_event().workspace, Role.ORGANIZER, Role.ADMIN
        )
        if not results_visible_to(plan, is_organizer=is_organizer):
            raise PermissionDenied("Results have not been published yet.")
        rows = tally(plan)
        projects_by_id = {
            p.id: p for p in Project.objects.filter(id__in=[r["project_id"] for r in rows])
        }
        return Response(
            [
                {
                    "project": str(projects_by_id[row["project_id"]].public_id),
                    "name": projects_by_id[row["project_id"]].name,
                    "votes": row["votes"],
                }
                for row in rows
                if row["project_id"] in projects_by_id
            ]
        )


class ResultsPublishView(VotingPlanMixin):
    def post(self, request, workspace_public_id, event_public_id):
        plan = self.get_plan()
        with transaction.atomic():
            plan.results_published_at = timezone.now()
            plan.save(update_fields=["results_published_at", "updated_at"])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="voting_results.published",
                target=plan,
                metadata={"event_id": str(plan.event.public_id)},
            )
        return Response(VotingPlanSerializer(plan).data)


def _signal_data(signal):
    return {
        "public_id": str(signal.public_id),
        "signal_type": signal.signal_type,
        "detail": signal.detail,
        "evidence": signal.evidence,
        "occurred_at": signal.occurred_at,
        "resolved_at": signal.resolved_at,
        "resolved_by": str(signal.resolved_by.public_id) if signal.resolved_by else None,
        "resolution_note": signal.resolution_note,
    }


def _review_offset(request):
    raw = request.query_params.get("offset", "0")
    try:
        offset = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError({"offset": "Must be a nonnegative integer."}) from exc
    if offset < 0 or offset > 100000:
        raise ValidationError({"offset": "Must be between 0 and 100000."})
    return offset


class AbuseSignalListView(VotingPlanMixin):
    def get(self, request, workspace_public_id, event_public_id):
        plan = self.get_plan()
        offset = _review_offset(request)
        signals = plan.abuse_signals.select_related("resolved_by").order_by("-occurred_at", "-id")[
            offset : offset + 100
        ]
        return Response([_signal_data(signal) for signal in signals])


class AbuseSignalResolveView(VotingPlanMixin):
    def post(self, request, workspace_public_id, event_public_id, signal_public_id):
        note = request.data.get("resolution_note")
        if not isinstance(note, str) or not note.strip() or len(note.strip()) > 2000:
            raise ValidationError({"resolution_note": "Enter a note of 1 to 2000 characters."})
        with transaction.atomic():
            signal = get_object_or_404(
                AbuseSignal.objects.select_for_update(),
                plan=self.get_plan(),
                public_id=signal_public_id,
            )
            if signal.resolved_at is not None:
                raise ValidationError({"detail": "This signal has already been resolved."})
            signal.resolved_at = timezone.now()
            signal.resolved_by = request.user
            signal.resolution_note = note.strip()
            signal.save(update_fields=["resolved_at", "resolved_by", "resolution_note"])
            record_mutation(
                actor=request.user,
                workspace=self.get_workspace(),
                action="community_abuse.resolved",
                target=signal,
                metadata={
                    "event_id": str(signal.plan.event.public_id),
                    "note": signal.resolution_note,
                },
            )
        return Response(_signal_data(signal))


class CommunityAuditView(VotingPlanMixin):
    def get(self, request, workspace_public_id, event_public_id):
        plan = self.get_plan()
        offset = _review_offset(request)
        signal_ids = [
            str(value) for value in plan.abuse_signals.values_list("public_id", flat=True)
        ]
        comment_ids = [
            str(value)
            for value in Comment.objects.filter(project__event=plan.event).values_list(
                "public_id", flat=True
            )
        ]
        events = (
            AuditEvent.objects.filter(workspace=self.get_workspace())
            .filter(
                Q(metadata__event_id=str(plan.event.public_id))
                | Q(target_type="VotingPlan", target_id=str(plan.public_id))
                | Q(target_type="AbuseSignal", target_id__in=signal_ids)
                | Q(target_type="Comment", target_id__in=comment_ids)
            )
            .select_related("actor")
            .order_by("-created_at", "-id")[offset : offset + 100]
        )
        return Response(
            [
                {
                    "public_id": str(item.public_id),
                    "actor": item.actor.username if item.actor else None,
                    "action": item.action,
                    "detail": _audit_detail(item),
                    "created_at": item.created_at,
                }
                for item in events
            ]
        )


def _audit_detail(item):
    if item.action == "community_abuse.detected":
        signal_type = item.metadata.get("signal_type", "unknown").replace("_", " ")
        return f"Suspicious voting activity: {signal_type}"
    if item.action == "vote_tokens.issued":
        return f"{item.metadata.get('count', 'Some')} voting tokens issued"
    labels = {
        "community_abuse.resolved": "Organizer resolved a voting abuse signal",
        "voting_plan.updated": "Voting settings updated",
        "email_vote_token.requested": "Email voting link requested",
        "voting_results.published": "Community results published",
        "comment.created": "Project comment posted",
        "comment.hidden": "Project comment hidden",
    }
    return labels.get(item.action, item.action.replace("_", " ").replace(".", ": "))


def _comment_visibility_allows(plan, workspace, user):
    if plan is None or plan.comment_visibility == CommentVisibility.EVERYONE:
        return True
    if plan.comment_visibility == CommentVisibility.ORGANIZER_JUDGE:
        return has_any_role(user, workspace, Role.JUDGE, Role.ORGANIZER, Role.ADMIN)
    return has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN)


class CommentListCreateView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.PARTICIPANT, Role.JUDGE, Role.ORGANIZER, Role.ADMIN)]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_project(self):
        event = get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )
        return get_object_or_404(Project, event=event, public_id=self.kwargs["project_public_id"])

    def get(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        plan = VotingPlan.objects.filter(event=project.event).first()
        if not _comment_visibility_allows(plan, self.get_workspace(), request.user):
            raise PermissionDenied("You cannot view comments on this project.")
        comments = project.comments.filter(hidden_at__isnull=True).select_related("author")
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, workspace_public_id, event_public_id, project_public_id):
        project = self.get_project()
        plan = VotingPlan.objects.filter(event=project.event).first()
        if plan is not None and not plan.allow_comments:
            raise ValidationError({"detail": "Comments are disabled for this event."})
        if not _comment_visibility_allows(plan, self.get_workspace(), request.user):
            raise PermissionDenied("You cannot comment on this project.")
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment(
            project=project, author=request.user, body=serializer.validated_data["body"]
        )
        try:
            with transaction.atomic():
                comment.full_clean()
                comment.save()
                record_mutation(
                    actor=request.user,
                    workspace=self.get_workspace(),
                    action="comment.created",
                    target=comment,
                    metadata={"event_id": str(project.event.public_id)},
                )
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(CommentSerializer(comment).data, status=201)


class CommentHideView(APIView):
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [require_roles(Role.ORGANIZER, Role.ADMIN)]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def post(
        self, request, workspace_public_id, event_public_id, project_public_id, comment_public_id
    ):
        workspace = self.get_workspace()
        comment = get_object_or_404(
            Comment,
            project__event__workspace=workspace,
            project__event__public_id=event_public_id,
            project__public_id=project_public_id,
            public_id=comment_public_id,
        )
        with transaction.atomic():
            comment.hidden_at = timezone.now()
            comment.hidden_by = request.user
            comment.save(update_fields=["hidden_at", "hidden_by"])
            record_mutation(
                actor=request.user,
                workspace=workspace,
                action="comment.hidden",
                target=comment,
                metadata={"event_id": str(comment.project.event.public_id)},
            )
        return Response(CommentSerializer(comment).data)
