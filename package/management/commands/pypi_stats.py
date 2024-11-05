import logging
import time

import djclick as click
import json
import pypistats

from rich import print
from rich.progress import track

from package.models import Package

logger = logging.getLogger(__name__)


@click.command()
@click.option("--slug", type=str, default=None)
@click.option(
    "--delay", type=float, default=2.0, help="Delay between API calls in seconds"
)
def command(slug, delay):
    if slug:
        packages = Package.objects.filter(slug=slug)
    else:
        packages = Package.objects.active().exclude(pypi_url="")

    total_packages = packages.count()

    for package in track(
        sequence=packages.iterator(),
        total=total_packages,
        description="Fetching PyPI stats...",
    ):
        try:
            pypi_slug = package.pypi_url.strip("/").split("/")[-1]
            response = pypistats.recent(pypi_slug, "month", format="json")
            response = json.loads(response)
            pypi_downloads = response["data"]["last_month"]
            msg = f"{pypi_slug}, {pypi_downloads=}"
            logger.info(msg)

            package.pypi_downloads = pypi_downloads
            package.save(update_fields=["pypi_downloads"])

        except Exception as e:
            print(f"{e=}")

        # Delay between API calls to avoid rate limiting
        logger.debug(f"Delaying for {delay} seconds...")
        time.sleep(delay)
