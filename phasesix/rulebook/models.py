import io

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as gt, activate
from pdf2image import convert_from_path
from sorl.thumbnail import get_thumbnail
from transmeta import TransMeta
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from homebrew.models import HomebrewModel
from phasesix.models import ModelWithImage, PhaseSixModel
from rulebook.font_utils import get_font_choices


class ModelWithCreationInfo(PhaseSixModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gt("created by"),
    )

    class Meta:
        abstract = True


BOOK_VARIANTS = ["online", "print"]


class WorldBook(models.Model, metaclass=TransMeta):
    world = models.ForeignKey("worlds.World", on_delete=models.CASCADE)
    book = models.ForeignKey("rulebook.Book", on_delete=models.CASCADE)
    description = models.TextField(gt("description"), blank=True, null=True)

    ordering = models.IntegerField(gt("ordering"), default=0)

    pdf_online_de = models.FileField(
        gt("PDF german online"), upload_to="rulebook_pdf", blank=True, null=True
    )
    pdf_online_en = models.FileField(
        gt("PDF english online"), upload_to="rulebook_pdf", blank=True, null=True
    )
    pdf_print_de = models.FileField(
        gt("PDF german print"), upload_to="rulebook_pdf", blank=True, null=True
    )
    pdf_print_en = models.FileField(
        gt("PDF english print"), upload_to="rulebook_pdf", blank=True, null=True
    )
    preview_image_de = models.ImageField(
        gt("preview image german"),
        upload_to="rulebook_preview_images",
        blank=True,
        null=True,
    )
    preview_image_en = models.ImageField(
        gt("preview image english"),
        upload_to="rulebook_preview_images",
        blank=True,
        null=True,
    )

    disabled_chapters = models.ManyToManyField("rulebook.Chapter", blank=True)

    book_title = models.CharField(gt("book title"), max_length=80)
    book_claim = models.CharField(gt("book claim"), max_length=80)
    book_title_image = models.ImageField(
        gt("book title image"), upload_to="rulebook_title_images", max_length=256
    )
    book_website = models.URLField(gt("book website"), blank=True, null=True)
    book_heading_font = models.CharField(
        gt("book heading font"),
        max_length=20,
        default="Oxanium",
        choices=get_font_choices(),
    )
    book_body_font = models.CharField(
        gt("book body font"),
        max_length=20,
        default="Playfair Display",
        choices=get_font_choices(),
    )

    def __str__(self):
        return f"{self.world} - {self.book}"

    class Meta:
        ordering = ("ordering",)
        translate = "book_title", "book_claim", "description"

    @property
    def identifier(self):
        return self.world.identifier

    @property
    def chapters(self):
        return self.book.chapter_set.exclude(id__in=self.disabled_chapters.all())

    def create_preview_images(self):
        """
        Create preview images for the online variant of this rulebook.
        """
        for language_code, language_description in settings.LANGUAGES:
            pdf = getattr(self, f"pdf_online_{language_code}")
            if pdf:
                buf = io.BytesIO()
                image = convert_from_path(pdf.path, last_page=1, dpi=96)[0]
                image.save(buf, format="PNG")
                buf.seek(0)
                getattr(self, f"preview_image_{language_code}").save(
                    f"{self.book_title}_{language_code}.png", buf
                )

    def render_pdf(self, language=None, variant=None):
        languages = [(language, language)] if language else settings.LANGUAGES
        variants = [variant] if variant else BOOK_VARIANTS

        for language_code, language_description in languages:
            activate(language_code)
            for variant in variants:
                if settings.DEBUG:
                    print(f"Rendering PDF for {self} ({language_code}, {variant})")

                title = self._render_pdf_title(variant, language_code)
                document = self._render_pdf_content(variant, language_code)
                toc = self._render_pdf_toc(variant, document, language_code)

                for page in reversed(toc.pages):
                    document.pages.insert(0, page)
                document.pages.insert(0, title.pages[0])

                buf = io.BytesIO()
                font_config = FontConfiguration()
                document.write_pdf(buf, font_config=font_config)
                buf.seek(0)

                getattr(self, f"pdf_{variant}_{language_code}").save(
                    f"{self.book_title}_{variant}_{language_code}.pdf", buf
                )

                if settings.DEBUG:
                    import webbrowser

                    webbrowser.open(
                        f"file://{getattr(self, f'pdf_{variant}_{language_code}').path}"
                    )

    def _render_pdf_title(self, variant: str = "online", language_code: str = "en"):
        title_html = render_to_string(
            "rulebook/pdf/title.html",
            {
                "world_book": self,
                "variant": variant,
            },
        )
        if settings.DEBUG:
            with open(f"/tmp/last_title_render_{language_code}.html", "w") as of:
                of.write(title_html)

        return HTML(string=title_html, base_url="src/").render()

    def _render_pdf_content(self, variant: str = "online", language_code: str = "en"):
        book_html = render_to_string(
            "rulebook/pdf/book.html",
            {
                "world_book": self,
                "variant": variant,
            },
        )

        if settings.DEBUG:
            with open(f"/tmp/last_book_render_{language_code}.html", "w") as of:
                of.write(book_html)

        return HTML(string=book_html, base_url="src/").render()

    def _render_pdf_toc(
        self, variant: str = "online", document=None, language_code: str = "en"
    ):
        table_of_contents_html = render_to_string(
            "rulebook/pdf/toc.html",
            {
                "world_book": self,
                "variant": variant,
                "bookmark_tree": document.make_bookmark_tree(),
            },
        )

        if settings.DEBUG:
            with open(f"/tmp/last_toc_render_{language_code}.html", "w") as of:
                of.write(table_of_contents_html)

        return HTML(string=table_of_contents_html).render()


class Book(ModelWithCreationInfo, ModelWithImage, HomebrewModel, metaclass=TransMeta):
    name = models.CharField(gt("name"), max_length=40)
    ordering = models.IntegerField(gt("ordering"), default=0)
    image_upload_to = "book_images"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("ordering",)
        translate = ("name",)
        verbose_name = gt("book")
        verbose_name_plural = gt("books")


class Chapter(
    ModelWithCreationInfo, ModelWithImage, HomebrewModel, metaclass=TransMeta
):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    image_upload_to = "chapter_images"
    name = models.CharField(gt("name"), max_length=40)
    number = models.IntegerField(gt("number"), default=1)
    identifier = models.CharField(gt("identifier"), max_length=40, unique=True)
    fa_icon_class = models.CharField(gt("fa icon class"), max_length=32)

    rules_file = models.FileField(
        gt("rules file"), upload_to="rulebook/", blank=True, null=True
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
