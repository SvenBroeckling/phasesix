import io

from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as gt, activate
from django.conf import settings
from transmeta import TransMeta
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from homebrew.models import HomebrewModel


class ModelWithCreationInfo(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gt("created by"),
    )
    created_at = models.DateTimeField(gt("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(gt("modified at"), auto_now=True)

    class Meta:
        abstract = True


class WorldBook(models.Model, metaclass=TransMeta):
    BOOK_FONT_CHOICES = (
        ("Oxanium", "Oxanium"),
        ("UnifrakturMaguntia", "UnifrakturMaguntia"),
        ("Baskervville", "Baskervville"),
    )
    world = models.ForeignKey("worlds.World", on_delete=models.CASCADE)
    book = models.ForeignKey("rulebook.Book", on_delete=models.CASCADE)
    pdf_de = models.FileField(
        gt("PDF german"), upload_to="rulebook_pdf", blank=True, null=True
    )
    pdf_en = models.FileField(
        gt("PDF english"), upload_to="rulebook_pdf", blank=True, null=True
    )

    book_title = models.CharField(gt("book title"), max_length=80)
    book_claim = models.CharField(gt("book claim"), max_length=80)
    book_title_image = models.ImageField(
        gt("book title image"), upload_to="rulebook_title_images", max_length=256
    )
    book_heading_font = models.CharField(
        gt("book heading font"),
        max_length=20,
        default="Oxanium",
        choices=BOOK_FONT_CHOICES,
    )
    book_body_font = models.CharField(
        gt("book body font"),
        max_length=20,
        default="Baskervville",
        choices=BOOK_FONT_CHOICES,
    )

    def __str__(self):
        return f"{self.world} - {self.book}"

    class Meta:
        translate = "book_title", "book_claim"

    def render_pdf(self):
        for language_code, language_description in settings.LANGUAGES:
            activate(language_code)
            book_html = render_to_string(
                "rulebook/book_pdf.html",
                {
                    "world_book": self,
                    "base_dir": settings.BASE_DIR,
                },
            )
            font_config = FontConfiguration()

            with open(f"/tmp/last_book_render_{language_code}.html", "w") as of:
                of.write(book_html)

            html = HTML(
                file_obj=io.BytesIO(bytes(book_html, encoding="utf-8")),
                base_url="src/",
                encoding="utf-8",
            )
            buf = io.BytesIO()
            html.write_pdf(buf, font_config=font_config)
            buf.seek(0)
            getattr(self, f"pdf_{language_code}").save(
                f"book_pdf_{language_code}.pdf", buf
            )
            if settings.DEBUG:
                print(getattr(self, f"pdf_{language_code}").path)


class Book(ModelWithCreationInfo, HomebrewModel, metaclass=TransMeta):
    name = models.CharField(gt("name"), max_length=40)
    ordering = models.IntegerField(gt("ordering"), default=0)

    image = models.ImageField(
        gt("image"), upload_to="book_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        gt("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        gt("image copyright url"), max_length=150, blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("ordering",)
        translate = ("name",)
        verbose_name = gt("book")
        verbose_name_plural = gt("books")


class Chapter(ModelWithCreationInfo, HomebrewModel, metaclass=TransMeta):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    name = models.CharField(gt("name"), max_length=40)
    number = models.IntegerField(gt("number"), default=1)
    fa_icon_class = models.CharField(gt("fa icon class"), max_length=32)

    rules_file = models.FileField(
        gt("rules file"), upload_to="rulebook/", blank=True, null=True
    )

    image = models.ImageField(
        gt("image"), upload_to="chapter_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        gt("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        gt("image copyright url"), max_length=150, blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("number",)
        translate = "name", "rules_file"
        verbose_name = gt("chapter")
        verbose_name_plural = gt("chapters")

    @property
    def text(self):
        with open(self.rules_file.path) as f:
            return f.read()
