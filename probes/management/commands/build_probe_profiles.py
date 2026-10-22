from __future__ import annotations

import djclick as click
from django.utils.timezone import now
from rich import print as rprint

from package.models import Package
from probes import stats as probe_stats
from probes.checkouts import scannable_packages
from probes.models import PackageProbe
from probes.version_support import declared_dependencies, version_support


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to process")
@click.option(
    "--min-score",
    default=0,
    type=int,
    help=(
        "Lowest package score to include. Below zero means roughly thirty "
        "months without a commit; pass -500 to reach those too (default: 0)"
    ),
)
@click.option("--dry-run", is_flag=True, help="Report without writing")
def command(slugs: tuple[str, ...], limit: int | None, min_score: int, dry_run: bool):
    """Fill in probe profiles from the PyPI metadata we already hold.

    Reads nothing from the network and clones nothing: everything here
    comes out of pypi_classifiers, pypi_requires_python and pypi_info,
    which the PyPI import already keeps current. The AST half of the
    profile is filled in separately by scan_package_repos, which does
    need a checkout.
    """
    queryset = (
        Package.objects.filter(slug__in=slugs)
        if slugs
        else scannable_packages(min_score=min_score)
    )
    # version_support reads the latest release's upload date, which would
    # otherwise be a query per package.
    queryset = queryset.select_related("latest_version")
    if limit:
        queryset = queryset[:limit]

    profiles = deps_written = with_python = with_django = 0

    for package in queryset.iterator(chunk_size=200):
        support = version_support(package)
        dependencies = declared_dependencies(package)

        if support.python:
            with_python += 1
        if support.django:
            with_django += 1
        profiles += 1
        deps_written += len(dependencies)

        if dry_run:
            continue

        # Replaced wholesale rather than merged: a dependency dropped
        # upstream should disappear here too.
        PackageProbe.objects.update_or_create(
            package=package,
            defaults={
                "python_versions": list(support.python),
                "django_versions": list(support.django),
                "python_source": support.python_source,
                "django_source": support.django_source,
                "dependencies": [
                    {
                        "name": dependency.name,
                        "specifier": dependency.specifier,
                        "extra": dependency.extra,
                        "marker": dependency.marker,
                    }
                    for dependency in dependencies
                ],
                "metadata_updated_at": now(),
            },
        )

    if not dry_run:
        probe_stats.invalidate()

    suffix = "  [dim](dry run)[/dim]" if dry_run else ""
    rprint(
        f"profiles {profiles:,}  dependencies {deps_written:,}  "
        f"python {with_python:,}  django {with_django:,}{suffix}"
    )
