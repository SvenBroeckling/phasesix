#!/usr/bin/env python
import os
import io

from jinja2 import Environment, FileSystemLoader
import markdown2
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from yaml import load, Loader

PRINCE_BINARY = '/usr/sbin/prince'


def create_book(language: str) -> None:
    with open(f'structure_{language}.yml', 'r', encoding='utf-8') as yml_file:
        structure = load(yml_file, Loader=Loader)

    for s in structure:
        with open(os.path.join('src', 'md', s['file']), 'r', encoding='utf-8') as chapter_file:
            s['content'] = markdown2.markdown(chapter_file.read(), extras=['tables'])

    with open('src/book.html', 'r', encoding='utf-8') as template_file:
        template = Environment(loader=FileSystemLoader(searchpath='src')).from_string(template_file.read())
        html = template.render(structure=structure)

    os.makedirs('build', exist_ok=True)
    with open("build/book.rendered.html", 'w') as outfile:
        outfile.write(html)

    font_config = FontConfiguration()
    html = HTML(file_obj=io.BytesIO(bytes(html, encoding='utf-8')), base_url='src/', encoding='utf-8')
    html.write_pdf(f'build/book_{language}.pdf', font_config=font_config)


create_book('de')
#create_book('en')
