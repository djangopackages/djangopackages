import logging
import logging.config

from django.core.management.base import NoArgsCommand
from django.utils import timezone


from package.models import Package

logger = logging.getLogger(__name__)


class Command(NoArgsCommand):

    help = "Updates all the packages in the system by checking against their PyPI data."

    def handle(self, *args, **options):

        count = 0
        count_updated = 0
        then = timezone.now() - timezone.timedelta(days=1)
        for package in Package.objects.filter(last_fetch__lt=then).iterator():
            print package
            print package.last_fetched
            break
            updated = package.fetch_pypi_data()
            if updated:
                count_updated += 1
                package.last_fetched = timezone.now()
                package.save()
            count += 1
            # msg = "{}. {}. {}".format(count, count_updated, package)
            # logger.info(msg)

