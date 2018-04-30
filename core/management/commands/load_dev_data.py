from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "Import development data for local dev"

    def handle(self, *args, **options):
        self.stdout.write("Commencing dev data import")

        for app in settings.INSTALLED_APPS:
            # Attempt to import the app's test.data module.
            try:
                mod_data = import_module('%s.tests.data' % app)
                mod_data.load()

            except ModuleNotFoundError:
                continue
