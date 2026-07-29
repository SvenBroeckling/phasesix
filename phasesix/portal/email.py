from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

EMAIL_THEMES = {
    "tirakan": {
        "background": "#080808",
        "surface": "#151515",
        "primary": "#9f784f",
        "text": "#e2d8c9",
        "muted": "#b7afa5",
    },
    "nexus": {
        "background": "#0e1217",
        "surface": "#0e1113",
        "primary": "#267e89",
        "text": "#e4f5f7",
        "muted": "#a7c4c7",
    },
    "phasesix": {
        "background": "#0c1118",
        "surface": "#141c26",
        "primary": "#4f8fdb",
        "text": "#edf5fc",
        "muted": "#b7c5d5",
    },
}


def email_brand_context(request):
    world = getattr(request, "world", None)
    identifier = getattr(getattr(world, "extension", None), "identifier", "")
    theme = EMAIL_THEMES.get(identifier, EMAIL_THEMES["phasesix"])
    return {
        "email_brand_name": getattr(world, "brand_name", "Phase Six"),
        "email_theme": theme,
        "email_domain": request.get_host(),
    }


def activation_url(request, activation_key, next_url=""):
    params = {"activation_key": activation_key}
    if next_url:
        params["next"] = next_url
    return f"{request.build_absolute_uri(reverse('django_registration_activate'))}?{urlencode(params)}"


def send_templated_email(
    subject, text_template, html_template, context, recipients, fail_silently=False
):
    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
    )
    message.attach_alternative(html_body, "text/html")
    return message.send(fail_silently=fail_silently)
