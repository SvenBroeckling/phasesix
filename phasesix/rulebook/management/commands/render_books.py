from django.core.management import BaseCommand
from django.conf import settings

from rulebook.models import WorldBook


class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.DEBUG:
            WorldBook.objects.first().render_pdf()
            return

        for wb in WorldBook.objects.all():
            wb.render_pdf()
