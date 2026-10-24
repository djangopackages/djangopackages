from __future__ import annotations

import djclick as click
from rich import print as rprint

from package import deps_dev
from package.models import Package


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Only these package slug(s)")
@click.option("--limit", default=None, type=int, help="Stop after this many packages")
@click.option(
    "--delay", default=0.5, type=float, help="Seconds between packages (default 0.5)"
)
@click.option("--dry-run", is_flag=True, help="Ask deps.dev, save nothing")
@click.option("-v", "--verbose", is_flag=True, help="One line per package")
def command(slugs, limit, delay, dry_run, verbose):
    """Record how many PyPI projects depend on each package, from deps.dev.

    Two requests per package, so a full pass is about an hour at the
    default delay. Meant to run weekly; `init_scheduled_jobs` has the job.
    """
    packages = Package.objects.exclude(pypi_url="").order_by("-score", "title")
    if slugs:
        packages = packages.filter(slug__in=slugs)
    if limit:
        packages = packages[:limit]

    outcome = deps_dev.sync(
        packages.iterator(),
        delay=delay,
        save=not dry_run,
        log=rprint if verbose else None,
    )
    verb = "would update" if dry_run else "updated"
    rprint(
        f"asked about {outcome.asked:,}: {outcome.found:,} on deps.dev, "
        f"{outcome.missing:,} unknown there, {outcome.no_answer:,} no answer; "
        f"{verb} {outcome.found + outcome.missing:,}"
    )
