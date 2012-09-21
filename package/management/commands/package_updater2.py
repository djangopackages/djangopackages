"""
TODO - get it working with Celery
"""


import logging
from time import sleep

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.mail import send_mail

from package.models import Package

logger = logging.getLogger(__name__)

DEBUG = True


class PackageUpdaterException(Exception):
    def __init__(self, error, title):
        log_message = "For {title}, {error_type}: {error}".format(
            title=title,
            error_type=type(error),
            error=error
        )
        logging.error(log_message)
        logging.exception(error)


class Command(NoArgsCommand):

    help = "Updates all the packages in the system. Commands belongs to django-packages.package"

    def handle(self, *args, **options):

        for index, package in enumerate(Package.objects.iterator()):
            if index > 100:
                break
            print index, package
            try:
                try:
                    package.fetch_metadata()
                    package.fetch_commits()
                except Exception, e:
                    raise PackageUpdaterException(e, package.title)
            except PackageUpdaterException:
                continue

            #if not hasattr(settings, "GITHUB_API_SECRET"):
            #    sleep(5)

        message = "TODO - load logfile here"  # TODO - make this
        send_mail(
            subject="Package Updating complete",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["pydanny@gmail.com", "pydanny@cartwheelweb.com", ],
        )
