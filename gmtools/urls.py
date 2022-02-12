from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from gmtools import views

app_name = 'gmtools'

urlpatterns = [
    url(
        '^template_statistics/$',
        staff_member_required(views.TemplateStatisticsView.as_view()),
        name='template_statistics'),
    url(
        '^assign_spell_cost/$',
        staff_member_required(views.AssignSpellCostView.as_view()),
        name='assign_spell_cost'),
    url(
        '^extension_grid/(?P<type>.*)/$',
        staff_member_required(views.ExtensionGrid.as_view()),
        name='extension_grid'),
]
