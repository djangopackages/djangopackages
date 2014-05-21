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
            package.repo.fetch_metadata(package, fetch_pypi=False)
            if package.last_fetched > yesterday:
                continue
            package.repo.fetch_commits(package)
            # if package.repo.title == "Github":
            #     msg = "{}. {}. {}".format(count, package.repo.github.ratelimit_remaining, package)
            # else:
            #     msg = "{}. {}".format(count, package)
            # logger.info(msg)
