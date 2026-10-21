from __future__ import annotations

import djclick as click
from rich import print as rprint

from package.models import Package
from probes.checkouts import checkout_path, scannable_packages
from probes.imports import canonical_name, detect_import_names, normalize
from probes.models import Library


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to look at")
@click.option("--min-score", default=0, type=int, help="Lowest score to include")
@click.option(
    "--differences-only",
    is_flag=True,
    help="Only print the ones a guess would have got wrong",
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
    importable directories out of the source we already cloned. Where
    there is no checkout it falls back to the usual guess of swapping
    hyphens for underscores, and says so in `source`, because a guess
    that cannot be told from a fact is worse than no answer.
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

    read = guessed = differs = 0

    for package in queryset:
        pypi_name = canonical_name(package.pypi_name or package.slug)
        names = detect_import_names(checkout_path(package), pypi_name=pypi_name)

        if names:
            source = Library.Source.CHECKOUT
            read += 1
        else:
            names = [normalize(pypi_name)]
            source = Library.Source.GUESS
            guessed += 1

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
        f"\nread from a checkout {read:,}  guessed {guessed:,}  "
        f"where a guess would be wrong {differs:,}"
        + ("  [dim](dry run, nothing written)[/dim]" if dry_run else "")
    )
