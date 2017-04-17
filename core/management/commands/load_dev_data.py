from sys import stdout

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule


class Command(NoArgsCommand):
    
    help = "Import development data for local dev"
    
    def handle(self, *args, **options): 
        print("Commencing dev data import", file=stdout)

        for app in settings.INSTALLED_APPS:
            mod = import_module(app)
            # Attempt to import the app's test.data module.
            try:
                mod_data = import_module('%s.tests.data' % app)
                mod_data.load()
            except:
                # Decide whether to bubble up this error. If the app just
                # doesn't have an test.data module, we can ignore the error
                # attempting to import it, otherwise we want it to bubble up.
                if module_has_submodule(mod, 'test.data'):
                    raise

