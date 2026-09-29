from django.core.exceptions import ValidationError
from django.db.models import Count
from stages.models import ParticipationMode, StageEntry
from workspaces.models import Membership, Role

from .models import MAX_TEAM_SIZE, MarketplaceProfile, TeamMembership, TeamOpening


def normalize_tags(values, *, field):
    if not isinstance(values, list) or len(values) > 10:
        raise ValidationError({field: f"Provide at most 10 {field}."})
    tags = []
    for value in values:
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 30:
            raise ValidationError(
                {field: f"Each entry in {field} must contain 1 to 30 characters."}
            )
        tag = value.strip().casefold()
        if tag not in tags:
            tags.append(tag)
    return tags


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


def _availability_compatible(candidate_hours, required_hours):
    """None means "unknown" (one side never specified a number) -- never
    treated as a mismatch, only as the absence of that evidence.
    """
    if candidate_hours is None or required_hours is None:
        return None
    return candidate_hours >= required_hours


def profile_data(profile):
    from accounts.profile import identity_for

    return {
        "identity": identity_for(profile.user, workspace=profile.event.workspace),
        "public_id": str(profile.public_id),
        "user": str(profile.user.public_id),
        "username": profile.user.username,
        "skills": profile.skills,
        "roles": profile.roles,
        "interests": profile.interests,
        "availability_hours_per_week": profile.availability_hours_per_week,
        "bio": profile.bio,
        "visible": profile.visible,
    }


def opening_data(
    opening, *, match_skills=(), match_roles=(), match_interests=(), candidate_hours=None
):
    return {
        "public_id": str(opening.public_id),
        "team": str(opening.team.public_id),
        "team_name": opening.team.name,
        "project": str(opening.project.public_id) if opening.project_id else None,
        "project_name": opening.project.name if opening.project_id else None,
        "title": opening.title,
        "description": opening.description,
        "desired_skills": opening.desired_skills,
        "desired_roles": opening.desired_roles,
        "interests": opening.interests,
        "min_availability_hours_per_week": opening.min_availability_hours_per_week,
        "is_open": opening.is_open,
        "matched_skills": sorted(set(opening.desired_skills) & set(match_skills)),
        "matched_roles": sorted(set(opening.desired_roles) & set(match_roles)),
        "matched_interests": sorted(set(opening.interests) & set(match_interests)),
        "availability_compatible": _availability_compatible(
            candidate_hours, opening.min_availability_hours_per_week
        ),
    }


def _match_sort_key(item):
    # Roles are the strongest signal (closest to "can do this job"), then
    # skills, then shared interests; availability never excludes a match,
    # it only breaks ties among candidates tied on every other signal --
    # an explicit incompatibility sorts after an unknown one.
    availability = item["availability_compatible"]
    return (
        -len(item["matched_roles"]),
        -len(item["matched_skills"]),
        -len(item["matched_interests"]),
        0 if availability is not False else 1,
    )


def matches_for_participant(event, user):
    if TeamMembership.objects.filter(team__event=event, user=user).exists():
        return []
    profile = MarketplaceProfile.objects.filter(event=event, user=user).first()
    match_skills = profile.skills if profile else ()
    match_roles = profile.roles if profile else ()
    match_interests = profile.interests if profile else ()
    candidate_hours = profile.availability_hours_per_week if profile else None
    return sorted(
        [
            opening_data(
                item,
                match_skills=match_skills,
                match_roles=match_roles,
                match_interests=match_interests,
                candidate_hours=candidate_hours,
            )
            for item in available_openings(event)
        ],
        key=lambda item: (*_match_sort_key(item), item["team_name"], item["title"]),
    )


def matches_for_opening(event, opening):
    profiles = [profile_data(item) for item in available_profiles(event)]
    for profile in profiles:
        profile["matched_skills"] = sorted(set(profile["skills"]) & set(opening.desired_skills))
        profile["matched_roles"] = sorted(set(profile["roles"]) & set(opening.desired_roles))
        profile["matched_interests"] = sorted(set(profile["interests"]) & set(opening.interests))
        profile["availability_compatible"] = _availability_compatible(
            profile["availability_hours_per_week"], opening.min_availability_hours_per_week
        )
    return sorted(
        profiles,
        key=lambda item: (*_match_sort_key(item), item["username"]),
    )
