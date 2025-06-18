from django.core.management import BaseCommand

from rulebook.models import WorldBook


class Command(BaseCommand):
    def handle(self, *args, **options):
        for wb in WorldBook.objects.all():
            wb.render_pdf()
