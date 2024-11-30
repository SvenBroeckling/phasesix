from django.core.management.base import BaseCommand

from worlds.models import World

import os


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("slug", nargs=1, type=str)

    def handle(self, *args, **options):
        world = World.objects.get(slug=options["slug"][0])

        os.makedirs(world.slug, exist_ok=True)

        for wiki_page in world.wikipage_set.all():
            with open(f"{world.slug}/{wiki_page.slug}.md", "w") as f:
                f.write(wiki_page.text_de)

        with open(f"{world.slug}/all.md", "w") as f:
            for wiki_page in world.wikipage_set.all():
                f.write(f"## {wiki_page.name_de}\n")
                f.write(wiki_page.text_de)
                f.write("\n\n--- \n\n")

        for wiki_page in world.wikipage_set.all():
            with open(f"{world.slug}/{wiki_page.slug}.md", "w") as f:
                f.write(wiki_page.text)
