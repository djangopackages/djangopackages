from socket import error as socket_error
from sys import stdout
from time import sleep, gmtime, strftime
from xml.parsers.expat import ExpatError
from xmlrpclib import ProtocolError

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from package.models import Package

class Command(NoArgsCommand):
    
    help = "Updates all the packages in the system. Commands belongs to django-packages.apps.package"    
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing package updating now at %s " % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        
        for index, package in enumerate(Package.objects.all()):
            try:
                try:
                    package.fetch_metadata()
                    package.fetch_commits()
                except socket_error, e:
                    print >> stdout, "For '%s', threw a socket.error: %s" % (package.title, e)
                    continue
            except RuntimeError, e:
                message = "For '%s', too many requests issued to repo threw a RuntimeError: %s" % (package.title, e)
                print >> stdout, message
                continue
            except UnicodeDecodeError, e:
                message = "For '%s', UnicodeDecodeError: %s" % (package.title, e)
                print >> stdout, message
                continue
            except ProtocolError, e:
                message = "For '%s', xmlrpc.ProtocolError: %s" % (package.title, e)
                print >> stdout, message
                continue
            except ExpatError, e:
                message = "For '%s', ExpatError: %s" % (package.title, e)
                print >> stdout, message
                continue                
                
            if not hasattr(settings, "GITHUB_ACCOUNT"):
               sleep(5)
            print >> stdout, "%s. Successfully updated package '%s'" % (index+1,package.title)

        print >> stdout, "-" * 40
        print >> stdout, "Finished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
