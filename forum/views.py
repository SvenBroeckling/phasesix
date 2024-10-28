from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin

from .forms import NewThreadForm, NewPostForm
from .models import Board, Thread, Post


class BoardDetailView(FormMixin, DetailView):
    model = Board
    form_class = NewThreadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["boards"] = Board.objects.order_by("is_staff_only", "name")
        if self.request.user.is_authenticated:
            context["is_subscribed"] = self.object.boardsubscription_set.filter(
                user=self.request.user
            ).exists()
        return context

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_staff_only:
            if not request.user.is_authenticated or not request.user.is_staff:
                messages.error(request, _("You have no access to this forum"))
                return HttpResponseRedirect(reverse("characters:index"))
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
                board=obj, name=form.cleaned_data["name"], created_by=request.user
            )
            post = thread.post_set.create(
                text=form.cleaned_data["text"], created_by=request.user
            )
            thread.notify_subscribers(post)
            return HttpResponseRedirect(thread.get_absolute_url())
        else:
            return self.form_invalid(form)


class ThreadDetailView(FormMixin, DetailView):
    model = Thread
    form_class = NewPostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["boards"] = Board.objects.order_by("is_staff_only", "name")
        if self.request.user.is_authenticated:
            context["is_subscribed"] = self.object.threadsubscription_set.filter(
                user=self.request.user
            ).exists()
            context["is_subscribed_to_board"] = (
                self.object.board.boardsubscription_set.filter(
                    user=self.request.user
                ).exists()
            )
        return context

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.board.is_staff_only:
            if not request.user.is_authenticated or not request.user.is_staff:
                messages.error(request, _("You have no access to this forum"))
                return HttpResponseRedirect(reverse("characters:index"))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = self.get_form()

        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if obj.board.is_staff_only and not request.user.is_staff:
            return HttpResponseForbidden()

        if form.is_valid():
            post = obj.post_set.create(
                text=form.cleaned_data["text"], created_by=request.user
            )
            obj.notify_subscribers(post)
            return HttpResponseRedirect(obj.get_absolute_url())
        else:
            return self.form_invalid(form)


class XhrImageUploadView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        image = request.FILES.get("image")
        if image:
            image = request.user.forumimage_set.create(image=image)
            markdown_url = f"![{_("Image")}]({image.image.url})"
            return JsonResponse({"status": "ok", "markdown_link": markdown_url})
        else:
            return JsonResponse({"status": "error"})


class RawPostTextView(DetailView):
    model = Post

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.thread.board.is_staff_only:
            if not request.user.is_authenticated or not request.user.is_staff:
                messages.error(request, _("You have no access to this forum"))
                return HttpResponseRedirect(reverse("characters:index"))
        text = "\n".join([f"> {line}" for line in obj.text.splitlines()])
        return JsonResponse(
            {"text": f"{text}\n\n"},
        )


class SubscribeView(View):
    def post(self, request, *args, **kwargs):
        if kwargs["mode"] == "thread":
            if request.POST.get("value", "") == "true":
                request.user.threadsubscription_set.create(
                    thread=Thread.objects.get(id=request.POST.get("object"))
                )
            else:
                request.user.threadsubscription_set.filter(
                    thread__id=request.POST.get("object")
                ).delete()
        else:
            if request.POST.get("value", "") == "true":
                request.user.boardsubscription_set.create(
                    board=Board.objects.get(id=request.POST.get("object"))
                )
            else:
                request.user.boardsubscription_set.filter(
                    board__id=request.POST.get("object")
                ).delete()

        return JsonResponse({"status": "ok"})
