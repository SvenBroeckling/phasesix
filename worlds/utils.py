from django.template import Engine, TemplateDoesNotExist


def get_world_configuration_template(request, template_name):
    if not request.world_configuration:
        return template_name

    parts = template_name.split('.')
    parts[0] = f'{parts[0]}_{request.world_configuration.world.template_addon}'
    world_template_name = ".".join(parts)

    engine = Engine.get_default()
    try:
        engine.get_template(world_template_name)
        return world_template_name
    except TemplateDoesNotExist:
        return template_name
