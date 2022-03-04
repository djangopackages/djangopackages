import djclick as click
import logging

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rich import print

from core.utils import healthcheck
from package.models import Package

logger = logging.getLogger(__name__)


@click.command()
@click.option("--all", default=False)
def command(all):
    """Updates all the packages in the system by checking against their PyPI data."""
    count = 0
    count_updated = 0

    now = timezone.now()
    if not all:
        now = now - timezone.timedelta(hours=24)

    packages = (
        Package.objects.exclude(Q(pypi_url="") | Q(pypi_url__isnull=True))
        .filter(Q(last_fetched__lt=now) | Q(last_fetched__isnull=True))
        .order_by("last_fetched")
    )
    print(f"{packages.count()} to update")
    for package in packages.iterator():
        print(f"{package} | {package.last_fetched} | {package.pypi_url}")
        try:
            if package.fetch_pypi_data():
                count_updated += 1
                package.last_fetched = timezone.now()
                package.save()
        except Exception as e:
            print(f"[red]{package} :: {e}[/red]")
        count += 1
        msg = f"{count}. {count_updated}. {package}"
        logger.info(msg)

    healthcheck(settings.PYPI_HEALTHCHECK_URL)
