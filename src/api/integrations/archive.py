"""Canonical archive v1 (PORT-001..004): a deterministic, versioned export of
one event's organizer-authored configuration, and a validated importer that
rebuilds it as a brand-new event.

Scope is deliberately bounded — see docs/architecture/CANONICAL_ARCHIVE.md
for what v1 covers, what it omits, and why. Cross-references inside a
document use each source row's own `public_id` as a stable local ref; import
remaps every ref to the newly created rows and never trusts a source-side
database identity (pk) or reuses a source-side public_id.
"""

from decimal import Decimal

from accounts.models import User
from awards.models import Award, PrizeComponent, PrizePackage
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from evaluations.models import EvaluationPlan, RubricVersion
from events.models import BasePrize, Event, EventStatus, Track
from forms.models import FormDefinition, FormVersion
from policies.models import Policy, PolicyBinding, TemporalGate
from presentation.models import Page, PageBlock
from projects.models import Project
from stages.models import Stage, StageTransition

FORMAT_VERSION = 1
MODES = ("config", "full")

# Optional top-level sections a caller may select a subset of (event-template
# cloning, TPL-002/003) -- "event" itself is never optional. Two sections
# (stage_transitions, evaluation_plans) hard-require "stages" to make any
# sense at all and are dropped outright if it's excluded; a handful of
# individual fields hold an optional cross-reference into another optional
# section and are nulled out (never left dangling) if that section is
# excluded. See `_filter_sections`.
SECTION_KEYS = (
    "tracks",
    "base_prizes",
    "stages",
    "stage_transitions",
    "forms",
    "policies",
    "temporal_gates",
    "policy_bindings",
    "awards",
    "evaluation_plans",
    "pages",
)
_REQUIRES_STAGES = {"stage_transitions", "evaluation_plans"}
_REQUIRES_POLICIES = {"policy_bindings"}
_OPTIONAL_TRACK_REF: dict[str, str] = {
    "base_prizes": "track_ref",
    "awards": "eligibility_track_ref",
    "projects": "track_ref",
}
_OPTIONAL_STAGE_REF: dict[str, str] = {"forms": "stage_ref"}


def _iso(value):
    return value.isoformat() if value is not None else None


def _parse_dt(value):
    if value is None:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValidationError({"archive": f"Not a valid ISO 8601 timestamp: {value!r}."})
    return parsed


def _decimal(value):
    return None if value is None else Decimal(value)


def build_archive(event, mode=None, sections=None):
    from .final_archive import build_final_archive
    from .models import ArchiveRestoration

    restored = ArchiveRestoration.objects.filter(event=event).exists()
    mode = mode or ("final" if restored else "config")
    if mode == "final":
        if sections is not None:
            raise ValidationError({"sections": "Final archives cannot omit tables."})
        return build_final_archive(event)
    if mode not in MODES:
        raise ValueError(f"Unknown archive mode: {mode!r}")

    tracks = list(event.tracks.order_by("position", "name", "pk"))
    track_ref = {t.pk: str(t.public_id) for t in tracks}

    stages = list(event.stages.order_by("position", "name", "pk"))
    stage_ref = {s.pk: str(s.public_id) for s in stages}

    policies = list(event.policies.order_by("name", "pk"))
    policy_ref = {p.pk: str(p.public_id) for p in policies}

    archive = {
        "format_version": FORMAT_VERSION,
        "mode": mode,
        "event": {
            "name": event.name,
            "slug": event.slug,
            "description": event.description,
            "timezone": event.timezone,
            "starts_at": _iso(event.starts_at),
            "ends_at": _iso(event.ends_at),
            "status": event.status,
            "is_public": event.is_public,
        },
        "tracks": [
            {
                "ref": track_ref[t.pk],
                "name": t.name,
                "description": t.description,
                "position": t.position,
            }
            for t in tracks
        ],
        "base_prizes": [
            {
                "ref": str(p.public_id),
                "track_ref": track_ref.get(p.track_id),
                "name": p.name,
                "description": p.description,
                "kind": p.kind,
                "amount": str(p.amount) if p.amount is not None else None,
                "currency": p.currency,
                "position": p.position,
            }
            for p in event.base_prizes.select_related("track").order_by("position", "name", "pk")
        ],
        "stages": [
            {
                "ref": stage_ref[s.pk],
                "name": s.name,
                "position": s.position,
                "is_initial": s.is_initial,
                "participation_mode": s.participation_mode,
            }
            for s in stages
        ],
        "stage_transitions": [
            {"from_ref": stage_ref[t.from_stage_id], "to_ref": stage_ref[t.to_stage_id]}
            for t in StageTransition.objects.filter(from_stage__event=event).order_by(
                "from_stage__position", "to_stage__position", "pk"
            )
        ],
        "forms": [
            {
                "ref": str(f.public_id),
                "name": f.name,
                "stage_ref": stage_ref.get(f.stage_id),
                "draft_schema": f.draft_schema,
                "versions": [
                    {"number": v.number, "schema": v.schema} for v in f.versions.order_by("number")
                ],
            }
            for f in event.forms.select_related("stage").order_by("name", "pk")
        ],
        "policies": [{"ref": policy_ref[p.pk], "name": p.name, "ast": p.ast} for p in policies],
        "temporal_gates": [
            {
                "ref": str(g.public_id),
                "name": g.name,
                "opens_at": _iso(g.opens_at),
                "closes_at": _iso(g.closes_at),
            }
            for g in event.temporal_gates.order_by("name", "pk")
        ],
        "policy_bindings": [
            {"action": b.action, "policy_ref": policy_ref[b.policy_id]}
            for b in event.policy_bindings.select_related("policy").order_by("action", "pk")
        ],
        "awards": [
            {
                "ref": str(a.public_id),
                "name": a.name,
                "description": a.description,
                "eligibility_track_ref": track_ref.get(a.eligibility_track_id),
                "require_finalized_submission": a.require_finalized_submission,
                "selection_source": a.selection_source,
                "evaluation_plan_name": (a.evaluation_plan.name if a.evaluation_plan_id else None),
                "winner_count": a.winner_count,
                "allow_stacking": a.allow_stacking,
                "conflict_group": a.conflict_group,
                "components": [
                    {
                        "kind": c.kind,
                        "name": c.name,
                        "description": c.description,
                        "quantity": c.quantity,
                        "amount": str(c.amount) if c.amount is not None else None,
                        "currency": c.currency,
                        "position": c.position,
                    }
                    for c in PrizeComponent.objects.filter(package__award=a).order_by(
                        "position", "pk"
                    )
                ],
            }
            for a in Award.objects.filter(event=event)
            .select_related("eligibility_track", "evaluation_plan")
            .order_by("name", "pk")
        ],
        "evaluation_plans": [
            {
                "ref": str(p.public_id),
                "stage_ref": stage_ref[p.stage_id],
                "name": p.name,
                "candidate_type": p.candidate_type,
                "pool_strategy": p.pool_strategy,
                "results_visible_to_participants": p.results_visible_to_participants,
                "rubric_versions": [
                    {"number": rv.number, "criteria": rv.criteria}
                    for rv in p.rubric_versions.order_by("number")
                ],
            }
            for p in EvaluationPlan.objects.filter(stage__event=event)
            .select_related("stage")
            .order_by("stage__position", "name", "pk")
        ],
        "pages": (
            [
                {
                    "theme": event.page.theme,
                    "blocks": [
                        {"kind": b.kind, "position": b.position, "config": b.config}
                        for b in event.page.blocks.order_by("position", "id")
                    ],
                }
            ]
            if hasattr(event, "page")
            else []
        ),
    }

    if mode == "full":
        archive["projects"] = _full_mode_projects(event, track_ref)

    if sections is not None:
        archive = _filter_sections(archive, sections)

    return archive


def _full_mode_projects(event, track_ref):
    return [
        {
            "ref": str(proj.public_id),
            "name": proj.name,
            "description": proj.description,
            "track_ref": track_ref.get(proj.track_id),
            "created_by_username": proj.created_by.username,
        }
        for proj in Project.objects.filter(event=event)
        .select_related("track", "created_by")
        .order_by("name", "pk")
    ]


def _resolve(refs, ref, field):
    if ref is None:
        return None
    try:
        return refs[ref]
    except KeyError as exc:
        raise ValidationError({field: f"Unknown reference: {ref!r}."}) from exc


def import_archive(*, workspace, archive, name, slug):
    """Rebuild `archive` as a brand-new Event in `workspace`, named/slugged
    by the caller. Runs every row through the model's own `full_clean()`,
    so domain invariants (track-in-event, cash-needs-amount, cycle-free
    stage graph, ...) apply exactly as they would to organizer-authored
    data — import never bypasses them. Must run inside the caller's
    transaction so a validation failure midway leaves nothing behind.
    """
    if not isinstance(archive, dict):
        raise ValidationError({"archive": "Archive must be an object."})
    if archive.get("format_version") == 2:
        from .final_archive import restore_final_archive

        return restore_final_archive(workspace=workspace, archive=archive, name=name, slug=slug)
    missing = [key for key in ("format_version", "mode", "event") if key not in archive]
    if missing:
        raise ValidationError(
            {"archive": f"Archive is missing required keys: {', '.join(missing)}."}
        )
    version = archive["format_version"]
    if version != FORMAT_VERSION:
        raise ValidationError(
            {
                "format_version": (
                    f"Unsupported archive format_version: {version!r}. "
                    f"This build only reads version {FORMAT_VERSION}."
                )
            }
        )
    mode = archive["mode"]
    if mode not in MODES:
        raise ValidationError({"mode": f"Unknown archive mode: {mode!r}."})

    event_data = archive["event"]
    event = Event(
        workspace=workspace,
        name=name,
        slug=slug,
        description=event_data.get("description", ""),
        timezone=event_data.get("timezone", "UTC"),
        starts_at=_parse_dt(event_data.get("starts_at")),
        ends_at=_parse_dt(event_data.get("ends_at")),
        status=EventStatus.DRAFT,
        is_public=False,
    )
    event.full_clean()
    event.save()

    refs = {}

    for t in archive.get("tracks", []):
        track = Track(
            event=event,
            name=t["name"],
            description=t.get("description", ""),
            position=t.get("position", 0),
        )
        track.full_clean()
        track.save()
        refs[t["ref"]] = track

    for p in archive.get("base_prizes", []):
        prize = BasePrize(
            event=event,
            track=_resolve(refs, p.get("track_ref"), "base_prizes.track_ref"),
            name=p["name"],
            description=p.get("description", ""),
            kind=p["kind"],
            amount=_decimal(p.get("amount")),
            currency=p.get("currency", ""),
            position=p.get("position", 0),
        )
        prize.full_clean()
        prize.save()

    for s in archive.get("stages", []):
        stage = Stage(
            event=event,
            name=s["name"],
            position=s.get("position", 0),
            is_initial=s.get("is_initial", False),
            participation_mode=s["participation_mode"],
        )
        stage.full_clean()
        stage.save()
        refs[s["ref"]] = stage

    for tr in archive.get("stage_transitions", []):
        transition = StageTransition(
            from_stage=_resolve(refs, tr["from_ref"], "stage_transitions.from_ref"),
            to_stage=_resolve(refs, tr["to_ref"], "stage_transitions.to_ref"),
        )
        transition.full_clean()
        transition.save()

    for f in archive.get("forms", []):
        form = FormDefinition(
            event=event,
            stage=_resolve(refs, f.get("stage_ref"), "forms.stage_ref"),
            name=f["name"],
            draft_schema=f.get("draft_schema", {}),
        )
        form.full_clean()
        form.save()
        for v in f.get("versions", []):
            version_row = FormVersion(definition=form, number=v["number"], schema=v["schema"])
            version_row.full_clean()
            version_row.save()

    for pol in archive.get("policies", []):
        policy = Policy(event=event, name=pol["name"], ast=pol["ast"])
        policy.full_clean()
        policy.save()
        refs[pol["ref"]] = policy

    for g in archive.get("temporal_gates", []):
        gate = TemporalGate(
            event=event,
            name=g["name"],
            opens_at=_parse_dt(g.get("opens_at")),
            closes_at=_parse_dt(g.get("closes_at")),
        )
        gate.full_clean()
        gate.save()

    for b in archive.get("policy_bindings", []):
        binding = PolicyBinding(
            event=event,
            action=b["action"],
            policy=_resolve(refs, b["policy_ref"], "policy_bindings.policy_ref"),
        )
        binding.full_clean()
        binding.save()

    for a in archive.get("awards", []):
        evaluation_plan = None
        plan_name = a.get("evaluation_plan_name")
        if plan_name:
            matches = list(EvaluationPlan.objects.filter(stage__event=event, name=plan_name))
            if not matches:
                raise ValidationError(
                    {
                        "awards": (
                            f"Award {a['name']!r} references evaluation plan {plan_name!r}, "
                            "which does not exist in the target event."
                        )
                    }
                )
            if len(matches) > 1:
                raise ValidationError(
                    {
                        "awards": (
                            f"Award {a['name']!r} references evaluation plan {plan_name!r}, "
                            "which is ambiguous in the target event."
                        )
                    }
                )
            evaluation_plan = matches[0]
        award = Award(
            event=event,
            name=a["name"],
            description=a.get("description", ""),
            eligibility_track=_resolve(
                refs, a.get("eligibility_track_ref"), "awards.eligibility_track_ref"
            ),
            require_finalized_submission=a.get("require_finalized_submission", True),
            selection_source=a["selection_source"],
            evaluation_plan=evaluation_plan,
            winner_count=a.get("winner_count", 1),
            allow_stacking=a.get("allow_stacking", True),
            conflict_group=a.get("conflict_group", ""),
        )
        award.full_clean()
        award.save()
        components = a.get("components", [])
        if components:
            package = PrizePackage(award=award, name=award.name)
            package.full_clean()
            package.save()
            for c in components:
                component = PrizeComponent(
                    package=package,
                    kind=c["kind"],
                    name=c["name"],
                    description=c.get("description", ""),
                    quantity=c.get("quantity", 1),
                    amount=_decimal(c.get("amount")),
                    currency=c.get("currency", ""),
                    position=c.get("position", 0),
                )
                component.full_clean()
                component.save()

    for p in archive.get("evaluation_plans", []):
        plan = EvaluationPlan(
            stage=_resolve(refs, p["stage_ref"], "evaluation_plans.stage_ref"),
            name=p["name"],
            candidate_type=p["candidate_type"],
            pool_strategy=p["pool_strategy"],
            results_visible_to_participants=p.get("results_visible_to_participants", False),
        )
        plan.full_clean()
        plan.save()
        for rv in p.get("rubric_versions", []):
            rubric_version = RubricVersion(plan=plan, number=rv["number"], criteria=rv["criteria"])
            rubric_version.full_clean()
            rubric_version.save()

    for page_data in archive.get("pages", []):
        page = Page(event=event, theme=page_data.get("theme", "default"))
        page.full_clean()
        page.save()
        for block in page_data.get("blocks", []):
            page_block = PageBlock(
                page=page,
                kind=block["kind"],
                position=block.get("position", 0),
                config=block.get("config", {}),
            )
            page_block.full_clean()
            page_block.save()

    if mode == "full":
        for proj in archive.get("projects", []):
            username = proj["created_by_username"]
            try:
                creator = User.objects.get(username=username)
            except User.DoesNotExist as exc:
                raise ValidationError(
                    {
                        "projects": (
                            f"Project {proj['name']!r} references user {username!r}, "
                            "which does not exist in this deployment."
                        )
                    }
                ) from exc
            project = Project(
                event=event,
                track=_resolve(refs, proj.get("track_ref"), "projects.track_ref"),
                name=proj["name"],
                description=proj.get("description", ""),
                created_by=creator,
            )
            project.full_clean()
            project.save()

    return event


def _filter_sections(archive, sections):
    unknown = set(sections) - set(SECTION_KEYS)
    if unknown:
        raise ValidationError({"sections": f"Unknown section(s): {', '.join(sorted(unknown))}."})
    selected = set(sections)
    filtered = {
        "format_version": archive["format_version"],
        "mode": archive["mode"],
        "event": archive["event"],
    }
    for key, rows in archive.items():
        if key in ("format_version", "mode", "event"):
            continue
        if key == "projects":
            filtered[key] = rows  # `sections` never governs full mode's participant data
            continue
        if key not in selected:
            continue
        if key in _REQUIRES_STAGES and "stages" not in selected:
            continue  # meaningless without the stages they point at
        if key in _REQUIRES_POLICIES and "policies" not in selected:
            continue
        track_field = _OPTIONAL_TRACK_REF.get(key)
        stage_field = _OPTIONAL_STAGE_REF.get(key)
        null_track = track_field and "tracks" not in selected
        null_stage = stage_field and "stages" not in selected
        if null_track or null_stage:
            rows = [
                {
                    **row,
                    **({track_field: None} if null_track else {}),
                    **({stage_field: None} if null_stage else {}),
                }
                for row in rows
            ]
        filtered[key] = rows
    return filtered
