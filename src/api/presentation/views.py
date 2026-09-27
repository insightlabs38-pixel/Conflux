from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from events.views import OrganizerView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Page, PageBlock
from .serializers import PageBlockSerializer, PageSerializer


def _as_drf_validation_error(exc):
    return ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class PageMixin(OrganizerView):
    def get_page(self):
        page, _ = Page.objects.get_or_create(event=self.get_event())
        return page


class PageDetailView(PageMixin):
    serializer_class = PageSerializer

    def get(self, request, workspace_public_id, event_public_id):
        return Response(PageSerializer(self.get_page()).data)

    def patch(self, request, workspace_public_id, event_public_id):
        page = self.get_page()
        serializer = PageSerializer(page, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PageSerializer(page).data)


class PageBlockListView(PageMixin):
    serializer_class = PageBlockSerializer

    def get(self, request, workspace_public_id, event_public_id):
        return Response(PageBlockSerializer(self.get_page().blocks.all(), many=True).data)

    def post(self, request, workspace_public_id, event_public_id):
        page = self.get_page()
        serializer = PageBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        next_position = (page.blocks.count()) or 0
        try:
            with transaction.atomic():
                block = serializer.save(page=page, position=next_position)
                block.full_clean()
                block.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(PageBlockSerializer(block).data, status=201)


class PageBlockDetailView(PageMixin):
    serializer_class = PageBlockSerializer

    def get_block(self):
        return get_object_or_404(
            PageBlock, page=self.get_page(), public_id=self.kwargs["block_public_id"]
        )

    def patch(self, request, workspace_public_id, event_public_id, block_public_id):
        block = self.get_block()
        serializer = PageBlockSerializer(block, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                block = serializer.save()
                block.full_clean()
                block.save()
        except ModelValidationError as exc:
            raise _as_drf_validation_error(exc) from exc
        return Response(PageBlockSerializer(block).data)

    def delete(self, request, workspace_public_id, event_public_id, block_public_id):
        self.get_block().delete()
        return Response(status=204)


class PageBlockReorderView(PageMixin):
    serializer_class = PageBlockSerializer

    def post(self, request, workspace_public_id, event_public_id):
        page = self.get_page()
        order = request.data.get("block_ids")
        blocks = {str(block.public_id): block for block in page.blocks.all()}
        if not isinstance(order, list) or set(order) != set(blocks):
            raise ValidationError({"block_ids": "Must list every block on this page exactly once."})
        with transaction.atomic():
            for position, public_id in enumerate(order):
                block = blocks[public_id]
                block.position = position
                block.save(update_fields=["position", "updated_at"])
        return Response(PageBlockSerializer(page.blocks.all(), many=True).data)
