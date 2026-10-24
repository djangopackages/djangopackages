from __future__ import annotations

from pathlib import Path

import djclick as click
from rich import print as rprint

from package import pypi_data


@click.command()
@click.option("--force", is_flag=True, help="Download even if we have this release")
@click.option(
    "--db",
    "db",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Read this pypi.db instead of downloading one",
)
@click.option("--dry-run", is_flag=True, help="Compute the metrics, save nothing")
def command(force: bool, db: Path | None, dry_run: bool):
    """Pull the pypi-data dump and record what it says about our packages.

    Dependents (how many PyPI projects require ours), dependency count,
    OpenSSF Scorecard and the known-vulnerabilities flag, onto
    `Package.pypi_*`. The dump is 1.6GB and changes a few times a year;
    a run that finds the same release on disk skips the download.
    """
    outcome = pypi_data.sync(force=force, path=db, save=not dry_run)
    fetched = "downloaded" if outcome.downloaded else "already on disk"
    verb = "would update" if dry_run else "updated"
    rprint(
        f"[bold]{outcome.release}[/bold] ({fetched}): {outcome.matched:,} of "
        f"{outcome.packages:,} PyPI packages found in the dump, {verb} all "
        f"{outcome.packages:,}"
    )
