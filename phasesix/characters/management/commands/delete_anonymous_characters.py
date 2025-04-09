from django.core.management import BaseCommand

from characters.models import Character


class Command(BaseCommand):
    def handle(self, *args, **options):
        Character.objects.filter(created_by__isnull=True).delete()