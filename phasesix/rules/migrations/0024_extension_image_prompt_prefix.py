from django.db import migrations, models
import django.utils.translation


class Migration(migrations.Migration):
    dependencies = [
        ("rules", "0023_alter_extension_image_alter_foe_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="extension",
            name="image_prompt_prefix",
            field=models.TextField(
                blank=True,
                default="",
                help_text=django.utils.translation.gettext_lazy(
                    "Optional prompt text prepended to AI image generation."
                ),
                verbose_name=django.utils.translation.gettext_lazy(
                    "image prompt prefix"
                ),
            ),
        ),
    ]
