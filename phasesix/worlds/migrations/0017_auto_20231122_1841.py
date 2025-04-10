# Generated by Django 4.2.7 on 2023-11-22 18:41

import re

from django.db import migrations


def forward(apps, schema_editor):
    WikiPage = apps.get_model("worlds", "WikiPage")
    for wiki_page in WikiPage.objects.all():
        if wiki_page.text_de and "{{" in wiki_page.text_de:
            wiki_page.text_de = re.sub(r"w-25,float-end", "image-end", wiki_page.text_de)
            wiki_page.text_de = re.sub(r"w-25,float-start", "image-start", wiki_page.text_de)
            wiki_page.save()
        if wiki_page.text_en and "{{" in wiki_page.text_en:
            wiki_page.text_en = re.sub(r"w-25,float-end", "image-end", wiki_page.text_en)
            wiki_page.text_en = re.sub(r"w-25,float-start", "image-start", wiki_page.text_en)
            wiki_page.save()


class Migration(migrations.Migration):

    dependencies = [
        ('worlds', '0016_auto_20231017_1021'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
