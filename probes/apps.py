from django.apps import AppConfig


class ProbesConfig(AppConfig):
    """Our own probing of the packages we index.

    Named for what it does rather than after django-probe, whose
    importable name is `django_probe`, so the two can sit side by side.
    We use its AST visitor and its probe registry; everything about
    keeping checkouts, storing profiles and rolling them up is ours.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "probes"
    verbose_name = "Probes"
