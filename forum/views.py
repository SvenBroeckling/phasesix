from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormMixin

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

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

