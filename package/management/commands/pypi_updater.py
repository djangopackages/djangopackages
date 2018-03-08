import logging
import logging.config

from django.core.management.base import BaseCommand
from django.conf import settings

from package.models import Package
from core.utils import healthcheck

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Updates all the packages in the system by checking against their PyPI data."

    def handle(self, *args, **options):

        count = 0
        count_updated = 0
        for package in Package.objects.filter().iterator():

            updated = package.fetch_pypi_data()
            if updated:
                count_updated += 1
                package.save()
            count += 1
            # msg = "{}. {}. {}".format(count, count_updated, package)
            # logger.info(msg)
        healthcheck(settings.PYPI_HEALTHCHECK_URL)
