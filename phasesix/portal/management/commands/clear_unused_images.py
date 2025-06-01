import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import FileField, ImageField


class Command(BaseCommand):
    help = "Deletes unused files from FileField and ImageField upload directories"

    def handle(self, *args, **options):
        total_bytes_freed = 0
        files_deleted = 0

        for model in apps.get_models():
            file_fields = [
                (f.name, f)
                for f in model._meta.fields
                if isinstance(f, (FileField, ImageField))
            ]

            for field_name, field in file_fields:
                if hasattr(field, "upload_to"):
                    upload_dir = field.upload_to
                    if callable(upload_dir):
                        self.stdout.write(
                            f"Skipping {model.__name__}.{field_name} - dynamic upload_to"
                        )
                        continue

                    full_path = os.path.join(settings.MEDIA_ROOT, upload_dir)
                    if not os.path.exists(full_path):
                        continue

                    for filename in os.listdir(full_path):
                        file_path = os.path.join(full_path, filename)
                        if not os.path.isfile(file_path):
                            continue

                        relative_path = os.path.join(upload_dir, filename)
                        filter_kwargs = {field_name: relative_path}
                        if not model.objects.filter(**filter_kwargs).exists():
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            total_bytes_freed += file_size
                            files_deleted += 1
                            self.stdout.write(f"Deleted: {relative_path}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {files_deleted} files, freed {total_bytes_freed/1024/1024:.2f} MB"
            )
        )
