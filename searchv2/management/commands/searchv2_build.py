from sys import stdout
from time import gmtime, strftime

from searchv2.builders import build_1

# https://docs.djangoproject.com/en/1.11/releases/1.8/#django-core-management-noargscommand
try:
    from django.core.management.base import NoArgsCommand as BaseCommand
except ImportError:
    from django.core.management import BaseCommand


class Command(BaseCommand):

    help = "Constructs the search results for the system"

    def handle(self, *args, **options):

        print("Commencing search result building now %s " % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()), file=stdout)
        build_1()
        print("Finished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()), file=stdout)
