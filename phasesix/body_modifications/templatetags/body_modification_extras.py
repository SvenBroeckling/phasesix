from django.utils.translation import gettext_lazy as _
from django.template import Library

register = Library()


@register.simple_tag
def bio_strain_display(bio_strain):
    if bio_strain > 0:
        return _(f"Causes {bio_strain} biostrain")
    elif bio_strain < 0:
        return _(f"Reduces {abs(bio_strain)} biostrain")
    return _(f"Neutral biostrain")


@register.simple_tag
def energy_display(energy):
    if energy > 0:
        return _(f"Consumes {energy} mA energy")
    elif energy < 0:
        return _(f"Produces {abs(energy)} mA energy")
    return _(f"Neutral energy")


@register.inclusion_tag(
    "body_modifications/_body_modification_widget.html", takes_context=True
)
def body_modification_widget(
    context, body_modification, character=None, add_button=False
):
    context.update(
        {
            "body_modification": body_modification,
            "character": character,
            "add_button": add_button,
        }
    )
    return context
