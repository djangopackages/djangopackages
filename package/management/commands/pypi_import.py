"""Create packages from PyPI names and fill them in.

    manage.py pypi_import django-nanopages wagtail-pagetree
    manage.py pypi_import --csv /data/media/pypi-discover/wagtail-7d-2026-10-29.csv
    manage.py pypi_import --csv new.csv --category apps --dry-run
    manage.py pypi_import --csv new.csv --queue

Names come from the arguments or from the `name` column of a
`pypi_discover --csv` file, where only rows with `status` of `new` are
taken. Each becomes a Package with its PyPI and repository metadata
fetched and its score set, tagged `pypi-import`. `--queue` hands each
name to the Django Q cluster as `import_from_pypi_task` instead of
running inline. See #1810.

Review the list first. Nothing filters spam or malware out of what
PyPI returns, which is why there is no scheduled job for this.
"""

from __future__ import annotations

import csv
from pathlib import Path

import djclick as click
from django_q.tasks import async_task
from rich.console import Console
from rich.table import Table

from package.importer import import_from_pypi
from package.models import Category
from package.pypi import PyPIClient
from probes.awesome import package_index


def names_from_csv(path: Path) -> list[str]:
    """The `new` rows of a discovery CSV, or every row of a plain one-column file."""
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames and "name" in reader.fieldnames:
            return [
                row["name"]
                for row in reader
                if row.get("name") and row.get("status", "new") == "new"
            ]
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


@click.command()
@click.argument("names", nargs=-1)
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="A pypi_discover CSV; its `new` rows are imported.",
)
@click.option(
    "--category",
    "category_slug",
    default="apps",
    show_default=True,
    help="Category slug for the new packages.",
)
@click.option(
    "--dry-run", is_flag=True, help="Fetch from PyPI and report; create nothing."
)
@click.option(
    "--queue",
    is_flag=True,
    help="Queue one import_from_pypi_task per name instead of running here.",
)
def command(names, csv_path, category_slug, dry_run, queue):
    """Create packages from PyPI names, filling in PyPI and repository data."""
    console = Console()
    names = list(names) + (names_from_csv(csv_path) if csv_path else [])
    if not names:
        raise click.UsageError("Give PyPI names, or --csv with a discovery file.")
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        known = ", ".join(Category.objects.values_list("slug", flat=True))
        raise click.BadParameter(f"no category {category_slug!r}; one of {known}")

    if queue:
        for name in names:
            async_task("package.tasks.import_from_pypi_task", name, category.slug)
        console.print(
            f"Queued {len(names):,} import task(s) in category {category.slug}."
        )
        return

    index = package_index()
    client = PyPIClient()
    results = [
        import_from_pypi(
            name, category=category, client=client, dry_run=dry_run, index=index
        )
        for name in names
    ]

    table = Table(title="dry run" if dry_run else "imported", title_justify="left")
    table.add_column("name")
    table.add_column("status")
    table.add_column("package / note")
    for result in results:
        where = result.package.get_absolute_url() if result.package else ""
        table.add_row(
            result.name,
            {
                "created": "[green]created[/green]",
                "dry_run": "[cyan]would create[/cyan]",
                "exists": "[dim]exists[/dim]",
                "no_repo": "[yellow]no repo[/yellow]",
                "not_on_pypi": "[red]not on PyPI[/red]",
                "error": "[red]error[/red]",
            }[result.status],
            " ".join(part for part in (where, result.note) if part),
        )
    console.print(table)
    created = sum(1 for r in results if r.created)
    console.print(
        f"{len(results):,} name(s): {created:,} created, "
        f"{sum(1 for r in results if r.status == 'exists'):,} already here, "
        f"{sum(1 for r in results if r.status == 'no_repo'):,} without a repository, "
        f"{sum(1 for r in results if r.status in ('not_on_pypi', 'error')):,} failed."
    )
