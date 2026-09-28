"""Deterministically enrich a generated demo workspace so every headline capability has
something to show: a full landing page, agenda, expo map, rules acknowledgements and
post-event continuation. Idempotent: re-running on an enriched event changes nothing.
"""

from datetime import timedelta

from accounts.models import User
from awards.models import AwardResource
from continuation.services import add_update, save_continuation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from eligibility import services as eligibility
from eligibility.models import EligibilityReview
from events.models import Announcement, Event, EventStatus, ParticipantCheckIn
from governance.services import acknowledge_rules, current_rules, publish_rules
from mentorship.models import MentorProfile, OfficeHourSlot
from mentorship.services import create_request
from onsite.models import AgendaSession, Attendance, AttendanceMode, Location, ProjectLocation
from presentation.models import Page, PageBlock
from presentation.public import public_projects
from workspaces.models import Membership, Role

from integrations.models import DemoScenario

LANDING = [
    (
        "hero",
        {
            "title": "Demo Hackathon",
            "subtitle": "Two days of building, judged blind, published with receipts.",
            "cta_label": "Browse the projects",
            "cta_href": "gallery/",
        },
    ),
    ("tracks", {}),
    ("gallery", {"limit": 6}),
    ("results", {}),
    ("announcements", {}),
]
SESSIONS = [
    ("Opening keynote", 9, 10, "Hall", "Priya Raman"),
    ("Judging calibration workshop", 11, 12, "Hall", "Wei Lindqvist"),
    ("Expo and demos", 13, 16, "Hall", ""),
    ("Awards ceremony", 17, 18, "Hall", "Organizing team"),
]
RESOURCES = [
    ("api", "Sponsor API documentation", "https://example.test/sponsor/api", ""),
    ("faq", "Judging FAQ", "", "The sponsor scores usefulness of the developer experience."),
]
CONTINUATIONS = [
    (
        "Open-sourcing the core as a library; looking for contributors.",
        ["contributors", "feedback"],
    ),
    ("Running a pilot with two campus clubs next term.", ["users", "mentors"]),
]


class Command(BaseCommand):
    help = "Enrich a generated demo workspace (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("slug")
        parser.add_argument(
            "--password", help="Password for the mentor/volunteer/sponsor accounts."
        )

    @transaction.atomic
    def handle(self, *args, slug, password=None, **options):
        marker = (
            DemoScenario.objects.filter(workspace__slug=slug).select_related("workspace").first()
        )
        if marker is None:
            raise CommandError("Only generated demo scenarios can be enriched.")
        workspace = marker.workspace
        event = Event.objects.filter(workspace=workspace).order_by("pk").first()
        prefix = f"demo-{marker.scenario}-{marker.seed}-"
        organizer = (
            Membership.objects.filter(
                workspace=workspace, role=Role.ORGANIZER, user__username=prefix + "organizer"
            )
            .select_related("user")
            .first()
            .user
        )

        page, _ = Page.objects.get_or_create(event=event)
        if not page.blocks.filter(kind="gallery").exists():
            page.blocks.all().delete()
            for position, (kind, config) in enumerate(LANDING):
                block = PageBlock(page=page, kind=kind, position=position, config=config)
                block.full_clean()
                block.save()

        if not event.announcements.exists():
            closed = event.status == EventStatus.CLOSED
            Announcement.objects.create(
                event=event,
                title="Results are published" if closed else "Submissions are open",
                body=(
                    "Thanks to everyone who built, judged and mentored. See the results page."
                    if closed
                    else "Create your team, submit your project, and check the agenda."
                ),
                posted_by=organizer,
            )

        base = event.starts_at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
        room, _ = Location.objects.get_or_create(event=event, kind="room", name="Hall")
        if not event.agenda_sessions.exists():
            for title, start, end, place, speakers in SESSIONS:
                session = AgendaSession(
                    event=event,
                    title=title,
                    starts_at=base + timedelta(hours=start),
                    ends_at=base + timedelta(hours=end),
                    location=room,
                    speakers=speakers,
                    created_by=organizer,
                )
                session.full_clean()
                session.save()

        projects = list(public_projects(event)[:6])
        for number, project in enumerate(projects, start=1):
            table, _ = Location.objects.get_or_create(
                event=event, kind="table", name=f"T{number}", defaults={"parent": room}
            )
            ProjectLocation.objects.get_or_create(project=project, defaults={"location": table})

        if current_rules(event) is None:
            publish_rules(
                event,
                organizer,
                title="Participant rules",
                body="Be kind. Build during the event. Cite what you reuse. Judging is blind.",
            )
        participants = (
            Membership.objects.filter(workspace=workspace, role=Role.PARTICIPANT)
            .select_related("user")
            .order_by("user__username")[:8]
        )
        for membership in participants:
            acknowledge_rules(event, membership.user)

        # Continuation opens once the event has closed; open checkpoints skip it.
        closing = event.status == EventStatus.CLOSED
        for (summary, seeking), project in zip(CONTINUATIONS, projects, strict=False):
            if not closing:
                break
            owner = project.memberships.select_related("user").order_by("pk").first().user
            item = save_continuation(
                project,
                owner,
                summary=summary,
                seeking=seeking,
                is_public=True,
                url="https://example.test/" + project.public_id.hex[:8],
            )
            if not item.updates.exists():
                add_update(project, owner, body="First release tagged; docs are up.")
        self._enrich_people(event, workspace, organizer, prefix, projects, password)
        self.stdout.write(
            f"Enriched {slug}: {event.agenda_sessions.count()} sessions, "
            f"{len(projects)} placements."
        )

    def _staff(self, workspace, prefix, label, role, password):
        user, created = User.objects.get_or_create(username=prefix + label)
        if created:
            user.set_password(password) if password else user.set_unusable_password()
            user.save()
        Membership.objects.get_or_create(workspace=workspace, user=user, role=role)
        return user

    def _enrich_people(self, event, workspace, organizer, prefix, projects, password):
        """Mentor, volunteer and sponsor accounts plus the state their screens need."""
        mentor = self._staff(workspace, prefix, "mentor", Role.MENTOR, password)
        volunteer = self._staff(workspace, prefix, "volunteer", Role.VOLUNTEER, password)
        sponsor = self._staff(workspace, prefix, "sponsor", Role.SPONSOR, password)
        MentorProfile.objects.get_or_create(
            event=event, mentor=mentor, defaults={"headline": "Backend, infrastructure and demos"}
        )
        if not event.office_hour_slots.exists():
            start = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
            OfficeHourSlot.objects.create(
                event=event,
                mentor=mentor,
                starts_at=start,
                ends_at=start + timedelta(hours=1),
                location="Hall, table M1",
                capacity=3,
            )
        grand = event.awards.filter(name="Grand Prize").first()
        if grand is not None:
            grand.sponsor_contacts.add(sponsor)
            for kind, title, url, body in RESOURCES:
                AwardResource.objects.get_or_create(
                    award=grand,
                    title=title,
                    defaults={"kind": kind, "url": url, "body": body, "created_by": sponsor},
                )
        if not projects:
            return
        first, second = projects[0], projects[1] if len(projects) > 1 else None
        if second is not None and not EligibilityReview.objects.filter(project=second).exists():
            eligibility.sync_checks(second, organizer)
            eligibility.raise_finding(
                second,
                organizer,
                message="Add a link to your source repository as an artifact.",
                severity="blocking",
            )
            eligibility.decide(
                second, organizer, decision="needs_remediation", note="One fix needed."
            )
        if not EligibilityReview.objects.filter(project=first).exists():
            eligibility.sync_checks(first, organizer)
            eligibility.decide(first, organizer, decision="cleared", note="Looks good.")
        members = list(
            Membership.objects.filter(workspace=workspace, role=Role.PARTICIPANT)
            .select_related("user")
            .order_by("user__username")[:4]
        )
        for membership in members:
            Attendance.objects.get_or_create(
                event=event, user=membership.user, defaults={"mode": AttendanceMode.IN_PERSON}
            )
        for membership in members[:2]:
            check_in = ParticipantCheckIn(
                event=event, participant=membership.user, checked_in_by=volunteer
            )
            if not ParticipantCheckIn.objects.filter(
                event=event, participant=membership.user
            ).exists():
                check_in.full_clean()
                check_in.save()
        owner = first.memberships.select_related("user").order_by("pk").first()
        if owner and not first.mentor_requests.exists():
            create_request(
                first, owner.user, topic="Deploying the demo to a public URL", urgency="normal"
            )
