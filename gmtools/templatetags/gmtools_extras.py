from decimal import Decimal

from django.db.models.functions import Length, Coalesce
from django.db.models import (
    Q,
    F,
    DecimalField,
    Value,
    When,
    Case,
    ExpressionWrapper,
    QuerySet,
)
from django.template import Library
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.safestring import mark_safe

register = Library()


@register.filter
def objects_with_missing_translations(qs, translatable_fields):
    for field in translatable_fields:
        qs = qs.annotate(
            **{f"{field}_de_length": Length(f"{field}_de", output_field=DecimalField())}
        )
        qs = qs.annotate(
            **{f"{field}_en_length": Length(f"{field}_en", output_field=DecimalField())}
        )

        # This annotation exists to prevent a division by zero for non-existent german texts
        qs = qs.annotate(
            **{
                f"{field}_length_ratio_divisor": Case(
                    When(
                        **{f"{field}_de_length__gt": "0.0"},
                        then=F(f"{field}_de_length"),
                    ),
                    default=Value(1, output_field=DecimalField()),
                    output_field=DecimalField(),
                )
            },
        )

        # calculate the en to de text ratio of the field in percent
        qs = qs.annotate(
            **{
                f"{field}_length_ratio": ExpressionWrapper(
                    (
                        F(f"{field}_en_length")
                        * Decimal("1.0")  # The Decimal() is a cast for the expression!
                        / F(f"{field}_length_ratio_divisor")
                        * Value(100, output_field=DecimalField())
                    ),
                    output_field=DecimalField(),
                )
            }
        )

    return qs


@register.simple_tag
def translation_field_badge(obj, field_name):
    value = getattr(obj, f"{field_name}_length_ratio") or 0

    badge_class = "bg-success"
    if value < 50:
        badge_class = "bg-warning"
    if value < 20:
        badge_class = "bg-danger"

    return mark_safe(
        f'<span class="badge {badge_class}">{field_name}: {floatformat(value, 2)}</span>'
    )


@register.filter
def model_name(value: QuerySet):
    return value.model.__mro__[0].__name__


@register.simple_tag
def admin_url_for_qs_model(value: QuerySet, pk: int):
    pattern = f"admin:{value.model._meta.app_label}_{value.model.__mro__[0].__name__.lower()}_change"
    return reverse(pattern, args=[pk])
