import logging
from time import sleep

import djclick as click
from django.conf import settings
from django.db.models import F
from django.utils import timezone
from github3 import login as github_login
from github3.exceptions import NotFoundError, UnexpectedResponse
from rich import print

from core.utils import healthcheck
from package.models import Package

logger = logging.getLogger(__name__)


class PackageUpdaterException(Exception):
    def __init__(self, error, title):
        log_message = f"For {title}, {type(error)}: {error}"
        logging.critical(log_message)
        logging.exception(error)


@click.command()
@click.option("--limit", default=None, type=int)
def command(limit):
    """Updates all the GitHub Packages in the database."""

    github = github_login(token=settings.GITHUB_TOKEN)

    packages = Package.objects.filter(
        date_deprecated__isnull=True, last_exception_count__lte=5
    ).order_by("last_fetched")
    if limit:
        packages = packages[:limit]

    for package in packages.iterator():
        # Simple attempt to deal with GitHub rate limiting
        while True:
            if github.ratelimit_remaining < 50:
                print(f"github.ratelimit_remaining=={github.ratelimit_remaining}")
                logger.debug(f"{__file__}::handle::sleep(120)")
                sleep(120)
            break

        try:
            try:
                package.fetch_metadata(fetch_pypi=False, fetch_repo=True)
                package.fetch_commits()
                package.save()

            except NotFoundError as e:
                logger.error(f"Package was not found for {package.title}.")

                Package.objects.filter(pk=package.pk).update(
                    date_deprecated=timezone.now(),
                    last_exception=e,
                    last_exception_at=timezone.now(),
                    last_exception_count=F("last_exception_count") + 1,
                )

            except UnexpectedResponse as e:
                logger.error(f"Empty repo found for {package.title}.")

                Package.objects.filter(pk=package.pk).update(
                    date_deprecated=timezone.now(),
                    last_exception=e,
                    last_exception_at=timezone.now(),
                    last_exception_count=F("last_exception_count") + 1,
                )

            except Exception as e:
                logger.error(
                    f"Error while fetching package details for {package.title}."
                )
                raise PackageUpdaterException(e, package.title)

        except PackageUpdaterException as e:
            logger.error(f"Unable to update {package.title}", exc_info=True)
            Package.objects.filter(pk=package.pk).update(
                last_exception=e,
                last_exception_at=timezone.now(),
                last_exception_count=F("last_exception_count") + 1,
            )

        logger.debug(f"{__file__}::handle::sleep(1)")
        sleep(1)

    healthcheck(settings.PACKAGE_HEALTHCHECK_URL)
