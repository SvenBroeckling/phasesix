from django.views.generic import ListView

from body_modifications.models import BodyModificationType


class BodyModificationTypeListView(ListView):
    model = BodyModificationType
