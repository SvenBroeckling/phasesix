from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from gmtools import views

app_name = 'gmtools'

urlpatterns = [
    path(
        'template_statistics/',
        staff_member_required(views.TemplateStatisticsView.as_view()),
        name='template_statistics'),
    path(
        'assign_spell_cost/',
        staff_member_required(views.AssignSpellCostView.as_view()),
        name='assign_spell_cost'),
    path(
        'extension_grid/<type>/',
        staff_member_required(views.ExtensionGrid.as_view()),
        name='extension_grid'),
]
