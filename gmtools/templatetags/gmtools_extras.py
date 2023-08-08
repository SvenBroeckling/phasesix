from decimal import Decimal

from django.db.models.functions import Length, Coalesce
from django.db.models import Q, F, DecimalField, Value, When, Case
from django.template import Library

register = Library()


@register.filter
def objects_with_missing_translations(qs, translatable_fields):
    q = Q()
    for field in translatable_fields:
        qs = qs.annotate(
            **{f"{field}_de_length": Length(f"{field}_de", output_field=DecimalField())}
        )
        qs = qs.annotate(
            **{f"{field}_en_length": Length(f"{field}_en", output_field=DecimalField())}
        )
        qs = qs.annotate(
            **{
                f"{field}_length_ratio": F(f"{field}_en_length")
                / Case(
                    When(
                        **{f"{field}_de_length__gt": "0.0"},
                        then=F(f"{field}_de_length"),
                    ),
                    When(**{f"{field}_de_length": "0"}, then=Value(1)),
                    output_field=DecimalField(),
                )
                * Value(100, output_field=DecimalField())
            },
        )

        # q |= Q(**{f"{field}_de__isnull": True})
        # q |= Q(**{f"{field}_en__isnull": True})

    return qs.filter(q)
