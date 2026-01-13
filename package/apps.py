"""
Package app configuration.
"""

from django.apps import AppConfig


class PackageConfig(AppConfig):
    """Configuration for the package app."""

    name = "package"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Import signals when the app is ready.

        This ensures that signal handlers are connected when Django starts.
        """
        # Import signals to register handlers
        import package.signals  # noqa: F401
