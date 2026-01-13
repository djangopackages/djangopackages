import logging

import djclick as click
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rich import print

from core.utils import healthcheck
from package.models import Package

logger = logging.getLogger(__name__)


@click.command()
@click.option("--all", is_flag=True, default=False)
@click.option("--pypi_url", type=str, default=None)
def command(all, pypi_url):
    """Updates all the packages in the system by checking against their PyPI data."""
    count = 0
    count_updated = 0

    now = timezone.now()
    if not all:
        now = now - timezone.timedelta(hours=24)

    if pypi_url:
        packages = Package.objects.filter(pypi_url=pypi_url)
    else:
        packages = (
            Package.objects.exclude(
                Q(pypi_url="")
                | Q(pypi_url__isnull=True)
                | Q(date_deprecated__lt=now)
                | Q(date_repo_archived__lt=now)
            )
            .filter(Q(last_fetched__lt=now) | Q(last_fetched__isnull=True))
            .order_by("-pypi_downloads", "last_fetched")
        )

    package_pks = list(packages.values_list("pk", flat=True))
    print(f"{len(package_pks)} to update")
    for pk in package_pks:
        package = Package.objects.get(pk=pk)
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
