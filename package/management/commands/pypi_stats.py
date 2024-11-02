import logging

import djclick as click
import json
import pypistats

from rich import print

from package.models import Package

logger = logging.getLogger(__name__)


@click.command()
@click.option("--slug", type=str, default=None)
def command(slug):
    if slug:
        packages = Package.objects.filter(slug=slug)
    else:
        packages = Package.objects.active().exclude(pypi_url="")

    for package in packages.iterator():
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
