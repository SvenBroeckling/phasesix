from django import template
from weasystrap.sass_utils import get_weasystrap_css

register = template.Library()


@register.simple_tag
def include_weasystrap():
    """Compile and include WeasyStrap SCSS for PDF templates"""
    compiled_css = get_weasystrap_css()

    return f"<style>{compiled_css}</style>"
