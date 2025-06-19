import os
import sass
from django.contrib.staticfiles import finders
from django_libsass import SassCompiler


def compile_scss_file(scss_path):
    """
    Compile an SCSS file to CSS using django-libsass.

    Args:
        scss_path: Path to the SCSS file (can be a static path)

    Returns:
        Compiled CSS as string
    """
    if not os.path.isfile(scss_path):
        found_path = finders.find(scss_path)
        if found_path:
            scss_path = found_path
        else:
            raise ValueError(f"SCSS file not found: {scss_path}")

    return sass.compile(filename=scss_path)


def get_weasystrap_css():
    """
    Get the compiled CSS for WeasyStrap.

    Returns:
        Compiled CSS as string
    """
    scss_path = 'weasystrap/weasystrap.scss'
    return compile_scss_file(scss_path)
