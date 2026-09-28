from accounts.models import User
from audit.services import record_mutation
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from events.models import Event
from events.views import OrganizerView
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from workspaces.models import Workspace

from .models import (
    MAX_TAXONOMIES_PER_WORKSPACE,
    MAX_TERMS_PER_TAXONOMY,
    SubjectType,
    Taxonomy,
    TaxonomyAssignment,
    TaxonomyTerm,
)

LIST_LIMIT = 5000


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict) and data.keys() - self.fields.keys():
            raise ValidationError({"non_field_errors": ["Unknown fields."]})
        return super().to_internal_value(data)


class TermInput(StrictInput):
    key = serializers.SlugField(max_length=50)
    label = serializers.CharField(max_length=80)


class TermsField(serializers.ListField):
    child = TermInput()

    def to_internal_value(self, data):
        terms = super().to_internal_value(data)
        if len(terms) > MAX_TERMS_PER_TAXONOMY:
            raise ValidationError(f"At most {MAX_TERMS_PER_TAXONOMY} terms.")
        if len({t["key"] for t in terms}) != len(terms):
            raise ValidationError("Term keys must be unique.")
        return terms


class TaxonomyCreateInput(StrictInput):
    key = serializers.SlugField(max_length=50)
    name = serializers.CharField(max_length=80)
    applies_to = serializers.ChoiceField(choices=SubjectType.choices)
    allows_multiple = serializers.BooleanField(default=False)
    terms = TermsField(required=False, default=list)


class TaxonomyPatchInput(StrictInput):
    name = serializers.CharField(max_length=80, required=False)
    allows_multiple = serializers.BooleanField(required=False)
    terms = TermsField(required=False)


class TermOutput(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    position = serializers.IntegerField()


class TaxonomyOutput(serializers.Serializer):
    public_id = serializers.UUIDField()
    key = serializers.CharField()
    name = serializers.CharField()
    applies_to = serializers.CharField()
    allows_multiple = serializers.BooleanField()
    terms = TermOutput(many=True)


class SubjectInput(StrictInput):
    type = serializers.ChoiceField(choices=SubjectType.choices)
    id = serializers.UUIDField(required=False)


class AssignmentInput(StrictInput):
    taxonomy = serializers.UUIDField()
    subject = SubjectInput()
    terms = serializers.ListField(child=serializers.SlugField(max_length=50), max_length=50)


class AssignmentOutput(serializers.Serializer):
    taxonomy = serializers.CharField()
    term = serializers.CharField()
    subject = serializers.DictField()


def _validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


def _data(taxonomy):
    return {
        "public_id": taxonomy.public_id,
        "key": taxonomy.key,
        "name": taxonomy.name,
        "applies_to": taxonomy.applies_to,
        "allows_multiple": taxonomy.allows_multiple,
        "terms": list(taxonomy.terms.all()),
    }


def _replace_terms(taxonomy, terms):
    existing = {t.key: t for t in taxonomy.terms.all()}
    removed = [t for key, t in existing.items() if key not in {x["key"] for x in terms}]
    if TaxonomyAssignment.objects.filter(term__in=removed).exists():
        raise ValidationError({"terms": "A term that is still assigned cannot be removed."})
    TaxonomyTerm.objects.filter(pk__in=[t.pk for t in removed]).delete()
    for position, item in enumerate(terms):
        term = existing.get(item["key"]) or TaxonomyTerm(taxonomy=taxonomy, key=item["key"])
        term.label, term.position = item["label"], position
        term.full_clean()
        term.save()


class TaxonomyListView(OrganizerView):
    @extend_schema(responses=TaxonomyOutput(many=True))
    def get(self, request, workspace_public_id):
        taxonomies = self.get_workspace().taxonomies.prefetch_related("terms")
        return Response(TaxonomyOutput([_data(t) for t in taxonomies], many=True).data)

    @extend_schema(request=TaxonomyCreateInput, responses={201: TaxonomyOutput})
    def post(self, request, workspace_public_id):
        data = TaxonomyCreateInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            workspace = Workspace.objects.select_for_update().get(pk=self.get_workspace().pk)
            if workspace.taxonomies.count() >= MAX_TAXONOMIES_PER_WORKSPACE:
                raise ValidationError(f"At most {MAX_TAXONOMIES_PER_WORKSPACE} taxonomies.")
            fields = {k: v for k, v in data.validated_data.items() if k != "terms"}
            if workspace.taxonomies.filter(key=fields["key"]).exists():
                raise ValidationError({"key": "This key is already used."})
            taxonomy = Taxonomy(workspace=workspace, **fields)
            try:
                taxonomy.full_clean(exclude=["workspace"])
                taxonomy.save()
                _replace_terms(taxonomy, data.validated_data["terms"])
            except ModelValidationError as exc:
                raise _validation_error(exc) from exc
            record_mutation(
                actor=request.user,
                workspace=workspace,
                action="taxonomy.created",
                target=taxonomy,
                metadata={**fields, "terms": [t["key"] for t in data.validated_data["terms"]]},
            )
        return Response(TaxonomyOutput(_data(taxonomy)).data, status=201)


class TaxonomyDetailView(OrganizerView):
    def get_taxonomy(self, *, lock=False):
        queryset = Taxonomy.objects.filter(workspace=self.get_workspace())
        if lock:
            queryset = queryset.select_for_update()
        return get_object_or_404(queryset, public_id=self.kwargs["taxonomy_public_id"])

    @extend_schema(responses=TaxonomyOutput)
    def get(self, request, workspace_public_id, taxonomy_public_id):
        return Response(TaxonomyOutput(_data(self.get_taxonomy())).data)

    @extend_schema(request=TaxonomyPatchInput, responses=TaxonomyOutput)
    def patch(self, request, workspace_public_id, taxonomy_public_id):
        data = TaxonomyPatchInput(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            taxonomy = self.get_taxonomy(lock=True)
            changes = {}
            if "allows_multiple" in data.validated_data:
                if (
                    taxonomy.allows_multiple
                    and not data.validated_data["allows_multiple"]
                    and self._has_multiple(taxonomy)
                ):
                    raise ValidationError(
                        {"allows_multiple": "Some subjects already have several terms."}
                    )
            for name in ("name", "allows_multiple"):
                if name in data.validated_data and data.validated_data[name] != getattr(
                    taxonomy, name
                ):
                    changes[name] = {
                        "before": getattr(taxonomy, name),
                        "after": data.validated_data[name],
                    }
                    setattr(taxonomy, name, data.validated_data[name])
            try:
                taxonomy.full_clean(exclude=["workspace"])
                taxonomy.save()
                if "terms" in data.validated_data:
                    before = [t.key for t in taxonomy.terms.all()]
                    _replace_terms(taxonomy, data.validated_data["terms"])
                    changes["terms"] = {
                        "before": before,
                        "after": [t["key"] for t in data.validated_data["terms"]],
                    }
            except ModelValidationError as exc:
                raise _validation_error(exc) from exc
            record_mutation(
                actor=request.user,
                workspace=taxonomy.workspace,
                action="taxonomy.updated",
                target=taxonomy,
                metadata={"changes": changes},
            )
        return Response(TaxonomyOutput(_data(taxonomy)).data)

    @staticmethod
    def _has_multiple(taxonomy):
        return (
            TaxonomyAssignment.objects.filter(term__taxonomy=taxonomy)
            .values("event", "project", "person")
            .annotate(n=Count("pk"))
            .filter(n__gt=1)
            .exists()
        )

    @extend_schema(responses={204: None})
    def delete(self, request, workspace_public_id, taxonomy_public_id):
        with transaction.atomic():
            taxonomy = self.get_taxonomy(lock=True)
            if TaxonomyAssignment.objects.filter(term__taxonomy=taxonomy).exists():
                raise ValidationError("Remove this taxonomy's assignments before deleting it.")
            record_mutation(
                actor=request.user,
                workspace=taxonomy.workspace,
                action="taxonomy.deleted",
                target=taxonomy,
                metadata={"key": taxonomy.key},
            )
            taxonomy.delete()
        return Response(status=204)


def _subject_filter(event, subject):
    kind = subject["type"]
    if kind == SubjectType.EVENT:
        if "id" in subject:
            raise ValidationError({"subject": "An event subject takes no id."})
        return {"subject_type": kind, "project": None, "person": None}
    if "id" not in subject:
        raise ValidationError({"subject": "A subject id is required."})
    if kind == SubjectType.PROJECT:
        project = get_object_or_404(Project, event=event, public_id=subject["id"])
        return {"subject_type": kind, "project": project, "person": None}
    person = get_object_or_404(
        User, public_id=subject["id"], memberships__workspace=event.workspace
    )
    return {"subject_type": kind, "project": None, "person": person}


def _row(assignment):
    subject = {"type": assignment.subject_type}
    if assignment.project_id:
        subject["id"] = str(assignment.project.public_id)
    if assignment.person_id:
        subject["id"] = str(assignment.person.public_id)
    return {
        "taxonomy": assignment.term.taxonomy.key,
        "term": assignment.term.key,
        "subject": subject,
    }


class AssignmentView(OrganizerView):
    @extend_schema(
        parameters=[
            OpenApiParameter("taxonomy", str),
            OpenApiParameter("term", str),
            OpenApiParameter("subject_type", str, enum=SubjectType.values),
        ],
        responses=AssignmentOutput(many=True),
    )
    def get(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        rows = TaxonomyAssignment.objects.filter(event=event).select_related(
            "term__taxonomy", "project", "person"
        )
        for param, lookup in (
            ("taxonomy", "term__taxonomy__key"),
            ("term", "term__key"),
            ("subject_type", "subject_type"),
        ):
            if request.query_params.get(param):
                rows = rows.filter(**{lookup: request.query_params[param]})
        return Response([_row(a) for a in rows[:LIST_LIMIT]])

    @extend_schema(request=AssignmentInput, responses=AssignmentOutput(many=True))
    def put(self, request, workspace_public_id, event_public_id):
        data = AssignmentInput(data=request.data)
        data.is_valid(raise_exception=True)
        keys = data.validated_data["terms"]
        if len(set(keys)) != len(keys):
            raise ValidationError({"terms": "Terms must be unique."})
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=self.get_event().pk)
            self.ensure_mutable(event)
            taxonomy = get_object_or_404(
                Taxonomy, workspace=event.workspace, public_id=data.validated_data["taxonomy"]
            )
            subject = data.validated_data["subject"]
            if subject["type"] != taxonomy.applies_to:
                raise ValidationError({"subject": "This taxonomy applies to another subject."})
            if len(keys) > 1 and not taxonomy.allows_multiple:
                raise ValidationError({"terms": "This taxonomy allows a single term."})
            terms = {t.key: t for t in taxonomy.terms.all()}
            unknown = [key for key in keys if key not in terms]
            if unknown:
                raise ValidationError({"terms": f"Unknown terms: {unknown}."})
            target = _subject_filter(event, subject)
            current = TaxonomyAssignment.objects.filter(
                event=event, term__taxonomy=taxonomy, **target
            )
            before = sorted(a.term.key for a in current.select_related("term"))
            current.delete()
            created = []
            try:
                for key in keys:
                    assignment = TaxonomyAssignment(
                        event=event, term=terms[key], assigned_by=request.user, **target
                    )
                    assignment.full_clean()
                    assignment.save()
                    created.append(assignment)
            except ModelValidationError as exc:
                raise _validation_error(exc) from exc
            record_mutation(
                actor=request.user,
                workspace=event.workspace,
                action="taxonomy.assigned",
                target=taxonomy,
                metadata={
                    "event_id": str(event.public_id),
                    "subject": {"type": subject["type"], "id": str(subject.get("id", ""))},
                    "before": before,
                    "after": sorted(keys),
                },
            )
        return Response([_row(a) for a in created])
