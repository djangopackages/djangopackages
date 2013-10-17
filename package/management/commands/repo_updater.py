import logging
import logging.config

from django.core.management.base import NoArgsCommand
from django.utils import timezone

from package.models import Package

logger = logging.getLogger(__name__)


class Command(NoArgsCommand):

    help = "Updates all the packages in the system focusing on repo data"

    def handle(self, *args, **options):

        count = 0
        for package in Package.objects.filter().iterator():
            package.repo.fetch_metadata(package)
            package.repo.fetch_commits(package)
            print package.slug
            count += 1
            # if package.repo.title == "Github":
            #     msg = "{}. {}. {}".format(count, package.repo.github.ratelimit_remaining, package)
            # else:
            #     msg = "{}. {}".format(count, package)
            # logger.info(msg)
