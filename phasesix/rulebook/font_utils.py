import glob
import os
import re

from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe


def get_font_dirs():
    static_fonts = finders.find("theme/fonts")
    if static_fonts:
        return [
            d for d in glob.glob(os.path.join(static_fonts, "*")) if os.path.isdir(d)
        ]
    return []


def get_font_choices():
    font_choices = set()
    for font_dir in get_font_dirs():
        css_path = os.path.join(font_dir, "stylesheet.css")
        if os.path.exists(css_path):
            with open(css_path) as f:
                content = f.read()
                font_families = re.findall(r"font-family:\s*'([^']+)'", content)
                for family in font_families:
                    font_choices.add((family, family))
    return sorted(list(font_choices))


def load_stylesheet(font_path):
    css_path = os.path.join(font_path, "stylesheet.css")
    if not os.path.exists(css_path):
        return ""

    with open(css_path) as f:
        content = f.read()

    def replace_url(match):
        url = match.group(1).strip("'\"")
        if url.startswith(("http://", "https://", "/")):
            return f"url({url})"
        return f"url({os.path.join(os.path.dirname(css_path), url)})"

    return re.sub(r"url\((.*?)\)", replace_url, content)


def get_accumulated_fonts_css():
    return mark_safe(
        "\n".join(load_stylesheet(font_dir) for font_dir in get_font_dirs())
    )
