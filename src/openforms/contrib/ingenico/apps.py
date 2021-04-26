from django.apps import AppConfig


class IngenicoAppConfig(AppConfig):
    name = "openforms.contrib.ingenico"

    def ready(self):
        from . import backends  # noqa
