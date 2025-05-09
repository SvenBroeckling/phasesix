# Generated by Django 5.1.7 on 2025-04-14 11:54

from django.db import migrations


def forwards_func(apps, schema_editor):
    SocketLocation = apps.get_model("body_modifications", "SocketLocation")
    SocketLocation.objects.filter(name_en="Head").update(identifier="head")
    SocketLocation.objects.filter(name_en="Torso").update(identifier="torso")
    SocketLocation.objects.filter(name_en="Left Arm").update(identifier="left_arm")
    SocketLocation.objects.filter(name_en="Right Arm").update(identifier="right_arm")
    SocketLocation.objects.filter(name_en="Left Leg").update(identifier="left_leg")
    SocketLocation.objects.filter(name_en="Right Leg").update(identifier="right_leg")


class Migration(migrations.Migration):

    dependencies = [
        ("body_modifications", "0009_socketlocation_identifier"),
    ]

    operations = [migrations.RunPython(forwards_func)]
