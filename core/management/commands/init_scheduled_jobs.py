import djclick as click
from django.db import IntegrityError
from django_q.models import Schedule
from django_q.tasks import schedule
from rich import print as rprint

TIMEOUT = 20 * 60 * 60  # 20 hours

# Each job is a Django Q schedule. The key is what --only takes; the
# name is the unique Schedule row, so re-running never duplicates one.
JOBS = {
    "search": {
        "name": "Build Search V3",
        "func": "django.core.management.call_command",
        "args": ("build_search_v3",),
        "cron": "12 23 * * *",
    },
    "package-updater": {
        "name": "Update All Packages from GitHub",
        "func": "django.core.management.call_command",
        "args": ("package_updater",),
        "cron": "36 17 * * *",
    },
    "pypi-updater": {
        "name": "Update All Packages from PyPI",
        "func": "django.core.management.call_command",
        "args": ("pypi_updater",),
        "cron": "48 21 * * *",
    },
    # The probe pipeline. The fan-out queues one task per package for
    # the network bound steps; the two single-pass roll-ups follow once
    # the cluster has had time to work through the queue.
    "probe-refresh": {
        "name": "Probe: queue source checks and checkout refreshes",
        "func": "probes.tasks.queue_probe_refresh",
        "args": (),
        "cron": "17 2 * * *",
    },
    "probe-profiles": {
        "name": "Probe: build profiles",
        "func": "django.core.management.call_command",
        "args": ("build_probe_profiles",),
        "cron": "12 5 * * *",
    },
    "probe-catalog": {
        "name": "Probe: build catalogue",
        "func": "django.core.management.call_command",
        "args": ("build_probe_catalog",),
        "cron": "12 6 * * *",
    },
    # Last-month download counts from pypistats.org, one request per
    # package two seconds apart, so a full pass takes about three hours.
    # Weekly, because the number is a 30-day window and the API is
    # someone else's. See #1065.
    "pypi-stats": {
        "name": "Update PyPI download counts",
        "func": "django.core.management.call_command",
        "args": ("pypi_stats",),
        "cron": "30 4 * * 0",
    },
    # Dependents and friends from the pypi-data dump. It is released a
    # few times a year and the sync skips the download when nothing has
    # changed, so weekly costs one small request most weeks. See #834.
    "pypi-data": {
        "name": "Sync metrics from the pypi-data dump",
        "func": "django.core.management.call_command",
        "args": ("pypi_data_sync",),
        "cron": "30 5 * * 1",
    },
    # The awesome lists: pull their READMEs and re-tag the packages they
    # name. Daily, since the lists change a few times a week at most.
    "awesome-lists": {
        "name": "Awesome lists: tag the packages they name",
        "func": "probes.tasks.refresh_awesome_lists",
        "args": (),
        "cron": "42 3 * * *",
    },
}


@click.command()
@click.option(
    "--only",
    "keys",
    multiple=True,
    type=click.Choice(sorted(JOBS)),
    help="Add just these jobs. Repeatable. Default is every job.",
)
@click.option("--list", "list_jobs", is_flag=True, help="Show the jobs and exit")
def command(keys: tuple[str, ...], list_jobs: bool):
    """Add the scheduled jobs to the Django Q cluster.

    Safe to re-run: a job whose schedule already exists is left alone
    and reported, not duplicated.
    """
    if list_jobs:
        for key, job in JOBS.items():
            rprint(f"  [bold]{key:18}[/bold] {job['cron']:14} {job['name']}")
        return

    for key in keys or JOBS:
        job = JOBS[key]
        try:
            schedule(
                job["func"],
                *job["args"],
                name=job["name"],
                schedule_type=Schedule.CRON,
                cron=job["cron"],
                q_options={"timeout": TIMEOUT, "max_attempts": 1},
            )
        except IntegrityError:
            rprint(f"[yellow]exists[/yellow]  {job['name']}")
        else:
            rprint(f"[green]created[/green] {job['name']}")
