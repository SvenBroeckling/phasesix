def brand_name(request):
    try:
        return {'brand_name': request.world_configuration.brand_name}
    except AttributeError:
        return {'brand_name': 'PhaseSix'}
