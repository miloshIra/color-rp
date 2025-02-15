from django.apps import AppConfig


class ColoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "coloring"

    def ready(self) -> None:
        import coloring.signals

        return super().ready()
