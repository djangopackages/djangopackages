"""Find Django, Wagtail or Django CMS packages on PyPI we do not index yet.

    manage.py pypi_discover --framework wagtail --days 7
    manage.py pypi_discover --framework django --all --csv
    manage.py pypi_discover --framework django-cms --days 30 --estimate

Reads `bigquery-public-data.pypi.distribution_metadata` through the
service account in `GOOGLE_BIGQUERY_CREDENTIALS`. Prints a review list;
creates nothing. `--csv` saves the full list under MEDIA_ROOT so it can
be pulled from the site afterwards. See #1810.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import djclick as click
from django.conf import settings
from rich.console import Console
from rich.table import Table

from package.models import Package
from probes import discovery

CSV_DIR = "pypi-discover"
CSV_COLUMNS = [
    "status",
    "name",
    "pypi_url",
    "package_slug",
    "version",
    "first_upload",
    "last_upload",
    "home_page",
    "summary",
]


def csv_destination(framework: str, window: int | None) -> Path:
    """`MEDIA_ROOT/pypi-discover/<framework>-<7d|all>-<today>.csv`.

    Media is served at `MEDIA_URL`, so the file can be pulled from the
    site once written; running twice in a day overwrites the same file.
    """
    span = "all" if window is None else f"{window}d"
    return (
        Path(settings.MEDIA_ROOT) / CSV_DIR / f"{framework}-{span}-{date.today()}.csv"
    )


def write_csv(path: Path, found: discovery.Discovery) -> int:
    """Every row, new ones first, with a status column telling them apart."""
    slugs = Package.objects.in_bulk([pk for _, pk in found.tracked])
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [(row, "new", "") for row in found.new] + [
        (row, "indexed", getattr(slugs.get(pk), "slug", ""))
        for row, pk in found.tracked
    ]
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for row, status, slug in rows:
            writer.writerow(
                [
                    status,
                    row.name,
                    row.pypi_url,
                    slug,
                    row.version,
                    row.first_upload.isoformat(),
                    row.last_upload.isoformat(),
                    row.home_page,
                    row.summary,
                ]
            )
    return len(rows)


@click.command()
@click.option(
    "--framework",
    type=click.Choice(sorted(discovery.FRAMEWORKS)),
    required=True,
    help="Which classifier family to search.",
)
@click.option(
    "--days",
    type=int,
    default=7,
    show_default=True,
    help="Only projects with an upload in the last N days.",
)
@click.option(
    "--all",
    "whole_index",
    is_flag=True,
    help="No date filter: every project ever tagged. For a one-time backfill.",
)
@click.option(
    "--estimate",
    is_flag=True,
    help="Dry run the query and print the bytes it would scan, then stop.",
)
@click.option(
    "--show-tracked",
    is_flag=True,
    help="Also list the matches we already index.",
)
@click.option(
    "--csv",
    "save_csv",
    is_flag=True,
    help="Also save the whole list as a CSV under MEDIA_ROOT/pypi-discover/.",
)
def command(framework, days, whole_index, estimate, show_tracked, save_csv):
    """Search PyPI by trove classifier and list the packages we do not have."""
    console = Console()
    window = None if whole_index else days
    scope = "the whole index" if window is None else f"the last {window} days"

    if estimate:
        scanned = discovery.estimate(framework, window)
        console.print(
            f"{discovery.FRAMEWORKS[framework]} over {scope}: "
            f"[bold]{scanned / 1024**3:,.2f} GB[/bold] would be scanned"
        )
        return

    found = discovery.discover(framework, window)
    console.print(
        f"[bold]{discovery.FRAMEWORKS[framework]}[/bold] over {scope}: "
        f"{len(found.tracked):,} already indexed, "
        f"[green]{len(found.new):,} new to us[/green] "
        f"({found.bytes_processed / 1024**3:,.2f} GB scanned)"
    )

    if found.new:
        table = Table(title="New to us", title_justify="left")
        table.add_column("package")
        table.add_column("version")
        table.add_column("first upload")
        table.add_column("last upload")
        table.add_column("summary")
        for row in found.new:
            table.add_row(
                f"[link={row.pypi_url}]{row.name}[/link]",
                row.version,
                row.first_upload.date().isoformat(),
                row.last_upload.date().isoformat(),
                row.summary[:70],
            )
        console.print(table)

    if show_tracked and found.tracked:
        table = Table(title="Already indexed", title_justify="left")
        table.add_column("package")
        table.add_column("last upload")
        table.add_column("package pk", justify="right")
        for row, pk in found.tracked:
            table.add_row(row.name, row.last_upload.date().isoformat(), str(pk))
        console.print(table)

    if save_csv:
        path = csv_destination(framework, window)
        written = write_csv(path, found)
        url = f"{settings.MEDIA_URL}{CSV_DIR}/{path.name}"
        console.print(f"Wrote {written:,} rows to {path}")
        console.print(f"Pull it from {url}")
