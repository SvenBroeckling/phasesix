from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import Board, Thread
from .forms import NewThreadForm, NewPostForm


class IndexView(TemplateView):
    template_name = 'forum/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['boards'] = Board.objects.order_by('is_staff_only', 'name')
        return context


class BoardDetailView(FormMixin, DetailView):
    model = Board
    form_class = NewThreadForm

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_staff_only:
            if not request.user.is_authenticated or request.user.is_staff:
                messages.error(request, _('You have no access to this forum'))
                return HttpResponseRedirect(reverse('forum:index'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = self.get_form()

        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if obj.is_staff_only and not request.user.is_staff:
            return HttpResponseForbidden()

        if form.is_valid():
            thread = Thread.objects.create(
                board=obj,
                name=form.cleaned_data['name'],
                created_by=request.user)
            thread.post_set.create(
                text=form.cleaned_data['text'],
                created_by=request.user)
            return HttpResponseRedirect(thread.get_absolute_url())
        else:
            return self.form_invalid(form)


class ThreadDetailView(FormMixin, DetailView):
    model = Thread
    form_class = NewPostForm

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.board.is_staff_only:
            if not request.user.is_authenticated or request.user.is_staff:
                messages.error(request, _('You have no access to this forum'))
                return HttpResponseRedirect(reverse('forum:index'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = self.get_form()

        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if obj.board.is_staff_only and not request.user.is_staff:
            return HttpResponseForbidden()

        if form.is_valid():
            obj.post_set.create(
                text=form.cleaned_data['text'],
                created_by=request.user)
            return HttpResponseRedirect(obj.get_absolute_url())
        else:
            return self.form_invalid(form)
