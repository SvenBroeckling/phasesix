import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import FileField, ImageField

from worlds.models import WikiPage, WikiPageImage

MODEL_BLACKLIST = [
    WikiPage,  # Shares an upload_to with WikiPageImage
    WikiPageImage,  # Shares an upload_to with WikiPage
]


class Command(BaseCommand):
    help = "Deletes unused files from FileField and ImageField upload directories"

    def handle(self, *args, **options):
        self.stderr.write("This command is disabled for now. See MODEL_BLACKLIST")
        self.stderr.write("It falsely deletes files from fields with shared upload_to")
        self.stderr.write("See [WikiPage.image, WikiPageImage.image]")
        self.stderr.write("See [WorldBook.pdf_{variant}_{language}")
        self.stderr.write("See [WorldBook.preview_image_{language}")
        raise CommandError("This command is disabled for now.")

        total_bytes_freed = 0
        files_deleted = 0
        deletion_stats = {}

        for model in apps.get_models():
            if model in MODEL_BLACKLIST:
                continue

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
                            model_name = model.__name__
                            if model_name not in deletion_stats:
                                deletion_stats[model_name] = {}
                            if field_name not in deletion_stats[model_name]:
                                deletion_stats[model_name][field_name] = {
                                    "count": 0,
                                    "size": 0,
                                }
                            deletion_stats[model_name][field_name]["count"] += 1
                            deletion_stats[model_name][field_name]["size"] += file_size
                            self.stdout.write(f"Deleted: {relative_path}")

        if deletion_stats:
            self.stdout.write("\nDeletion Summary:")
            self.stdout.write("-" * 60)
            self.stdout.write(
                f"{'Model':<20} {'Field':<15} {'Count':>8} {'Size (MB)':>12}"
            )
            self.stdout.write("-" * 60)
            for model_name in sorted(deletion_stats.keys()):
                for field_name, stats in deletion_stats[model_name].items():
                    self.stdout.write(
                        f"{model_name:<20} {field_name:<15} {stats['count']:>8} "
                        f"{stats['size'] / 1024 / 1024:>12.2f}"
                    )
            self.stdout.write("-" * 60)

        self.stdout.write(
            self.style.SUCCESS(
                f"Total: Deleted {files_deleted} files, freed {total_bytes_freed / 1024 / 1024:.2f} MB"
            )
        )
