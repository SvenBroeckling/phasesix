import io

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as gt, activate
from sorl.thumbnail import get_thumbnail
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
        ("Baskervville", "Libre Baskerville"),
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

            title = self._render_pdf_title(language_code)
            document = self._render_pdf_content(language_code)
            toc = self._render_pdf_toc(document, language_code)

            for page in reversed(toc.pages):
                document.pages.insert(0, page)
            document.pages.insert(0, title.pages[0])

            buf = io.BytesIO()
            font_config = FontConfiguration()
            document.write_pdf(buf, font_config=font_config)
            buf.seek(0)

            getattr(self, f"pdf_{language_code}").save(
                f"book_pdf_{language_code}.pdf", buf
            )

            if settings.DEBUG:
                import webbrowser

                webbrowser.open(f"file://{getattr(self, f'pdf_{language_code}').path}")
                print(f"{self} {getattr(self, f'pdf_{language_code}').path}")

    def _render_pdf_title(self, language_code: str = "en"):
        title_html = render_to_string(
            "rulebook/pdf/title.html",
            {
                "world_book": self,
            },
        )
        if settings.DEBUG:
            with open(f"/tmp/last_title_render_{language_code}.html", "w") as of:
                of.write(title_html)

        return HTML(string=title_html, base_url="src/").render()

    def _render_pdf_content(self, language_code: str = "en"):
        book_html = render_to_string(
            "rulebook/pdf/book.html",
            {
                "world_book": self,
            },
        )

        if settings.DEBUG:
            with open(f"/tmp/last_book_render_{language_code}.html", "w") as of:
                of.write(book_html)

        return HTML(string=book_html, base_url="src/").render()

    def _render_pdf_toc(self, document, language_code: str = "en"):
        table_of_contents_html = render_to_string(
            "rulebook/pdf/toc.html",
            {
                "world_book": self,
                "bookmark_tree": document.make_bookmark_tree(),
            },
        )

        if settings.DEBUG:
            with open(f"/tmp/last_toc_render_{language_code}.html", "w") as of:
                of.write(table_of_contents_html)

        return HTML(string=table_of_contents_html).render()


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
    identifier = models.CharField(gt("identifier"), max_length=40, unique=True)
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

    def get_absolute_url(self):
        return reverse("rulebook:detail", kwargs={"pk": self.id})

    def get_image_url(self, geometry="180", crop="center"):
        return None

    def get_backdrop_image_url(self, geometry="1800x500", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

    @property
    def text(self):
        with open(self.rules_file.path) as f:
            return f.read()
