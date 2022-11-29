# -*- coding: utf-8 -*-
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, CreateView, TemplateView
from django.utils.translation import gettext_lazy as _

from worlds.forms import WikiPageForm, WikiPageTextForm
from worlds.models import World, WikiPage


class WorldDetailView(DetailView):
    model = World
    template_name = 'worlds/world_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context


class WikiPageDetailView(DetailView):
    model = WikiPage
    template_name = 'worlds/wiki_page_detail.html'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context


class WikiPageEditTextView(DetailView):
    model = WikiPage
    template_name = 'worlds/wiki_page_edit.html'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = WikiPageTextForm(instance=self.object)
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = WikiPageTextForm(request.POST, instance=obj)

        if not obj.may_edit(request.user):
            return HttpResponseRedirect(obj.get_absolute_url())

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(obj.get_absolute_url())
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


class XhrCreateWikiPageView(TemplateView):
    template_name = 'worlds/create_wiki_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['world'] = get_object_or_404(World, id=self.kwargs['world_pk'])
        if 'parent_pk' in self.kwargs:
            context['parent'] = get_object_or_404(WikiPage, id=self.kwargs['parent_pk'])
        context['form'] = WikiPageForm()
        return context

    def post(self, request, *args, **kwargs):
        world = get_object_or_404(World, id=self.kwargs['world_pk'])

        if not world.may_edit(request.user):
            return JsonResponse({
                'error': _('You do not have permission to edit this world.'),
                'status': 'error',
            })

        parent = None
        if 'parent_pk' in self.kwargs:
            parent = get_object_or_404(WikiPage, id=self.kwargs['parent_pk'])

        form = WikiPageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.created_by = request.user
            page.world = world
            page.parent = parent
            page.save()
            return JsonResponse({'status': 'ok'})
        return JsonResponse({
            'status': 'error',
            'error': form.errors
        })


class XhrSidebarView(DetailView):
    model = WikiPage
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['may_edit'] = self.object.may_edit(self.request.user)
        except AttributeError:
            context['may_edit'] = False
        return context

    def get_template_names(self):
        return ['worlds/sidebar/' + self.kwargs['sidebar_template'] + '.html']


class XhrSearchLinksView(TemplateView):
    template_name = 'worlds/sidebar/_search_links.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q')
        context['pages'] = WikiPage.objects.filter(
            world__slug=self.kwargs['world_slug']).filter(
            Q(name_de__icontains=context['query']) | Q(name_en__icontains=context['query'])
        )
        return context


class XhrUploadImageView(View):
    def post(self, request, *args, **kwargs):
        wiki_page = get_object_or_404(WikiPage, slug=self.kwargs['slug'])
        if not wiki_page.may_edit(request.user):
            return JsonResponse({
                'error': _('You do not have permission to edit this wiki page.'),
                'status': 'error',
            })

        wiki_page.wikipageimage_set.create(
            image=request.FILES.get('file'),
            created_by=request.user,
            image_copyright=request.POST.get('copyright'),
            image_copyright_url=request.POST.get('copyright-url'),
            caption=request.POST.get('caption'))
        return JsonResponse({'status': 'ok'})


class XhrAdditionalImagesView(TemplateView):
    template_name = 'worlds/sidebar/_additional_images.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = get_object_or_404(WikiPage, slug=self.kwargs['slug'])
        return context

