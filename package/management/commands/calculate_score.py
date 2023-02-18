import logging

from django.core.management.base import BaseCommand

from package.models import Package

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calculates the new star score for all Package objects."

    def handle(self, *args, **options):
        count = 0
        # Business logic is in calculate_score(), which is called by save()
        for package in Package.objects.filter().iterator():
            package.save()
            count += 1
            msg = f"{count}. {package}"
            logger.info(msg)
        print(f"{count} packages were updated...")
