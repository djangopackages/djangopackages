from time import sleep
import logging
import logging.config

from django.core.management.base import NoArgsCommand
from django.utils import timezone

from package.models import Package

logger = logging.getLogger(__name__)


class Command(NoArgsCommand):

    help = "Updates all the packages in the system focusing on repo data"

    def handle(self, *args, **options):

        yesterday = timezone.now() - timezone.timedelta(1)
        for package in Package.objects.filter().iterator():
            # keep this here because for now we only have one last_fetched field.
            package = package.repo.fetch_metadata(package)
            if package is None:
                continue
            if package.last_fetched is not None and package.last_fetched > yesterday:
                print package, "skipped"
                continue
            package.repo.fetch_commits(package)
            package.last_fetched = timezone.now()
            package.save()
            print package, "updated"
            sleep(1)
            # if package.repo.title == "Github":
            #     msg = "{}. {}. {}".format(count, package.repo.github.ratelimit_remaining, package)
            # else:
            #     msg = "{}. {}".format(count, package)
            # logger.info(msg)
