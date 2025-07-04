import os
from django.core.management.base import BaseCommand
from django.conf import settings
from rulebook.sass_utils import get_weasystrap_css


class Command(BaseCommand):
    help = "Precompiles WeasyStrap SCSS to CSS for faster loading"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Compiling WeasyStrap SCSS to CSS..."))

        # Get the compiled CSS
        try:
            css_content = get_weasystrap_css()

            # Get the path to the CSS file
            css_path = os.path.join(
                settings.STATIC_ROOT, "rulebook", "weasystrap", "weasystrap.css"
            )

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(css_path), exist_ok=True)

            # Write the CSS to the file
            with open(css_path, "w") as f:
                f.write("/* Auto-generated from SCSS - DO NOT EDIT */\n\n")
                f.write(css_content)

            self.stdout.write(
                self.style.SUCCESS(f"Successfully compiled WeasyStrap to {css_path}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error compiling WeasyStrap: {e}"))
