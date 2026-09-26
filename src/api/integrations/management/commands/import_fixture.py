import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from integrations.models import (
    FixtureJudge,
    FixtureProject,
    FixtureScore,
    FixtureScoreCriterion,
    FixtureTeam,
    FixtureTeamMember,
    FixtureTrack,
    ImportedFixture,
)

DEFAULT_PATH = "fixtures/fixtures.json"


def _parse_dt(value):
    parsed = parse_datetime(value)
    if parsed is None:
        raise CommandError(f"Not a valid ISO 8601 timestamp: {value!r}")
    return parsed


class Command(BaseCommand):
    """Import fixtures/fixtures.json verbatim into a defended relational schema.

    "Verbatim" means every record in the file becomes exactly one row, with
    no deduplication, normalization, or repair of its content — the fixture
    file deliberately contains a duplicate project submission and a
    constant-scoring judge (jdg_07, 4/4/4 on every review), and both must
    survive the import unchanged for later judging-integrity work to see.
    "Defended" means the fields are typed and constrained (real FKs, unique
    external IDs, an EmailField for emails) rather than stored as opaque
    JSON — the file is input, not the data model it becomes.

    Re-running clears the previous import first (not additive), so the
    acceptance identities always face exactly one fixture generation.
    """

    help = "Import fixtures/fixtures.json into the integrations app's defended schema."

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default=DEFAULT_PATH)

    @transaction.atomic
    def handle(self, *args, **options):
        path = options["path"]
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as exc:
            raise CommandError(f"Fixture file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Fixture file is not valid JSON: {path}: {exc}") from exc

        for key in ("event", "tracks", "judges", "teams", "projects", "scores"):
            if key not in data:
                raise CommandError(f"Fixture file is missing required key: {key!r}")

        # Not additive: a prior import's rows would otherwise collide on the
        # external_id uniqueness constraints on re-import, and a stale
        # second generation is worse than a clean rebuild for a fixture that
        # every acceptance run and every seeded identity should agree on.
        ImportedFixture.objects.all().delete()

        fixture = ImportedFixture.objects.create(
            source_path=path,
            event_external_id=data["event"]["id"],
            event_name=data["event"]["name"],
            event_submissions_close=_parse_dt(data["event"]["submissions_close"]),
        )

        tracks_by_external_id = {}
        for track in data["tracks"]:
            row = FixtureTrack.objects.create(
                fixture=fixture, external_id=track["id"], name=track["name"]
            )
            tracks_by_external_id[track["id"]] = row

        judges_by_external_id = {}
        for judge in data["judges"]:
            row = FixtureJudge.objects.create(
                fixture=fixture,
                external_id=judge["id"],
                name=judge["name"],
                email=judge["email"],
            )
            row.tracks.set(tracks_by_external_id[tid] for tid in judge.get("tracks", []))
            judges_by_external_id[judge["id"]] = row

        teams_by_external_id = {}
        for team in data["teams"]:
            row = FixtureTeam.objects.create(
                fixture=fixture, external_id=team["id"], name=team["name"]
            )
            FixtureTeamMember.objects.bulk_create(
                FixtureTeamMember(team=row, email=email) for email in team.get("members", [])
            )
            teams_by_external_id[team["id"]] = row

        projects_by_external_id = {}
        for project in data["projects"]:
            row = FixtureProject.objects.create(
                fixture=fixture,
                external_id=project["id"],
                team=teams_by_external_id[project["team"]],
                track=tracks_by_external_id[project["track"]],
                title=project["title"],
                summary=project.get("summary", ""),
                repo_url=project["repo_url"],
                submitted_at=_parse_dt(project["submitted_at"]),
            )
            projects_by_external_id[project["id"]] = row

        for score in data["scores"]:
            row = FixtureScore.objects.create(
                fixture=fixture,
                judge=judges_by_external_id[score["judge"]],
                project=projects_by_external_id[score["project"]],
                comment=score.get("comment", ""),
            )
            FixtureScoreCriterion.objects.bulk_create(
                FixtureScoreCriterion(score=row, name=name, value=value)
                for name, value in score.get("criteria", {}).items()
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported fixture {fixture.event_external_id!r}: "
                f"{len(tracks_by_external_id)} tracks, {len(judges_by_external_id)} judges, "
                f"{len(teams_by_external_id)} teams, {len(projects_by_external_id)} projects, "
                f"{len(data['scores'])} scores."
            )
        )
