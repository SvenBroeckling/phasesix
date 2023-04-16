from django.utils.translation import gettext as _

def brand_information(request):
    obj = request.world_configuration
    if obj is not None:
        return {
            'brand_name': obj.brand_name,
            'brand_domain_name': obj.dns_domain_name,
            'brand_description': obj.description,
        }
    return {
        'brand_name': 'Phase Six',
        'brand_domain_name': 'phasesix.org',
        'brand_description': _("Do you need a simple and fast rulebook to play your stories as a pen'n'paper roleplaying game? Phase Six is a quick to play roleplaying game rulebook that can be used in any setting."),
    }
