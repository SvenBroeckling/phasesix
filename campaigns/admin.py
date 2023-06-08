from django.contrib import admin

from campaigns.models import Campaign, Roll


class RollAdmin(admin.ModelAdmin):
    list_display = (
    'campaign', 'character', 'header', 'roll_string', 'results_csv', 'modifier', 'minimum_roll')
    list_filter = ('campaign', 'character')


admin.site.register(Campaign)
admin.site.register(Roll, RollAdmin)
