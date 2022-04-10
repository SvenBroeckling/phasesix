import itertools

from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from armory.models import ItemType, Item, WeaponType, Weapon, RiotGear
from magic.models import BaseSpell
from rules.models import Knowledge, Extension, Template, Lineage


class LatestNewAdmin(Feed):
    link = '/'

    def title(self):
        return _('Phase Six latest additions')

    def description(self):
        return _('New Items, Templates and other things from Phase Six')

    def items(self):
        return itertools.chain(
            Lineage.objects.order_by('-created_at')[:30],
            Knowledge.objects.order_by('-created_at')[:30],
            Extension.objects.order_by('-created_at')[:30],
            Template.objects.order_by('-created_at')[:30],
            ItemType.objects.order_by('-created_at')[:30],
            Item.objects.order_by('-created_at')[:30],
            BaseSpell.objects.order_by('-created_at')[:30],
            WeaponType.objects.order_by('-created_at')[:30],
            Weapon.objects.order_by('-created_at')[:30],
            RiotGear.objects.order_by('-created_at')[:30],
        )

    def item_link(self, item):
        url = reverse(
            "admin:%s_%s_change" % (
                item._meta.app_label,
                item._meta.model_name), args=(item.id,))
        return 'http://phasesix.org' + url

    def item_title(self, item):
        return "%s: %s" % (item.__class__.__name__, item)

    def item_pubdate(self, item):
        return item.created_at


class LatestModifiedAdmin(LatestNewAdmin):

    def title(self):
        return _('Phase Six latest updates')

    def items(self):
        return itertools.chain(
            Lineage.objects.order_by('-modified_at')[:30],
            Knowledge.objects.order_by('-modified_at')[:30],
            Extension.objects.order_by('-modified_at')[:30],
            Template.objects.order_by('-modified_at')[:30],
            BaseSpell.objects.order_by('-modified_at')[:30],
            ItemType.objects.order_by('-modified_at')[:30],
            Item.objects.order_by('-modified_at')[:30],
            WeaponType.objects.order_by('-modified_at')[:30],
            Weapon.objects.order_by('-modified_at')[:30],
            RiotGear.objects.order_by('-modified_at')[:30],
        )

    def item_pubdate(self, item):
        return item.modified_at
