from __future__ import annotations

import djclick as click
from rich import print as rprint

from package.models import Package
from probes.checkouts import checkout_path, scannable_packages
from probes.imports import canonical_name, detect_import_names
from probes.models import Library


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to look at")
@click.option("--min-score", default=0, type=int, help="Lowest score to include")
@click.option(
    "--differences-only",
    is_flag=True,
    help="Only print the ones whose import name differs",
)
@click.option("--dry-run", is_flag=True, help="Report without writing")
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    min_score: int,
    differences_only: bool,
    dry_run: bool,
):
    """Record what each package is imported as, read from its checkout.

    PyPI does not publish the import name, so this reads the top-level
    importable directories out of the source we already cloned. A
    package we have no checkout for gets no row. We used to fall back
    to swapping hyphens for underscores, which is wrong for about one
    package in five, and a row nobody can tell from a read one is
    worse than a missing row.
    """
    queryset = (
        Package.objects.order_by("-score", "title")
        if slugs
        else scannable_packages(min_score=min_score)
    )
    if slugs:
        queryset = queryset.filter(slug__in=slugs)
    if limit:
        queryset = queryset[:limit]

    read = skipped = differs = 0

    for package in queryset:
        pypi_name = canonical_name(package.pypi_name or package.slug)
        names = detect_import_names(checkout_path(package), pypi_name=pypi_name)

        if not names:
            skipped += 1
            continue

        source = Library.Source.CHECKOUT
        read += 1

        if not dry_run:
            library, _created = Library.objects.update_or_create(
                pypi_name=pypi_name,
                defaults={
                    "import_name": names[0],
                    "also_imports": names[1:],
                    "source": source,
                    "package": package,
                },
            )
        else:
            library = Library(
                pypi_name=pypi_name, import_name=names[0], also_imports=names[1:]
            )

        if library.names_differ:
            differs += 1
            rprint(
                f"  [bold]{pypi_name}[/bold] imports as "
                f"[green]{names[0]}[/green]"
                + (f" (+{', '.join(names[1:])})" if names[1:] else "")
                + f" [dim]{source}[/dim]"
            )
        elif not differences_only:
            rprint(f"  {pypi_name} [dim]{source}[/dim]")

    rprint(
        f"\nread from a checkout {read:,}  no checkout to read {skipped:,}  "
        f"where the names differ {differs:,}"
        + ("  [dim](dry run, nothing written)[/dim]" if dry_run else "")
    )
