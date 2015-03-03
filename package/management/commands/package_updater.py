import logging
import logging.config
from time import sleep

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.mail import send_mail

from github3 import login as github_login

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

        github = github_login(token=settings.GITHUB_TOKEN)

        for index, package in enumerate(Package.objects.iterator()):

            # Simple attempt to deal with Github rate limiting
            while True:
                if github.ratelimit_remaining() < 50:
                    sleep(120)
                break

            try:
                try:
                    package.fetch_metadata(fetch_metadata=False)
                    package.fetch_commits()
                except Exception as e:
                    raise PackageUpdaterException(e, package.title)
            except PackageUpdaterException:
                pass  # We've already caught the error so let's move on now

            sleep(5)

        message = "TODO - load logfile here"  # TODO
        send_mail(
            subject="Package Updating complete",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[x[1] for x in settings.ADMINS]
        )
