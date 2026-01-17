import logging
import time

import djclick as click
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from github3 import login as github_login
from github3.exceptions import NotFoundError, UnexpectedResponse
from rich import print

from core.utils import healthcheck
from package.management.commands._rate_limiter import RateLimiter
from package.models import Package
from package.repos.base_handler import RepoRateLimitError

logger = logging.getLogger(__name__)


class PackageUpdaterException(Exception):
    def __init__(self, error, title):
        log_message = f"For {title}, {type(error)}: {error}"
        logging.critical(log_message)
        logging.exception(error)


@click.command()
@click.option("--limit", default=None, type=int, help="Max packages to process")
@click.option("--chunk-size", default=200, type=int, help="Batch size for DB writes")
@click.option("--all", is_flag=True, default=False, help="Ignore staleness filter")
@click.option(
    "--stale-hours", default=24, type=int, help="Only update packages older than this"
)
@click.option(
    "--min-interval", default=0.5, type=float, help="Minimum seconds between requests"
)
@click.option(
    "--max-per-minute", default=60, type=int, help="Hard cap for requests per minute"
)
@click.option(
    "--jitter", default=0.1, type=float, help="Random delay to avoid burst alignment"
)
@click.option(
    "--time-budget", default=None, type=int, help="Stop after this many seconds"
)
@click.option(
    "--rate-threshold",
    default=50,
    type=int,
    help="Stop when provider quota drops below this",
)
def command(
    limit,
    chunk_size,
    all,
    stale_hours,
    min_interval,
    max_per_minute,
    jitter,
    time_budget,
    rate_threshold,
):
    """Updates all the GitHub Packages in the database."""

    github = github_login(token=settings.GITHUB_TOKEN)

    if chunk_size <= 0:
        raise click.ClickException("--chunk-size must be > 0")

    if stale_hours < 0:
        raise click.ClickException("--stale-hours must be >= 0")

    now = timezone.now()
    cutoff = now - timezone.timedelta(hours=stale_hours)

    packages = (
        Package.objects.filter(
            date_deprecated__isnull=True,
            last_exception_count__lte=5,
        )
        .exclude(Q(repo_url="") | Q(repo_url__isnull=True))
        .only(
            "pk",
            "repo_url",
            "repo_host",
            "repo_description",
            "repo_forks",
            "repo_watchers",
            "participants",
            "date_repo_archived",
            "commits_over_52w",
            "last_commit_date",
            "last_fetched",
            "score",
            "last_exception_count",
        )
    )

    if not all:
        packages = packages.filter(
            Q(last_fetched__lt=cutoff) | Q(last_fetched__isnull=True)
        )

    packages = packages.order_by("last_fetched", "pk")

    if limit:
        packages = packages[:limit]

    total = packages.count()
    print(f"{total} package(s) to update")

    rate_limiter = RateLimiter(
        min_interval=min_interval,
        max_per_minute=max_per_minute if max_per_minute > 0 else None,
        jitter=jitter,
        stop_on_limit=True,
    )

    started = time.monotonic()
    packages_to_update = []
    exception_updates = []
    update_fields = [
        "repo_description",
        "repo_forks",
        "repo_watchers",
        "participants",
        "date_repo_archived",
        "commits_over_52w",
        "last_commit_date",
        "last_fetched",
        "score",
    ]
    exception_fields = [
        "date_deprecated",
        "last_exception",
        "last_exception_at",
        "last_exception_count",
    ]

    def flush_updates() -> None:
        nonlocal packages_to_update, exception_updates

        if not packages_to_update:
            return

        # Bulk write avoids per-row saves and reduces DB round-trips.
        Package.objects.bulk_update(packages_to_update, fields=update_fields)
        print(f"[green]Flushed {len(packages_to_update)} package(s) to DB.[/green]")
        packages_to_update = []

        if not exception_updates:
            return

        Package.objects.bulk_update(exception_updates, fields=exception_fields)
        print(
            f"[yellow]Flushed {len(exception_updates)} exception update(s) to DB.[/yellow]"
        )
        exception_updates = []

    def queue_exception_update(
        package: Package, *, deprecated: bool, error: Exception
    ) -> None:
        package.last_exception = error
        package.last_exception_at = timezone.now()
        package.last_exception_count = (package.last_exception_count or 0) + 1
        if deprecated:
            package.date_deprecated = timezone.now()
        exception_updates.append(package)
        if len(exception_updates) >= chunk_size:
            flush_updates()

    for package in packages.iterator(chunk_size=chunk_size):
        if time_budget is not None:
            elapsed = time.monotonic() - started
            if elapsed >= time_budget:
                print("[yellow]Time budget reached; stopping early.[/yellow]")
                break

        print(f"[blue]Processing {package.pk} :: {package.title}[/blue]")

        try:
            rate_limiter.stop_if_remaining_below(
                getattr(github, "ratelimit_remaining", None),
                rate_threshold,
                label="GitHub",
            )
        except RuntimeError:
            print("[yellow]GitHub rate limit reached; stopping early.[/yellow]")
            break

        try:
            rate_limiter.wait()
        except RuntimeError:
            print("[yellow]Rate limit reached; stopping early.[/yellow]")
            break

        try:
            try:
                package.fetch_metadata(fetch_pypi=False, fetch_repo=True, save=False)
                package.fetch_commits(save=False)
                if not package.repo_description:
                    package.repo_description = ""
                package.last_fetched = timezone.now()
                package.score = package.calculate_score()
                packages_to_update.append(package)
                print(
                    f"[green]Updated {package.pk} :: {package.title} | score={package.score}[/green]"
                )
                if len(packages_to_update) >= chunk_size:
                    flush_updates()

            except RepoRateLimitError as e:
                print("[yellow]Provider rate limit reached; stopping early.[/yellow]")
                raise e
                # break
            except NotFoundError as e:
                logger.error(f"Package was not found for {package.title}.")
                queue_exception_update(package, deprecated=True, error=e)

            except UnexpectedResponse as e:
                logger.error(f"Empty repo found for {package.title}.")
                queue_exception_update(package, deprecated=True, error=e)

            except Exception as e:
                logger.error(
                    f"Error while fetching package details for {package.title}."
                )
                raise PackageUpdaterException(e, package.title)

        except PackageUpdaterException as e:
            logger.error(f"Unable to update {package.title}", exc_info=True)
            queue_exception_update(package, deprecated=False, error=e)
        except RepoRateLimitError:
            print("[yellow]Provider rate limit reached; stopping early.[/yellow]")
            break

    flush_updates()
    healthcheck(settings.PACKAGE_HEALTHCHECK_URL)
