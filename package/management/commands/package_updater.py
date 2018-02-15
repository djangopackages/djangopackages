import logging
import logging.config
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

from github3 import login as github_login

from package.models import Package
from core.utils import healthcheck

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


class Command(BaseCommand):

    help = "Updates all the packages in the system. Commands belongs to django-packages.package"

    def handle(self, *args, **options):

        github = github_login(token=settings.GITHUB_TOKEN)

        for index, package in enumerate(Package.objects.iterator()):

            # Simple attempt to deal with Github rate limiting
            while True:
                if github.ratelimit_remaining < 50:
                    sleep(120)
                break

            try:
                try:
                    package.fetch_metadata(fetch_pypi=False)
                    package.fetch_commits()
                except Exception as e:
                    raise PackageUpdaterException(e, package.title)
            except PackageUpdaterException:
                logger.error(f"Unable to update {package.title}", exc_info=True)

            sleep(5)
        healthcheck(settings.PACKAGE_HEALTHCHECK_URL)
