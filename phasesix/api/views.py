import io

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import activate
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pdf2image import convert_from_path

from armory.models import (
    WeaponType,
    RiotGearType,
    ItemType,
    WeaponModificationType,
)
from body_modifications.models import BodyModificationType
from horror.models import QuirkCategory
from magic.models import SpellOrigin, SpellTemplateCategory
from portal.models import Profile
from rulebook.models import WorldBook, BOOK_VARIANTS
from rules.models import TemplateCategory, FoeType, Extension
from worlds.models import World


class ApiKeyView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        api_key = request.headers.get("Authorization")
        if not Profile.objects.filter(
            Q(api_key=api_key) & Q(api_key__isnull=False)
        ).exists():
            raise PermissionDenied()
        activate(request.headers.get("Accept-Language") or "en")
        return super().dispatch(request, *args, **kwargs)


class DumpApiView(ApiKeyView):
    def get(self, request, *args, **kwargs):
        model_map = {
            "templates": TemplateCategory,
            "weapons": WeaponType,
            "weapon_modifications": WeaponModificationType,
            "riot_gear": RiotGearType,
            "items": ItemType,
            "spells": SpellOrigin,
            "spell_templates": SpellTemplateCategory,
            "quirks": QuirkCategory,
            "body_modifications": BodyModificationType,
            "foes": FoeType,
        }
        qs = model_map[kwargs["model"]].objects.all()

        world_name = request.GET.get("world", None)
        if world_name is not None and world_name in ["nexus", "tirakan"]:
            extensions = Extension.objects.for_world_identifier(world_name)
        else:
            extensions = Extension.objects.exclude(type="w")
        return JsonResponse(
            [t.as_dict(extension_qs=extensions) for t in qs], safe=False
        )


class UploadRulebooksView(ApiKeyView):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        world_identifier = request.POST.get("world_identifier")
        variant = request.POST.get("variant")
        language = request.POST.get("language")
        upload = request.FILES.get("file")

        if not world_identifier:
            return JsonResponse(
                {"error": "Missing field: world_identifier"}, status=400
            )
        if not variant:
            return JsonResponse({"error": "Missing field: variant"}, status=400)
        if not language:
            return JsonResponse({"error": "Missing field: language"}, status=400)
        if upload is None:
            return JsonResponse(
                {"error": "Missing file upload under key 'file'"}, status=400
            )

        valid_variants = set(BOOK_VARIANTS)
        if variant not in valid_variants:
            return JsonResponse(
                {
                    "error": f"Invalid variant '{variant}'. Must be one of {sorted(valid_variants)}"
                },
                status=400,
            )

        valid_language_codes = {code for code, _ in settings.LANGUAGES}
        if language not in valid_language_codes:
            return JsonResponse(
                {
                    "error": f"Invalid language '{language}'. Must be one of {sorted(valid_language_codes)}"
                },
                status=400,
            )

        try:
            world = World.objects.get(extension__identifier=world_identifier)
        except World.DoesNotExist:
            return JsonResponse(
                {"error": f"World with identifier '{world_identifier}' not found"},
                status=404,
            )

        world_book = WorldBook.objects.filter(world=world).first()
        if world_book is None:
            return JsonResponse(
                {"error": f"No WorldBook configured for world '{world_identifier}'"},
                status=404,
            )

        pdf_field_name = f"pdf_{variant}_{language}"
        if not hasattr(world_book, pdf_field_name):
            return JsonResponse(
                {"error": f"Unsupported field '{pdf_field_name}' on WorldBook"},
                status=400,
            )

        getattr(world_book, pdf_field_name).save(upload.name, upload)
        world_book.save()

        try:
            pdf_path = getattr(world_book, pdf_field_name).path
            image = convert_from_path(pdf_path, last_page=1, dpi=96)[0]

            for lang_code in [code for code, _ in settings.LANGUAGES]:
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                buf.seek(0)
                preview_field_name = f"preview_image_{lang_code}"
                getattr(world_book, preview_field_name).save(
                    f"{world_book.book_title}_{lang_code}.png", buf
                )
            world_book.save()
        except Exception as e:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "PDF uploaded but failed to generate preview images",
                    "error": str(e),
                },
                status=500,
            )

        return JsonResponse(
            {
                "ok": True,
                "world": world_identifier,
                "book": str(world_book.book),
                "field_updated": pdf_field_name,
                "previews": {
                    code: (
                        getattr(world_book, f"preview_image_{code}").url
                        if getattr(world_book, f"preview_image_{code}")
                        else None
                    )
                    for code, _ in settings.LANGUAGES
                },
            }
        )
