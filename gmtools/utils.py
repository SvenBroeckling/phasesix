from django import apps
from homebrew.models import HomebrewModel


def get_all_models():
    return apps.apps.get_models()


def get_homebrew_models():
    return [model for model in get_all_models() if HomebrewModel in model.__mro__]


def get_models_with_translations():
    return [
        model
        for model in get_all_models()
        if getattr(model._meta, "translatable_fields", None) is not None
    ]
