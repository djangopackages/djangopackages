from __future__ import annotations

import djclick as click
from rich import print as rprint

from probes import pipeline
from probes.awesome import (
    awesome_lists,
    package_index,
    tag_all_lists,
    tag_listed_packages,
)


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Only these list package slug(s)")
@click.option(
    "--sync", is_flag=True, help="Refresh each list's checkout before reading it"
)
@click.option("--dry-run", is_flag=True, help="Report what would change, save nothing")
def command(slugs: tuple[str, ...], sync: bool, dry_run: bool):
    """Tag the packages each awesome list names.

    Reads the README out of every `awesome-list` package's checkout and
    gives each repository or PyPI project it links to the list's slug
    as a tag. A package that drops off the list loses the tag. Meant to
    run from a schedule; `init_scheduled_jobs` has the job.
    """
    lists = awesome_lists()
    if slugs:
        lists = lists.filter(slug__in=slugs)
        missing = set(slugs) - set(lists.values_list("slug", flat=True))
        for slug in sorted(missing):
            rprint(f"[yellow]{slug}: not a package tagged awesome-list[/yellow]")

    if sync:
        for list_package in lists:
            outcome = pipeline.sync_package(list_package)
            rprint(f"  {list_package.slug}: checkout {outcome.action} {outcome.note}")

    if slugs:
        index = package_index()
        outcomes = [
            tag_listed_packages(p, index=index, save=not dry_run) for p in lists
        ]
    else:
        outcomes = tag_all_lists(save=not dry_run)

    verb = "would add" if dry_run else "added"
    for o in outcomes:
        if not o.ok:
            rprint(f"[red]{o.tag}: {o.note}[/red]")
            continue
        rprint(
            f"[bold]{o.tag}[/bold]: {o.links} links, {o.listed} on the site, "
            f"{verb} {o.added}, removed {o.removed}"
        )
    if not outcomes:
        rprint("[yellow]no packages are tagged awesome-list[/yellow]")
