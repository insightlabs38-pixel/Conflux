from django.core.exceptions import ValidationError
from django.db.models import Count
from stages.models import ParticipationMode, StageEntry
from workspaces.models import Membership, Role

from .models import MAX_TEAM_SIZE, MarketplaceProfile, TeamMembership, TeamOpening


def normalize_skills(values):
    if not isinstance(values, list) or len(values) > 10:
        raise ValidationError({"skills": "Provide at most 10 skills."})
    skills = []
    for value in values:
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 30:
            raise ValidationError({"skills": "Each skill must contain 1 to 30 characters."})
        skill = value.strip().casefold()
        if skill not in skills:
            skills.append(skill)
    return skills


def available_profiles(event):
    participant_ids = Membership.objects.filter(
        workspace=event.workspace, role=Role.PARTICIPANT
    ).values_list("user_id", flat=True)
    teamed_ids = TeamMembership.objects.filter(team__event=event).values_list("user_id", flat=True)
    return (
        MarketplaceProfile.objects.filter(event=event, visible=True, user_id__in=participant_ids)
        .exclude(user_id__in=teamed_ids)
        .select_related("user")
        .order_by("user__username", "id")
    )


def available_openings(event):
    locked_ids = set(
        StageEntry.objects.filter(
            stage__event=event,
            stage__participation_mode=ParticipationMode.TEAM_LOCKED,
            subject_type="team",
            exited_at__isnull=True,
        ).values_list("subject_id", flat=True)
    )
    openings = (
        TeamOpening.objects.filter(team__event=event, is_open=True)
        .select_related("team", "project")
        .annotate(member_count=Count("team__memberships"))
    )
    return [
        opening
        for opening in openings
        if opening.member_count < MAX_TEAM_SIZE and str(opening.team.public_id) not in locked_ids
    ]


def profile_data(profile):
    return {
        "public_id": str(profile.public_id),
        "user": str(profile.user.public_id),
        "username": profile.user.username,
        "skills": profile.skills,
        "bio": profile.bio,
        "visible": profile.visible,
    }


def opening_data(opening, *, match_skills=()):
    overlap = sorted(set(opening.desired_skills) & set(match_skills))
    return {
        "public_id": str(opening.public_id),
        "team": str(opening.team.public_id),
        "team_name": opening.team.name,
        "project": str(opening.project.public_id) if opening.project_id else None,
        "project_name": opening.project.name if opening.project_id else None,
        "title": opening.title,
        "description": opening.description,
        "desired_skills": opening.desired_skills,
        "is_open": opening.is_open,
        "matched_skills": overlap,
    }


def matches_for_participant(event, user):
    if TeamMembership.objects.filter(team__event=event, user=user).exists():
        return []
    profile = MarketplaceProfile.objects.filter(event=event, user=user).first()
    match_skills = profile.skills if profile else ()
    return sorted(
        [opening_data(item, match_skills=match_skills) for item in available_openings(event)],
        key=lambda item: (-len(item["matched_skills"]), item["team_name"], item["title"]),
    )


def matches_for_opening(event, opening):
    profiles = [profile_data(item) for item in available_profiles(event)]
    for profile in profiles:
        profile["matched_skills"] = sorted(set(profile["skills"]) & set(opening.desired_skills))
    return sorted(
        profiles,
        key=lambda item: (-len(item["matched_skills"]), item["username"]),
    )
