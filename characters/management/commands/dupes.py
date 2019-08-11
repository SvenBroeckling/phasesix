from django.core.management import BaseCommand
from django.utils.translation import activate

from rules.models import Template


class Command(BaseCommand):
    def handle(self, *args, **options):
        activate('de')
        for t in Template.objects.all():
            if Template.objects.filter(name_de=t.name_de).count() > 1:
                print("{} {}".format(
                    t, 'http://phasesix.org/admin/rules/template/{}/change'.format(t.id)
                ))
