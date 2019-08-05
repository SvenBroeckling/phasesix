from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from gmtools import views

app_name = 'gmtools'

urlpatterns = [
    url(
        '^extension_grid/(?P<type>.*)/$',
        staff_member_required(views.ExtensionGrid.as_view()),
        name='extension_grid'),
    url('^combat_sim/$', staff_member_required(views.CombatSimView.as_view()), name='combat_sim'),
]
