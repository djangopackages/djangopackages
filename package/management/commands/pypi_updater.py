import djclick as click
import logging

from django.conf import settings

from package.models import Package
from core.utils import healthcheck

logger = logging.getLogger(__name__)


@click.command()
def command():
    """Updates all the packages in the system by checking against their PyPI data."""
    count_updated = 0
    for count, package in enumerate(Package.objects.filter().iterator()):
        if updated := package.fetch_pypi_data():
            count_updated += 1
            package.save()
        msg = f"{count}. {count_updated}. {package}"
        logger.info(msg)
    healthcheck(settings.PYPI_HEALTHCHECK_URL)
