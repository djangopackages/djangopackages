from sys import stdout
from time import gmtime, strftime

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from searchv2.builders import build_1

class Command(NoArgsCommand):
    
    help = "Constructs the search results for the system"    
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing search result building now %s " % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        build_1()
        print >> stdout, "Finished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
