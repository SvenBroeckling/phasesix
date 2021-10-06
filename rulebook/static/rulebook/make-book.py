#!/usr/bin/env python
import os
import subprocess

from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from yaml import load, Loader

PRINCE_BINARY = '/usr/sbin/prince'


def create_book(language: str) -> None:
    with open(f'structure_{language}.yml', 'r') as yml_file:
        structure = load(yml_file, Loader=Loader)

    for s in structure:
        with open(os.path.join('src', 'md', s['file']), 'r') as chapter_file:
            s['content'] = markdown(chapter_file.read(), extensions=['markdown.extensions.tables'])

    with open('src/book.html', 'r') as template_file:
        template = Environment(loader=FileSystemLoader(searchpath='src')).from_string(template_file.read())
        html = template.render(structure=structure)

    os.makedirs('build', exist_ok=True)
    with open("build/book.rendered.html", 'w') as outfile:
        outfile.write(html)

    cd = os.getcwd()
    os.chdir('src')
    try:
        p = subprocess.Popen([PRINCE_BINARY, '--insecure', '-', '-o', f'../build/book_{language}.pdf'],
                             stdin=subprocess.PIPE)
        p.stdin.write(html.encode('utf-8'))
        p.stdin.close()
    finally:
        os.chdir(cd)


create_book('de')
create_book('en')
