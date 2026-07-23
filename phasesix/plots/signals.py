from django.db.models import F
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from characters.models import Character
from essential_characters.models import EssentialCharacter
from plots.models import Location, Plot, PlotElement
from rules.models import Foe, FoeAction


def bump_export_versions(plot_ids):
    """Invalidate Foundry modules for plots whose exported material changed."""
    plot_ids = {plot_id for plot_id in plot_ids if plot_id}
    if plot_ids:
        Plot.objects.filter(pk__in=plot_ids).update(
            export_version=F("export_version") + 1
        )


def related_plot_ids(instance, relation_name):
    return instance.__getattribute__(relation_name).values_list("plot_id", flat=True)


@receiver(post_save, sender=PlotElement)
@receiver(pre_delete, sender=PlotElement)
def bump_element_plot_version(sender, instance, **kwargs):
    bump_export_versions([instance.plot_id])


@receiver(m2m_changed, sender=PlotElement.npc.through)
@receiver(m2m_changed, sender=PlotElement.essential_npc.through)
@receiver(m2m_changed, sender=PlotElement.foes.through)
@receiver(m2m_changed, sender=PlotElement.locations.through)
def bump_element_relation_plot_version(sender, instance, action, **kwargs):
    if action.startswith("post_") or action == "pre_clear":
        bump_export_versions([instance.plot_id])


@receiver(post_save, sender=Location)
@receiver(pre_delete, sender=Location)
def bump_location_plot_versions(sender, instance, **kwargs):
    bump_export_versions(related_plot_ids(instance, "plotelement_set"))


@receiver(post_save, sender=Character)
@receiver(pre_delete, sender=Character)
def bump_character_plot_versions(sender, instance, **kwargs):
    bump_export_versions(related_plot_ids(instance, "plotelement_set"))


@receiver(post_save, sender=EssentialCharacter)
@receiver(pre_delete, sender=EssentialCharacter)
def bump_essential_character_plot_versions(sender, instance, **kwargs):
    bump_export_versions(related_plot_ids(instance, "essential_plot_elements"))


@receiver(post_save, sender=Foe)
@receiver(pre_delete, sender=Foe)
def bump_foe_plot_versions(sender, instance, **kwargs):
    bump_export_versions(related_plot_ids(instance, "plotelement_set"))


@receiver(post_save, sender=FoeAction)
@receiver(pre_delete, sender=FoeAction)
def bump_foe_action_plot_versions(sender, instance, **kwargs):
    bump_export_versions(related_plot_ids(instance.foe, "plotelement_set"))


@receiver(m2m_changed, sender=Foe.resistances.through)
@receiver(m2m_changed, sender=Foe.weaknesses.through)
def bump_foe_relation_plot_versions(sender, instance, action, **kwargs):
    if action.startswith("post_") or action == "pre_clear":
        bump_export_versions(related_plot_ids(instance, "plotelement_set"))
