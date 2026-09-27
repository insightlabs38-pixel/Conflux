from datetime import timedelta

from accounts.authentication import CookieSessionAuthentication
from audit.services import record_mutation
from core.authz import has_any_role, is_workspace_member
from core.permissions import require_roles
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
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
from .models import Comment, CommentVisibility, VoteIdentityMode, VoteToken, VotingPlan
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
            plan = serializer.save()
            plan.full_clean()
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
                metadata={"count": count},
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
                    metadata={},
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
        plan.results_published_at = timezone.now()
        plan.save(update_fields=["results_published_at", "updated_at"])
        record_mutation(
            actor=request.user,
            workspace=self.get_workspace(),
            action="voting_results.published",
            target=plan,
        )
        return Response(VotingPlanSerializer(plan).data)


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
            comment.full_clean()
            comment.save()
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
            project__public_id=project_public_id,
            public_id=comment_public_id,
        )
        comment.hidden_at = timezone.now()
        comment.hidden_by = request.user
        comment.save(update_fields=["hidden_at", "hidden_by"])
        record_mutation(
            actor=request.user, workspace=workspace, action="comment.hidden", target=comment
        )
        return Response(CommentSerializer(comment).data)
