from django.template import Library
from django.db.models import Q

from worlds.models import WikiPageGameAction

register = Library()


@register.simple_tag
def entity_work(character, priest_action):
    if character.entity is None or priest_action.work_type is None:
        return []
    return WikiPageGameAction.objects.filter(
        entity_work_type=priest_action.work_type).filter(
            Q(wiki_page__entity=character.entity) | Q(wiki_page__parent__entity=character.entity)
        )

