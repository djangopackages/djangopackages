"""
Grid app configuration.
"""

from django.apps import AppConfig


class GridConfig(AppConfig):
    """Configuration for the grid app."""

    name = "grid"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Import signals when the app is ready.

        This ensures that signal handlers are connected when Django starts.
        """
        # Import signals to register handlers
        import grid.signals  # noqa: F401
