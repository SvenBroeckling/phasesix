from django.core.management.base import BaseCommand
from django.utils.translation import activate
from rules.models import Template, Extension, CHARACTER_ATTRIBUTE_CHOICES, Skill

class Command(BaseCommand):
    def handle(self, *args, **options):
        activate("de")
        attributes = {}
        attributes_count = {}
        skills = {}
        skills_count = {}

        for a in CHARACTER_ATTRIBUTE_CHOICES:
            attributes[a[0]] = {e: 0 for e in Extension.objects.all()}
            attributes_count[a[0]] = {e: 0 for e in Extension.objects.all()}

        for s in Skill.objects.all():
            skills[s] = {e: 0 for e in Extension.objects.all()}
            skills_count[s] = {e: 0 for e in Extension.objects.all()}

        for t in Template.objects.all():
            for m in t.templatemodifier_set.all():
                if m.attribute:
                    attributes[m.attribute][m.template.extension] += m.attribute_modifier
                    attributes_count[m.attribute][m.template.extension] += 1
                if m.skill:
                    skills[m.skill][m.template.extension] += m.skill_modifier
                    skills_count[m.skill][m.template.extension] += 1


        print()
        print()
        print("Sums")
        print(" " * 26 + "{} {} {} {} {}".format(*[str(e)[:3] for e in Extension.objects.all()]))
        for a, data in attributes.items():
            print("{:25s} {:3d} {:3d} {:3d} {:3d} {:3d}".format(*[a] + [i for d, i in data.items()]))

        print()

        print(" " * 26 + "{} {} {} {} {}".format(*[str(e)[:3] for e in Extension.objects.all()]))
        for a, data in skills.items():
            print("{:25s} {:3d} {:3d} {:3d} {:3d} {:3d}".format(*[str(a)] + [i for d, i in data.items()]))


        print()
        print()
        print("Counts")
        print(" " * 26 + "{} {} {} {} {}".format(*[str(e)[:3] for e in Extension.objects.all()]))
        for a, data in attributes_count.items():
            print("{:25s} {:3d} {:3d} {:3d} {:3d} {:3d}".format(*[a] + [i for d, i in data.items()]))

        print()

        print(" " * 26 + "{} {} {} {} {}".format(*[str(e)[:3] for e in Extension.objects.all()]))
        for a, data in skills_count.items():
            print("{:25s} {:3d} {:3d} {:3d} {:3d} {:3d}".format(*[str(a)] + [i for d, i in data.items()]))
