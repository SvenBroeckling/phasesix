from django.template import Library
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = Library()


@register.inclusion_tag("modals_sidebars/site_modal.html")
def site_modal():
    return {}


@register.inclusion_tag("modals_sidebars/sidebar_right.html")
def sidebar_right():
    return {}


@register.simple_tag
def modals_sidebars_javascript():
    js_modules = [
        static("modals_sidebars/js/sidebar_right.js"),
        static("modals_sidebars/js/fetch_form.js"),
        static("modals_sidebars/js/modals.js"),
        static("modals_sidebars/js/action_trigger.js"),
    ]
    return mark_safe(
        "\n".join([f'<script type="module" src="{js}"></script>' for js in js_modules])
    )
