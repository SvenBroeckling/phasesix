from django.templatetags.static import static
from django.utils.translation import gettext as _


def brand_information(request):
    obj = request.world_configuration
    if obj is not None:
        world = obj.world
        return {
            "brand_name": world.brand_name,
            "brand_domain_name": obj.dns_domain_name,
            "brand_description": world.description_1,
            "brand_logo": world.brand_logo.url,
        }
    return {
        "brand_name": "Phase Six",
        "brand_domain_name": "phasesix.org",
        "brand_description": _(
            "Phase Six is a simple, adaptable set of rules for roleplaying adventures, designed to suit a wide variety "
            "of settings and themes. The system requires only a few standard six-sided dice and some paper. You can "
            "start by exploring the rules or creating your own character."
        ),
        "brand_logo": static("img/phasesix_logo_2.png"),
    }
