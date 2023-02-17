import json
import logging
from pathlib import Path

import djclick as click
from django.urls import reverse
from rich.progress import Progress

from grid.models import Grid
from package.models import Package

logger = logging.getLogger(__name__)


def get_grids(*, domain: str, limit: int) -> list[dict]:
    links = []
    grids = Grid.objects.all().order_by("slug")

    if limit:
        grids = grids[0:limit]

    with Progress() as progress:
        task = progress.add_task(
            "[green]Generating Grids...[/green]", total=grids.count()
        )
        for grid in grids:
            progress.update(task, advance=1)
            path = reverse("grid_opengraph", kwargs={"slug": grid.slug})
            url = f"{domain}{path}"
            links.append({"slug": grid.slug, "url": url})

    return links


def get_packages(*, domain: str, limit: int) -> list[dict]:
    links = []
    packages = Package.objects.all().order_by("slug")

    if limit:
        packages = packages[0:limit]

    with Progress() as progress:
        task = progress.add_task(
            "[green]Generating Packages...[/green]", total=packages.count()
        )
        for package in packages:
            progress.update(task, advance=1)
            path = reverse("package_opengraph", kwargs={"slug": package.slug})
            url = f"{domain}{path}"
            links.append({"slug": package.slug, "url": url})
    return links


@click.command()
@click.argument("filename", type=Path, default=Path("opengraph-image-export.json"))
@click.option("--domain", type=str, default="https://djangopackages.org")
@click.option("--limit", default=None, type=int)
@click.option("--overwrite", default=False, is_flag=True)
def command(filename, domain, limit, overwrite):
    links = []
    links += get_grids(domain=domain, limit=limit)
    links += get_packages(domain=domain, limit=limit)

    filename.write_text(json.dumps(links, indent=2))
