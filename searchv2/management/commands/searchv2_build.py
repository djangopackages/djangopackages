from sys import stdout
from time import gmtime, strftime

from django.core.management.base import BaseCommand
from django.conf import settings

from searchv2.builders import build_1
from core.utils import healthcheck


class Command(BaseCommand):

    help = "Constructs the search results for the system"

    def handle(self, *args, **options):

        print("Commencing search result building now %s " % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()), file=stdout)
        build_1()
        print("Finished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()), file=stdout)
        healthcheck(settings.SEARCHV2_HEALTHCHECK_URL)
