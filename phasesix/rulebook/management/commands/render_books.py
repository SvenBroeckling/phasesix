from django.core.management import BaseCommand
from django.db.models import Q

from rulebook.models import WorldBook


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-t", "--title_filter", nargs="?", type=str)
        parser.add_argument(
            "-b", "--book_variant", nargs="?", type=str, choices=["online", "print"]
        )
        parser.add_argument(
            "-l", "--language", nargs="?", type=str, choices=["de", "en"]
        )

    def handle(self, *args, **options):
        qs = WorldBook.objects.all()

        if options["title_filter"]:
            qs = qs.filter(
                Q(book_title_de__icontains=options["title_filter"])
                | Q(book_title_en__icontains=options["title_filter"])
            )

        for wb in qs:
            wb.render_pdf(options["language"], options["book_variant"])
            wb.create_preview_images()
