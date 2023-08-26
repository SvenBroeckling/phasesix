import io

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from rulebook.models import Chapter, Book


class ChapterDetailView(DetailView):
    template_name = "rulebook/chapter_detail.html"
    model = Chapter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chapters"] = Chapter.objects.all()
        return context


class BookPDFView(View):
    def get(self, request, *args, **kwargs):
        book_html = render_to_string(
            "rulebook/book_pdf.html",
            {
                "book": Book.objects.get(id=kwargs["pk"]),
                "base_dir": settings.BASE_DIR,
            },
        )
        font_config = FontConfiguration()

        with open('/tmp/last_book_render.html', 'w') as of:
            of.write(book_html)

        html = HTML(
            file_obj=io.BytesIO(bytes(book_html, encoding="utf-8")),
            base_url="src/",
            encoding="utf-8",
        )
        response = HttpResponse(content_type="application/pdf")
        html.write_pdf(response, font_config=font_config)

        return response
