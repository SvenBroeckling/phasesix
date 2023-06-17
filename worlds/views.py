# -*- coding: utf-8 -*-
import re

import reversion
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, CreateView, TemplateView
from django.utils.translation import gettext_lazy as _

from worlds.forms import WikiPageForm, WikiPageTextForm
from worlds.models import World, WikiPage, WikiPageImage


class WorldDetailView(DetailView):
    model = World
    template_name = "worlds/world_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class WikiPageDetailView(DetailView):
    model = WikiPage
    template_name = "worlds/wiki_page_detail.html"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class WikiPageEditTextView(DetailView):
    model = WikiPage
    template_name = "worlds/wiki_page_edit.html"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = WikiPageTextForm(instance=self.object)
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = WikiPageTextForm(request.POST, instance=obj)

        if not obj.may_edit(request.user):
            return HttpResponseRedirect(obj.get_absolute_url())

        if form.is_valid():
            with reversion.create_revision():
                form.save()
                reversion.set_user(request.user)
                reversion.set_comment("Edit wiki page text from web interface.")
            return HttpResponseRedirect(obj.get_absolute_url())
        else:
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)


class XhrCreateWikiPageView(TemplateView):
    template_name = "worlds/create_wiki_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["world"] = get_object_or_404(World, id=self.kwargs["world_pk"])
        if "parent_pk" in self.kwargs:
            context["parent"] = get_object_or_404(WikiPage, id=self.kwargs["parent_pk"])
        context["form"] = WikiPageForm()
        return context

    def post(self, request, *args, **kwargs):
        world = get_object_or_404(World, id=self.kwargs["world_pk"])

        if not world.may_edit(request.user):
            return JsonResponse(
                {
                    "error": _("You do not have permission to edit this world."),
                    "status": "error",
                }
            )

        parent = None
        if "parent_pk" in self.kwargs:
            parent = get_object_or_404(WikiPage, id=self.kwargs["parent_pk"])

        form = WikiPageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.created_by = request.user
            page.world = world
            page.parent = parent
            page.save()
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error", "error": form.errors})


class XhrSidebarView(DetailView):
    model = WikiPage
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["may_edit"] = self.object.may_edit(self.request.user)
        except AttributeError:
            context["may_edit"] = False
        return context

    def get_template_names(self):
        return ["worlds/sidebar/" + self.kwargs["sidebar_template"] + ".html"]


class XhrWorldSortSubPagesSidebarView(XhrSidebarView):
    model = World

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model"] = "world"
        context["sub_pages"] = WikiPage.objects.filter(world=self.object, parent=None)
        return context


class XhrWikiPageSortSubPagesSidebarView(XhrSidebarView):
    model = WikiPage

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model"] = "wiki_page"
        context["sub_pages"] = WikiPage.objects.filter(parent=self.object)
        return context


class XhrUpdateItemSortOrderView(View):
    def post(self, request, *args, **kwargs):
        if self.kwargs.get("model") == "world":
            model = World
        else:
            model = WikiPage

        obj = model.objects.get(id=kwargs.get("pk"))

        if not obj.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        for pk, order in request.POST.items():
            WikiPage.objects.filter(id=pk).update(ordering=order)

        return JsonResponse({"status": "ok"})


class XhrSearchLinksView(TemplateView):
    template_name = "worlds/sidebar/_search_links.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q")
        context["pages"] = WikiPage.objects.filter(
            world__slug=self.kwargs["world_slug"]
        ).filter(
            Q(name_de__icontains=context["query"])
            | Q(name_en__icontains=context["query"])
        )
        return context


class XhrUploadImageView(View):
    def post(self, request, *args, **kwargs):
        wiki_page = get_object_or_404(WikiPage, slug=self.kwargs["slug"])
        if not wiki_page.may_edit(request.user):
            return JsonResponse(
                {
                    "error": _("You do not have permission to edit this wiki page."),
                    "status": "error",
                }
            )

        wiki_page.wikipageimage_set.create(
            image=request.FILES.get("file"),
            created_by=request.user,
            image_copyright=request.POST.get("copyright"),
            image_copyright_url=request.POST.get("copyright-url"),
            caption=request.POST.get("caption"),
        )
        return JsonResponse({"status": "ok"})


class XhrAdditionalImagesView(TemplateView):
    template_name = "worlds/sidebar/_additional_images.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(WikiPage, slug=self.kwargs["slug"])
        return context


class XhrAutoTagView(View):
    def post(self, request, *args, **kwargs):
        wiki_page = WikiPage.objects.get(id=kwargs["pk"])

        def _tag_text(text: str, lang: str):
            result = []
            for word in text.split(" "):
                if word.startswith("[[") or word.startswith("{{"):
                    result.append(word)
                    continue
                try:
                    q = re.search(
                        r"([^a-zA-ZäöüÄÖÜ\-]*)([a-zA-ZäöüÄÖÜ\-]+)(.*)", word, re.DOTALL
                    )
                    if q is not None:
                        kwargs = {
                            f"short_name_{lang}__iexact": q.group(2),
                            "world": wiki_page.world,
                        }
                        wp = WikiPage.objects.exclude(id=wiki_page.id).get(**kwargs)
                        name = getattr(wp, f"short_name_{lang}")
                        result.append(f"{q.group(1)}[[{wp.slug}|{name}]]{q.group(3)}")
                    else:
                        result.append(word)
                except WikiPage.DoesNotExist:
                    result.append(word)
            return " ".join(result)

        return JsonResponse(
            {
                "status": "ok",
                "text_de": _tag_text(request.POST["text_de"], "de"),
                "text_en": _tag_text(request.POST["text_en"], "en"),
            }
        )


class WikiPageWithGameValuesView(TemplateView):
    template_name = "worlds/wiki_page_with_game_values.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_list = WikiPage.objects.filter(wikipagegamevalues__id__isnull=False)
        if self.request.world_configuration is not None:
            object_list = object_list.filter(
                world=self.request.world_configuration.world
            )
        context["object_list"] = object_list
        return context
