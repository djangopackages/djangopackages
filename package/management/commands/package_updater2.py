from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
from package.pypi import PyPIClient, PyPIRateLimitError, update_package_from_pypi
from package.repos.base_handler import RepoRateLimitError
from package.scores import update_package_score


if TYPE_CHECKING:
    from github3 import GitHub

logger = logging.getLogger(__name__)


UPDATE_FIELDS = [
    # PyPI fields
    "pypi_classifiers",
    "pypi_requires_python",
    "documentation_url",
    "pypi_downloads",
    "pypi_license",
    "pypi_licenses",
    "latest_version",
    "supports_python3",
    "pypi_url",
    # Git fields
    "repo_description",
    "repo_forks",
    "repo_watchers",
    "participants",
    "date_repo_archived",
    "commits_over_52w",
    "last_commit_date",
    "commit_count",
    # Shared/computed fields
    "score",
    "last_fetched",
]

EXCEPTION_FIELDS = [
    "date_deprecated",
    "last_exception",
    "last_exception_at",
    "last_exception_count",
]


class StopPhase(Exception):
    """Signal to stop processing a particular phase due to rate limiting."""

    pass


@dataclass
class UpdateStats:
    """Track update statistics for reporting."""

    pypi_updated: int = 0
    pypi_skipped: int = 0
    pypi_errors: int = 0
    git_updated: int = 0
    git_skipped: int = 0
    git_errors: int = 0
    git_deprecated: int = 0
    scores_updated: int = 0
    total_processed: int = 0
    total_flushed: int = 0

    def summary(self) -> str:
        """Generate a summary string of the update statistics."""
        return (
            f"Processed: {self.total_processed} | "
            f"Flushed: {self.total_flushed} | "
            f"PyPI: {self.pypi_updated} updated, {self.pypi_errors} errors | "
            f"Git: {self.git_updated} updated, {self.git_deprecated} deprecated, {self.git_errors} errors | "
            f"Scores: {self.scores_updated} updated"
        )


@dataclass
class UpdateContext:
    """Context for the unified update operation."""

    # Rate limiters
    pypi_rate_limiter: RateLimiter
    git_rate_limiter: RateLimiter

    # Clients
    pypi_client: PyPIClient
    github: GitHub | None

    # Configuration
    chunk_size: int
    time_budget: int | None
    rate_threshold: int

    # Timing
    started: float = field(default_factory=time.monotonic)

    # Tracking
    stats: UpdateStats = field(default_factory=UpdateStats)

    # Batched updates - unified list for all update types
    packages_to_update: list[Package] = field(default_factory=list)
    exception_updates: list[Package] = field(default_factory=list)

    # Track packages already in batch (avoid duplicates)
    _batch_pks: set[int] = field(default_factory=set)

    # Phase control flags
    pypi_stopped: bool = False
    git_stopped: bool = False

    def time_remaining(self) -> float | None:
        """Calculate remaining time budget, or None if no budget set."""
        if self.time_budget is None:
            return None
        elapsed = time.monotonic() - self.started
        return max(0, self.time_budget - elapsed)

    def is_time_expired(self) -> bool:
        """Check if time budget has been exhausted."""
        remaining = self.time_remaining()
        return remaining is not None and remaining <= 0

    def add_to_batch(self, package: Package) -> None:
        """Add package to update batch, avoiding duplicates."""
        if package.pk not in self._batch_pks:
            self.packages_to_update.append(package)
            self._batch_pks.add(package.pk)

    def should_flush(self) -> bool:
        """Check if batch should be flushed."""
        return len(self.packages_to_update) >= self.chunk_size


class PackageUpdaterException(Exception):
    """Exception raised during package update operations."""

    def __init__(self, error: Exception, title: str):
        self.original_error = error
        self.title = title
        log_message = f"For {title}, {type(error)}: {error}"
        logging.critical(log_message)
        super().__init__(log_message)


def flush_updates(ctx: UpdateContext) -> int:
    """
    Flush all pending updates to database in a single bulk operation.

    Returns the number of packages flushed.
    """
    flushed = 0

    if ctx.packages_to_update:
        Package.objects.bulk_update(
            ctx.packages_to_update,
            fields=UPDATE_FIELDS,
            batch_size=ctx.chunk_size,
        )
        flushed = len(ctx.packages_to_update)
        ctx.stats.total_flushed += flushed
        print(f"[green]Flushed {flushed} package(s) to DB.[/green]")
        ctx.packages_to_update = []
        ctx._batch_pks = set()

    if ctx.exception_updates:
        Package.objects.bulk_update(
            ctx.exception_updates,
            fields=EXCEPTION_FIELDS,
            batch_size=ctx.chunk_size,
        )
        print(
            f"[yellow]Flushed {len(ctx.exception_updates)} exception update(s) to DB.[/yellow]"
        )
        ctx.exception_updates = []

    return flushed


def queue_exception_update(
    ctx: UpdateContext,
    package: Package,
    *,
    deprecated: bool,
    error: Exception,
) -> None:
    """Queue a package exception update for later bulk write."""
    package.last_exception = str(error)
    package.last_exception_at = timezone.now()
    package.last_exception_count = (package.last_exception_count or 0) + 1
    if deprecated:
        package.date_deprecated = timezone.now()
        ctx.stats.git_deprecated += 1
    ctx.exception_updates.append(package)


def update_pypi(ctx: UpdateContext, package: Package) -> bool:
    """
    Update a single package from PyPI.

    Returns True if update was successful.
    Raises StopPhase if rate limit is hit.
    """
    if not package.pypi_url:
        ctx.stats.pypi_skipped += 1
        return False

    if ctx.pypi_stopped:
        ctx.stats.pypi_skipped += 1
        return False

    try:
        ctx.pypi_rate_limiter.wait()
    except RuntimeError:
        print("[yellow]PyPI rate limit reached; stopping PyPI updates.[/yellow]")
        ctx.pypi_stopped = True
        raise StopPhase("PyPI rate limit")

    try:
        update_package_from_pypi(package, client=ctx.pypi_client, save=False)
        ctx.stats.pypi_updated += 1
        print(
            f"[green]  PyPI: {package.pypi_name} -> v{package.latest_version}[/green]"
        )
        return True

    except PyPIRateLimitError:
        print("[yellow]PyPI rate limit (429) reached; stopping PyPI updates.[/yellow]")
        ctx.pypi_stopped = True
        ctx.stats.pypi_errors += 1
        raise StopPhase("PyPI 429")

    except Exception as e:
        print(f"[red]  PyPI error: {e}[/red]")
        ctx.stats.pypi_errors += 1
        logger.exception("PyPI update failed for %s", package)
        return False


def update_git(ctx: UpdateContext, package: Package) -> bool:
    """
    Update a single package from its Git provider.

    Returns True if update was successful.
    Raises StopPhase if rate limit is hit.
    """
    if not package.repo_url:
        ctx.stats.git_skipped += 1
        return False

    if ctx.git_stopped:
        ctx.stats.git_skipped += 1
        return False

    # Check GitHub rate limit before proceeding
    if ctx.github:
        try:
            ctx.git_rate_limiter.stop_if_remaining_below(
                getattr(ctx.github, "ratelimit_remaining", None),
                ctx.rate_threshold,
                label="GitHub",
            )
        except RuntimeError:
            print("[yellow]GitHub quota low; stopping Git updates.[/yellow]")
            ctx.git_stopped = True
            raise StopPhase("GitHub quota")

    try:
        ctx.git_rate_limiter.wait()
    except RuntimeError:
        print("[yellow]Git rate limit reached; stopping Git updates.[/yellow]")
        ctx.git_stopped = True
        raise StopPhase("Git rate limit")

    try:
        repo = package.repo
        repo.fetch_metadata(package, save=False)
        ctx.stats.git_updated += 1
        print(
            f"[green]  Git: ★{package.repo_watchers} forks:{package.repo_forks}[/green]"
        )
        return True

    except RepoRateLimitError:
        print("[yellow]Provider rate limit reached; stopping Git updates.[/yellow]")
        ctx.git_stopped = True
        raise StopPhase("Provider rate limit")

    except NotFoundError as e:
        logger.error("Package not found for %s", package.title)
        queue_exception_update(ctx, package, deprecated=True, error=e)
        ctx.stats.git_errors += 1
        return False

    except UnexpectedResponse as e:
        logger.error("Empty repo found for %s", package.title)
        queue_exception_update(ctx, package, deprecated=True, error=e)
        ctx.stats.git_errors += 1
        return False

    except Exception as e:
        logger.error(
            "Error fetching package details for %s", package.title, exc_info=True
        )
        queue_exception_update(ctx, package, deprecated=False, error=e)
        ctx.stats.git_errors += 1
        return False


def process_package(
    ctx: UpdateContext,
    package: Package,
    *,
    skip_pypi: bool,
    skip_git: bool,
    skip_scores: bool,
) -> bool:
    """
    Process a single package through all update phases.

    Returns True if any updates were made.
    """
    updated = False

    # Phase 1: PyPI update
    if not skip_pypi:
        try:
            if update_pypi(ctx, package):
                updated = True
        except StopPhase:
            pass  # Continue with other phases

    # Phase 2: Git provider update
    if not skip_git:
        try:
            if update_git(ctx, package):
                updated = True
        except StopPhase:
            pass  # Continue with score phase

    # Phase 3: Score recalculation (always possible, no external API)
    if not skip_scores:
        if update_package_score(package, save=False):
            ctx.stats.scores_updated += 1
            updated = True
            print(f"[green]  Score: {package.score}[/green]")

    # Mark last_fetched if any update occurred
    if updated:
        package.last_fetched = timezone.now()
        ctx.add_to_batch(package)

    return updated


@click.command()
@click.option(
    "--all", "update_all", is_flag=True, default=False, help="Ignore staleness filter"
)
@click.option(
    "--pypi-url", type=str, default=None, help="Update a single package by PyPI slug"
)
@click.option("--limit", default=None, type=int, help="Max packages to process")
@click.option("--chunk-size", default=200, type=int, help="Batch size for DB writes")
@click.option(
    "--stale-hours", default=24, type=int, help="Only update packages older than this"
)
@click.option(
    "--pypi-min-interval",
    default=0.2,
    type=float,
    help="Min seconds between PyPI requests",
)
@click.option(
    "--pypi-max-per-minute", default=60, type=int, help="Max PyPI requests per minute"
)
@click.option(
    "--git-min-interval",
    default=0.5,
    type=float,
    help="Min seconds between Git requests",
)
@click.option(
    "--git-max-per-minute", default=60, type=int, help="Max Git requests per minute"
)
@click.option(
    "--jitter", default=0.05, type=float, help="Random delay to avoid burst alignment"
)
@click.option(
    "--time-budget", default=None, type=int, help="Stop after this many seconds"
)
@click.option(
    "--pypi-timeout", default=10.0, type=float, help="PyPI HTTP timeout in seconds"
)
@click.option(
    "--rate-threshold",
    default=50,
    type=int,
    help="Stop when GitHub quota drops below this",
)
@click.option("--skip-pypi", is_flag=True, default=False, help="Skip PyPI updates")
@click.option(
    "--skip-git", is_flag=True, default=False, help="Skip Git provider updates"
)
@click.option(
    "--skip-scores", is_flag=True, default=False, help="Skip score recalculation"
)
def command(
    update_all,
    pypi_url,
    limit,
    chunk_size,
    stale_hours,
    pypi_min_interval,
    pypi_max_per_minute,
    git_min_interval,
    git_max_per_minute,
    jitter,
    time_budget,
    pypi_timeout,
    rate_threshold,
    skip_pypi,
    skip_git,
    skip_scores,
):
    """
    Unified package updater for PyPI metadata, Git provider data, and scores.

    Updates packages in the following order:
    1. PyPI metadata (versions, classifiers, Python support)
    2. Git provider data (stars, forks, commits, last update)
    3. Package scores (calculated from watchers, activity, Python 3 support)

    All updates are batched and flushed together for efficiency.

    Examples:
        # Update all stale packages (older than 24 hours)
        python manage.py package_updater2

        # Update all packages regardless of staleness
        python manage.py package_updater2 --all

        # Update a specific package
        python manage.py package_updater2 --pypi-url django

        # Run with a 5-minute time budget
        python manage.py package_updater2 --time-budget 300

        # Only update Git data and scores (skip PyPI)
        python manage.py package_updater2 --skip-pypi
    """
    if chunk_size <= 0:
        raise click.ClickException("--chunk-size must be > 0")

    if stale_hours < 0:
        raise click.ClickException("--stale-hours must be >= 0")

    now = timezone.now()
    cutoff = now - timezone.timedelta(hours=stale_hours)

    # Build base queryset
    if pypi_url:
        packages = Package.objects.filter(pypi_url=pypi_url)
    else:
        packages = Package.objects.filter(
            date_deprecated__isnull=True,
        ).filter(Q(last_exception_count__lte=5) | Q(last_exception_count__isnull=True))

        if not update_all:
            packages = packages.filter(
                Q(last_fetched__lt=cutoff) | Q(last_fetched__isnull=True)
            )

        packages = packages.order_by("last_fetched", "pk")

    if limit:
        packages = packages[:limit]

    total = packages.count()
    print(f"[bold]{total} package(s) to update[/bold]")

    if total == 0:
        print("[green]Nothing to update.[/green]")
        return

    # Initialize GitHub client
    github = None
    if hasattr(settings, "GITHUB_TOKEN") and settings.GITHUB_TOKEN:
        try:
            github = github_login(token=settings.GITHUB_TOKEN)
        except Exception as e:
            logger.warning("Failed to initialize GitHub client: %s", e)

    # Initialize context
    ctx = UpdateContext(
        pypi_rate_limiter=RateLimiter(
            min_interval=pypi_min_interval,
            max_per_minute=pypi_max_per_minute if pypi_max_per_minute > 0 else None,
            jitter=jitter,
            stop_on_limit=False,
        ),
        git_rate_limiter=RateLimiter(
            min_interval=git_min_interval,
            max_per_minute=git_max_per_minute if git_max_per_minute > 0 else None,
            jitter=jitter,
            stop_on_limit=False,
        ),
        pypi_client=PyPIClient(
            timeout=pypi_timeout,
        ),
        github=github,
        chunk_size=chunk_size,
        time_budget=time_budget,
        rate_threshold=rate_threshold,
    )

    # Process packages
    for package in packages.iterator(chunk_size=chunk_size):
        if ctx.is_time_expired():
            print("[yellow]Time budget reached; stopping early.[/yellow]")
            break

        # Check if all phases are stopped
        if ctx.pypi_stopped and ctx.git_stopped and skip_scores:
            print("[yellow]All update phases stopped; exiting.[/yellow]")
            break

        ctx.stats.total_processed += 1
        print(
            f"[blue]{ctx.stats.total_processed}. Processing {package.pk} :: {package.title}[/blue]"
        )

        process_package(
            ctx,
            package,
            skip_pypi=skip_pypi,
            skip_git=skip_git,
            skip_scores=skip_scores,
        )

        # Flush when batch is full
        if ctx.should_flush():
            flush_updates(ctx)

        # Log progress periodically
        if ctx.stats.total_processed % 50 == 0:
            logger.info(
                "Progress: %d processed, %d flushed (PyPI: %d, Git: %d, Scores: %d)",
                ctx.stats.total_processed,
                ctx.stats.total_flushed,
                ctx.stats.pypi_updated,
                ctx.stats.git_updated,
                ctx.stats.scores_updated,
            )

    # Final flush
    flush_updates(ctx)

    # Print summary
    print(f"\n[bold green]{ctx.stats.summary()}[/bold green]")
    elapsed = (time.monotonic() - ctx.started) / 60
    print(f"[bold green]Completed in {elapsed:.2f} minutes[/bold green]")

    # Trigger healthchecks
    if hasattr(settings, "PYPI_HEALTHCHECK_URL") and not skip_pypi:
        healthcheck(settings.PYPI_HEALTHCHECK_URL)
    if hasattr(settings, "PACKAGE_HEALTHCHECK_URL") and not skip_git:
        healthcheck(settings.PACKAGE_HEALTHCHECK_URL)
