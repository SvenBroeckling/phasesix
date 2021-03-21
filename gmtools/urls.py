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
        '^extension_grid/(?P<type>.*)/$',
        staff_member_required(views.ExtensionGrid.as_view()),
        name='extension_grid'),
]
