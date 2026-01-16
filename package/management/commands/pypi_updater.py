import logging
import time

import djclick as click
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rich import print

from core.utils import healthcheck
from package.models import Package
from package.management.commands._rate_limiter import RateLimiter
from package.pypi import PyPIClient, PyPIRateLimitError, update_package_from_pypi

logger = logging.getLogger(__name__)


@click.command()
@click.option("--all", is_flag=True, default=False, help="Ignore staleness filter")
@click.option("--pypi_url", type=str, default=None, help="Update a single PyPI slug")
@click.option("--limit", default=None, type=int, help="Max packages to process")
@click.option("--chunk-size", default=200, type=int, help="Batch size for DB writes")
@click.option(
    "--stale-hours", default=24, type=int, help="Only update packages older than this"
)
@click.option(
    "--min-interval", default=0.2, type=float, help="Minimum seconds between requests"
)
@click.option(
    "--max-per-minute", default=240, type=int, help="Hard cap for requests per minute"
)
@click.option(
    "--jitter", default=0.05, type=float, help="Random delay to avoid burst alignment"
)
@click.option(
    "--time-budget", default=None, type=int, help="Stop after this many seconds"
)
@click.option("--timeout", default=10.0, type=float, help="HTTP timeout in seconds")
def command(
    all,
    pypi_url,
    limit,
    chunk_size,
    stale_hours,
    min_interval,
    max_per_minute,
    jitter,
    time_budget,
    timeout,
):
    """Updates all the packages in the system by checking against their PyPI data."""
    count = 0
    count_updated = 0

    now = timezone.now()
    if not all:
        now = now - timezone.timedelta(hours=stale_hours)

    if chunk_size <= 0:
        raise click.ClickException("--chunk-size must be > 0")

    if stale_hours < 0:
        raise click.ClickException("--stale-hours must be >= 0")

    if pypi_url:
        packages = Package.objects.filter(pypi_url=pypi_url)
    else:
        packages = (
            Package.objects.active()
            .exclude(pypi_url="")
            .filter(Q(last_fetched__lt=now) | Q(last_fetched__isnull=True))
            .only(
                "pk",
                "pypi_url",
                "pypi_classifiers",
                "pypi_requires_python",
                "supports_python3",
                "documentation_url",
                "pypi_license",
                "pypi_licenses",
                "latest_version",
                "last_fetched",
            )
            .order_by("last_fetched", "pk")
        )

    if limit:
        packages = packages[:limit]

    total = packages.count()
    print(f"{total} to update")

    rate_limiter = RateLimiter(
        min_interval=min_interval,
        max_per_minute=max_per_minute if max_per_minute > 0 else None,
        jitter=jitter,
        stop_on_limit=True,
    )
    client = PyPIClient(
        user_agent="djangopackages/pypi-updater",
        timeout=timeout,
    )

    started = time.monotonic()
    packages_to_update = []
    update_fields = [
        "pypi_classifiers",
        "pypi_requires_python",
        "supports_python3",
        "documentation_url",
        "pypi_license",
        "pypi_licenses",
        "latest_version",
        "last_fetched",
    ]

    def flush_updates() -> None:
        nonlocal packages_to_update
        if not packages_to_update:
            return
        # Bulk write avoids per-row saves and reduces DB round-trips.
        Package.objects.bulk_update(packages_to_update, fields=update_fields)
        print(f"[green]Flushed {len(packages_to_update)} package(s) to DB.[/green]")
        packages_to_update = []

    for package in packages.iterator(chunk_size=chunk_size):
        if time_budget is not None:
            elapsed = time.monotonic() - started
            if elapsed >= time_budget:
                print("[yellow]Time budget reached; stopping early.[/yellow]")
                break

        print(f"[blue]Processing {package.pk} :: {package} | {package.pypi_url}[/blue]")
        try:
            try:
                rate_limiter.wait()
            except RuntimeError:
                print("[yellow]Rate limit reached; stopping early.[/yellow]")
                break
            if update_package_from_pypi(package, client=client, save=False):
                count_updated += 1
                package.last_fetched = timezone.now()
                packages_to_update.append(package)
                print(
                    f"[green]Updated {package.pk} :: {package} | version={package.latest_version}[/green]"
                )
                if len(packages_to_update) >= chunk_size:
                    flush_updates()
        except PyPIRateLimitError:
            print("[yellow]PyPI rate limit reached; stopping early.[/yellow]")
            break
        except Exception as e:
            print(f"[red]{package} :: {e}[/red]")
        count += 1
        msg = f"{count}. {count_updated}. {package}"
        logger.info(msg)

    flush_updates()
    healthcheck(settings.PYPI_HEALTHCHECK_URL)
