from events.models import Track

from .models import JudgeExpertiseProfile


def normalize_tag(value):
    return value.strip().casefold()


def judge_track_ids_for_pool(memberships, event):
    judge_ids = [membership.judge_id for membership in memberships]
    tracks_by_name = {}
    for track_id, name in Track.objects.filter(event=event).values_list("id", "name"):
        tracks_by_name.setdefault(normalize_tag(name), set()).add(track_id)
    tags_by_judge = dict(
        JudgeExpertiseProfile.objects.filter(
            workspace=event.workspace, judge_id__in=judge_ids
        ).values_list("judge_id", "tags")
    )
    result = {}
    for membership in memberships:
        track_ids = {track.id for track in membership.track_expertise.all()}
        for tag in tags_by_judge.get(membership.judge_id, []):
            track_ids.update(tracks_by_name.get(normalize_tag(tag), ()))
        result[membership.judge_id] = track_ids
    return result
