# python -m smtpd -n -c DebuggingServer localhost:1025
# 538

from sys import stdout
from socket import error as socket_error
from time import sleep, gmtime, strftime
from xml.parsers.expat import ExpatError
from xmlrpclib import ProtocolError

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.mail import send_mail

from package.models import Package

DEBUG = True


class Command(NoArgsCommand):

    help = "Updates all the packages in the system. Commands belongs to django-packages.package"

    def handle(self, *args, **options):

        text = "Commencing package updating now at %s " % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        
        for index, package in enumerate(Package.objects.all()):
            #if index < 1154:
            #    continue
            print 'hi'
            try:
                try:
                    package.fetch_metadata()
                    package.fetch_commits()
                except socket_error, e:
                    text += "\nFor '%s', threw a socket_error: %s" % (package.title, e)
                    continue
                except ValueError, e:
                    text += "\nFor '%s', threw a ValueError: %s" % (package.title, e)
                    continue
                
            except RuntimeError, e:
                text += "\nFor '%s', too many requests issued to repo threw a RuntimeError: %s" % (package.title, e)
                continue
            except UnicodeDecodeError, e:
                text += "\nFor '%s', UnicodeDecodeError: %s" % (package.title, e)
                continue
            except ProtocolError, e:
                text += "\nFor '%s', xmlrpc.ProtocolError: %s" % (package.title, e)
                continue
            except ExpatError, e:
                text += "\nFor '%s', ExpatError: %s" % (package.title, e)
                continue
            except Exception, e:
                text += "\nFor '%s', General Exception: %s" % (package.title, e)
                continue

            if not hasattr(settings, "GITHUB_API_SECRET"):
                sleep(5)
            text += "\n%s. Successfully updated package '%s'" % (index + 1, package.title)
            
            if DEBUG:
                try:
                    print(text.splitlines()[index-1154])
                except UnicodeDecodeError, e:
                    print('Stupid UnicodeDecodeError error on {0}'.format(package.pk))
                except UnicodeEncodeError, e:
                    print('Stupid UnicodeEncodeError error on {0}'.format(package.pk))
                    print text
                

        #print >> stdout, "-" * 40
        text += "\n"
        text += "-" * 40
        #print >> stdout, "Finished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        text += "\nFinished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

        send_mail(
            subject="Package Updating complete",
            message=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["pydanny@gmail.com", "pydanny@cartwheelweb.com", ],
        )

