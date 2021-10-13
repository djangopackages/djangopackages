import logging

from django.core.management.base import BaseCommand

from package.models import Package

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Updates the score for all packages"

    def handle(self, *args, **options):
        count = 0
        for package in Package.objects.filter().iterator():
            package.save()
            count += 1
            msg = f"{count}. {package}"
            logger.info(msg)
        print(f"{count} packages were updated...")
