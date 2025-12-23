import json
import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views import View
from django.views.generic import TemplateView

from .models import Pad, PadObject


def _normalize_upload_path(value: str | None) -> str | None:
    if not value:
        return None
    media_url = settings.MEDIA_URL or "/media/"
    if value.startswith(media_url):
        return value[len(media_url) :]
    return value.lstrip("/")


class IndexView(TemplateView):
    template_name = "partypad/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pads"] = Pad.objects.filter(created_by=self.request.user).order_by(
            "-created_at"
        )
        return context

    def post(self, request):
        pad = Pad.objects.create(
            created_by=request.user,
        )
        response = redirect("partypad:detail", pad_id=pad.id)
        if request.htmx:
            response["HX-Redirect"] = response.url
        return response


class DetailView(TemplateView):
    template_name = "partypad/pad_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pad = get_object_or_404(
            Pad.objects.prefetch_related("pad_objects"), id=self.kwargs["pad_id"]
        )
        context.update(
            {
                "pad": pad,
                "pad_objects": pad.as_dict()["objects"],
            }
        )
        return context


class ModifyObjectView(View):
    def post(self, request, pad_id, object_id=None):
        pad = get_object_or_404(Pad, id=pad_id)

        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)
        else:
            payload = request.POST.dict()

        if object_id:
            try:
                object_uuid = uuid.UUID(str(object_id))
            except ValueError:
                return JsonResponse(
                    {"success": False, "error": "Invalid object id."}, status=400
                )
        else:
            # Try to get id from payload for backward compatibility or direct creation with specific ID
            payload_id = payload.get("id")
            if payload_id:
                try:
                    object_uuid = uuid.UUID(str(payload_id))
                except ValueError:
                    return JsonResponse(
                        {"success": False, "error": "Invalid object id in payload."},
                        status=400,
                    )
            else:
                object_uuid = uuid.uuid4()

        object_type = payload.get("object_type")
        if object_type not in PadObject.ObjectType.values:
            return JsonResponse(
                {"success": False, "error": "Invalid object type."}, status=400
            )

        defaults = {
            "object_type": object_type,
            "x": int(payload.get("x", 0)),
            "y": int(payload.get("y", 0)),
            "width": int(payload.get("width", 100)),
            "height": int(payload.get("height", 100)),
            "rotation": int(payload.get("rotation", 0)),
            "playing": str(payload.get("playing", "")).lower() == "true",
            "loop": str(payload.get("loop", "")).lower() == "true",
        }

        if "file" in request.FILES:
            defaults["file"] = request.FILES["file"]
        elif payload.get("file"):
            defaults["file"] = _normalize_upload_path(payload.get("file"))

        obj, created = PadObject.objects.get_or_create(
            id=object_uuid,
            pad=pad,
            defaults=defaults | {"created_by": request.user},
        )
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save(update_fields=list(defaults.keys()))

        return JsonResponse(
            {
                "success": True,
                "created": created,
                "id": str(obj.id),
                "file": obj.file.name if obj.file else None,
                "file_url": obj.file.url if obj.file else None,
                "modify_url": obj.as_dict()["modify_url"],
            }
        )

    def delete(self, request, pad_id, object_id=None):
        pad = get_object_or_404(Pad, id=pad_id)

        if not object_id:
            try:
                payload = json.loads(request.body.decode("utf-8"))
                object_id = payload.get("id")
            except (json.JSONDecodeError, AttributeError):
                pass

        if not object_id:
            return JsonResponse(
                {"success": False, "error": "Object id missing."}, status=400
            )

        obj = get_object_or_404(PadObject, id=object_id, pad=pad)
        obj.delete()
        return JsonResponse({"success": True})
