from __future__ import annotations

from collections import Counter

import djclick as click
from rich import print as rprint

from package import licenses
from package.models import Package
from package.pypi import PyPIPackage


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--dry-run", is_flag=True, help="Report without writing")
def command(slugs: tuple[str, ...], dry_run: bool):
    """Recompute every package's license from the metadata already stored.

    No network. Uses the PyPI JSON kept in `pypi_info` where we have it,
    else the stored classifiers, else the current value run through the
    normaliser. The repository host's license is filled in by the
    regular updater as it revisits each package.
    """
    queryset = Package.objects.select_related("latest_version").order_by("slug")
    if slugs:
        queryset = queryset.filter(slug__in=slugs)

    changed = 0
    before: Counter[str] = Counter()
    after: Counter[str] = Counter()

    for package in queryset.iterator(chunk_size=500):
        old = package.pypi_license
        before[old or licenses.UNKNOWN] += 1

        if package.pypi_info:
            found = PyPIPackage({"info": package.pypi_info}).license_list
        else:
            found = licenses.from_pypi(
                license_expression=None,
                classifiers=package.pypi_classifiers or [],
                legacy=old,
            )

        new = found[0] if found else None
        after[new or package.repo_license or licenses.UNKNOWN] += 1

        if new == old and (found or None) == package.pypi_licenses:
            continue
        changed += 1
        if dry_run:
            rprint(f"  {package.slug}: {old!r} -> {new!r}")
            continue

        package.pypi_license = new
        package.pypi_licenses = found or None
        package.save(update_fields=["pypi_license", "pypi_licenses"])
        if (version := package.latest_version) and version.license != new:
            version.license = new
            version.licenses = found or None
            version.save(update_fields=["license", "licenses"])

    rprint(
        f"\nchanged {changed:,} of {sum(before.values()):,}"
        + ("  [dim](dry run, nothing written)[/dim]" if dry_run else "")
    )
    rprint("\n[bold]Most common, before -> after[/bold]")
    for name, count in after.most_common(15):
        rprint(f"  {before.get(name, 0):>6,} -> {count:>6,}  {name}")
