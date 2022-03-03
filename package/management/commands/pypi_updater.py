import djclick as click
import logging

from django.conf import settings
from django.utils import timezone
from rich import print

from core.utils import healthcheck
from package.models import Package

logger = logging.getLogger(__name__)


@click.command()
def command():
    """Updates all the packages in the system by checking against their PyPI data."""
    count = 0
    count_updated = 0
    for package in Package.objects.all().order_by("last_fetched").iterator():
        updated = package.fetch_pypi_data()
        if updated:
            count_updated += 1
            try:
                package.last_fetched = timezone.now()
                package.save()
            except Exception as e:
                print(f"[bold red]{e}[/bold red]")
        count += 1
        msg = f"{count}. {count_updated}. {package}"
        logger.info(msg)

    healthcheck(settings.PYPI_HEALTHCHECK_URL)
