"""Prize-fulfillment handoff reports (VS49).

Rows carry only what a handoff needs. Recipient contacts and organizer notes
are organizer-only, opt-in, and audited; sponsors see their own awards and
never personal data.
"""

import csv

from audit.services import record_mutation
from core.csv_safety import safe_cell
from django.db import transaction
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Award, FulfillmentState, PrizeFulfillment
from .sponsor_portal import SponsorPortalBase

COLUMNS = [
    "handoff_reference",
    "award",
    "component",
    "kind",
    "quantity",
    "amount",
    "currency",
    "project",
    "team",
    "state",
    "updated_at",
]


def _cell(value):
    return safe_cell("" if value is None else str(value))


def fulfillment_rows(awards, *, state=None, include_recipients=False, include_notes=False):
    items = (
        PrizeFulfillment.objects.filter(
            winner__award__in=awards, winner__award__published_at__isnull=False
        )
        .select_related("winner__award", "winner__project__team", "component", "updated_by")
        .order_by("winner__award__name", "component__position", "winner__project__name", "pk")
    )
    if state:
        items = items.filter(state=state)
    rows = []
    for item in items:
        project = item.winner.project
        row = {
            "handoff_reference": str(item.public_id),
            "award": item.winner.award.name,
            "component": item.component.name,
            "kind": item.component.kind,
            "quantity": item.component.quantity,
            "amount": None if item.component.amount is None else str(item.component.amount),
            "currency": item.component.currency,
            "project": project.name,
            "team": project.team.name if project.team_id else None,
            "state": item.state,
            "updated_at": item.updated_at.isoformat(),
        }
        if include_notes:
            row["note"] = item.note
        if include_recipients:
            row["recipients"] = [
                {"username": m.user.username, "email": m.user.email}
                for m in project.memberships.select_related("user").order_by("user__username")
            ]
        rows.append(row)
    return rows


def _flatten(row):
    flat = {name: row[name] for name in COLUMNS}
    if "note" in row:
        flat["note"] = row["note"]
    if "recipients" in row:
        flat["recipients"] = "; ".join(
            f"{r['username']} <{r['email']}>" if r["email"] else r["username"]
            for r in row["recipients"]
        )
    return flat


class FulfillmentExportBase(SponsorPortalBase):
    def build(self, request):
        event = self.get_event()
        organizer = self.is_organizer(request)
        options = {
            name: request.query_params.get(name, "").lower() == "true"
            for name in ("include_recipients", "include_notes")
        }
        if any(options.values()) and not organizer:
            raise PermissionDenied("Only organizers can include contacts or notes.")
        state = request.query_params.get("state") or None
        if state and state not in FulfillmentState.values:
            raise ValidationError({"state": "Unknown fulfillment state."})
        awards = Award.objects.filter(event=event)
        if not organizer:
            awards = awards.filter(sponsor_contacts=request.user)
        with transaction.atomic():
            rows = fulfillment_rows(
                awards,
                state=state,
                include_recipients=options["include_recipients"],
                include_notes=options["include_notes"],
            )
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="award.fulfillment_exported",
                target=event,
                metadata={"event_id": str(event.public_id), "rows": len(rows), **options},
            )
        return rows


PARAMETERS = [
    OpenApiParameter("state", str, enum=FulfillmentState.values),
    OpenApiParameter("include_recipients", bool),
    OpenApiParameter("include_notes", bool),
]


class FulfillmentExportView(FulfillmentExportBase):
    @extend_schema(parameters=PARAMETERS, responses={200: OpenApiTypes.OBJECT})
    def get(self, request, workspace_public_id, event_public_id):
        return Response({"rows": self.build(request)})


class FulfillmentExportCsvView(FulfillmentExportBase):
    @extend_schema(parameters=PARAMETERS, responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request, workspace_public_id, event_public_id):
        rows = [_flatten(row) for row in self.build(request)]
        fields = COLUMNS + [
            name for name in ("note", "recipients") if any(name in row for row in rows)
        ]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="prize-fulfillment.csv"'
        writer = csv.writer(response)
        writer.writerow(fields)
        for row in rows:
            writer.writerow([_cell(row.get(name)) for name in fields])
        return response
