"""
TODO - get it working with Celery
"""


import logging
import logging.config
from time import sleep

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.mail import send_mail

from package.models import Package

logger = logging.getLogger(__name__)


class PackageUpdaterException(Exception):
    def __init__(self, error, title):
        log_message = "For {title}, {error_type}: {error}".format(
            title=title,
            error_type=type(error),
            error=error
        )
        logging.critical(log_message)
        logging.exception(error)


class Command(NoArgsCommand):

    help = "Updates all the packages in the system. Commands belongs to django-packages.package"

    def handle(self, *args, **options):

        for index, package in enumerate(Package.objects.iterator()):
            #if index not in (89, 90, 91, 92):
            #    continue
            #print index
            try:
                try:
                    package.fetch_metadata()
                    package.fetch_commits()
                except Exception, e:
                    raise PackageUpdaterException(e, package.title)
            except PackageUpdaterException:
                pass  # We've already caught the error so let's move on now

            #if not hasattr(settings, "GITHUB_API_SECRET"):
            sleep(5)

        message = "TODO - load logfile here"  # TODO
        send_mail(
            subject="Package Updating complete",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[x[1] for x in settings.ADMINS]
        )
