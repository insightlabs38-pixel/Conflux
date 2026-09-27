from accounts.authentication import CookieSessionAuthentication
from core.permissions import IsWorkspaceMember
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Event
from events.views import OrganizerView
from projects.models import Project
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace

from .models import FormDefinition, FormResponse, FormVersion
from .services import create_form, publish_form, save_draft, save_response
from .validation import field_visible


class FormPayloadSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    stage = serializers.UUIDField(allow_null=True)
    draft_schema = serializers.JSONField()


class FormVersionSchema(serializers.Serializer):
    public_id = serializers.UUIDField()
    number = serializers.IntegerField()
    schema = serializers.JSONField()
    published_at = serializers.DateTimeField()


class FormResponseSchema(serializers.Serializer):
    version = serializers.UUIDField()
    answers = serializers.JSONField()


class FormNameInputSchema(serializers.Serializer):
    name = serializers.CharField()


class FormDraftInputSchema(serializers.Serializer):
    schema = serializers.JSONField()


class FormAnswersInputSchema(serializers.Serializer):
    answers = serializers.JSONField()


def participant_answers(response):
    if response is None:
        return {}
    values = {answer.field_id: answer.value for answer in response.answers.all()}
    fields = {field["id"]: field for field in response.version.schema["fields"]}
    return {
        field_id: value
        for field_id, value in values.items()
        if field_id in fields and field_visible(fields[field_id], "participant", values)
    }


def form_payload(form):
    return {
        "public_id": str(form.public_id),
        "name": form.name,
        "stage": str(form.stage.public_id) if form.stage_id else None,
        "draft_schema": form.draft_schema,
    }


def version_payload(version):
    return {
        "public_id": str(version.public_id),
        "number": version.number,
        "schema": version.schema,
        "published_at": version.published_at,
    }


class FormOrganizerView(OrganizerView):
    def get_form(self):
        return get_object_or_404(
            FormDefinition, event=self.get_event(), public_id=self.kwargs["form_public_id"]
        )


class FormListView(FormOrganizerView):
    serializer_class = FormPayloadSchema

    def get(self, request, workspace_public_id, event_public_id):
        return Response(
            [
                form_payload(form)
                for form in FormDefinition.objects.filter(event=self.get_event()).order_by("name")
            ]
        )

    @extend_schema(request=FormNameInputSchema, responses={201: FormPayloadSchema})
    def post(self, request, workspace_public_id, event_public_id):
        event = self.get_event()
        self.ensure_mutable(event)
        name = str(request.data.get("name", "")).strip()
        if not name:
            raise ValidationError({"name": "Form name is required."})
        try:
            form = create_form(event, name)
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(form_payload(form), status=201)


class FormDetailView(FormOrganizerView):
    serializer_class = FormPayloadSchema

    def get(self, request, workspace_public_id, event_public_id, form_public_id):
        return Response(form_payload(self.get_form()))

    @extend_schema(request=FormDraftInputSchema, responses=FormPayloadSchema)
    def put(self, request, workspace_public_id, event_public_id, form_public_id):
        form = self.get_form()
        self.ensure_mutable(form.event)
        try:
            save_draft(form, request.data.get("schema"))
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(form_payload(form))


class FormVersionListView(FormOrganizerView):
    serializer_class = FormVersionSchema

    def get(self, request, workspace_public_id, event_public_id, form_public_id):
        return Response([version_payload(version) for version in self.get_form().versions.all()])


class FormPublishView(FormOrganizerView):
    @extend_schema(request=None, responses={201: FormVersionSchema})
    def post(self, request, workspace_public_id, event_public_id, form_public_id):
        form = self.get_form()
        self.ensure_mutable(form.event)
        try:
            version = publish_form(form)
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(version_payload(version), status=201)


class ProjectFormResponseView(APIView):
    serializer_class = FormResponseSchema
    authentication_classes = [CookieSessionAuthentication]
    permission_classes = [IsWorkspaceMember]

    def get_workspace(self):
        return get_object_or_404(Workspace, public_id=self.kwargs["workspace_public_id"])

    def get_objects(self, request):
        event = get_object_or_404(
            Event, workspace=self.get_workspace(), public_id=self.kwargs["event_public_id"]
        )
        project = get_object_or_404(
            Project,
            event=event,
            public_id=self.kwargs["project_public_id"],
            memberships__user=request.user,
        )
        version = get_object_or_404(
            FormVersion, definition__event=event, public_id=self.kwargs["version_public_id"]
        )
        return project, version

    def get(
        self, request, workspace_public_id, event_public_id, project_public_id, version_public_id
    ):
        project, version = self.get_objects(request)
        response = FormResponse.objects.filter(project=project, version=version).first()
        return Response(
            {
                "version": str(version.public_id),
                "answers": participant_answers(response),
            }
        )

    @extend_schema(request=FormAnswersInputSchema, responses=FormResponseSchema)
    def put(
        self, request, workspace_public_id, event_public_id, project_public_id, version_public_id
    ):
        project, version = self.get_objects(request)
        try:
            response = save_response(project, version, request.user, request.data.get("answers"))
        except ModelValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            ) from exc
        return Response(
            {
                "version": str(version.public_id),
                "answers": participant_answers(response),
            }
        )
