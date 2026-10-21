from __future__ import annotations

import djclick as click
from django.db.models import Q
from django.utils.timezone import now
from rich import print as rprint

from package.models import Package
from package.repo_checkouts import (
    CLONEABLE_HOSTS,
    pypi_is_published,
    repo_is_reachable,
)


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to check")
@click.option(
    "--recheck",
    is_flag=True,
    help="Also re-check packages already decided, not just the undecided ones",
)
@click.option(
    "--timeout", default=30, type=int, help="Seconds per git request (default: 30)"
)
@click.option("--dry-run", is_flag=True, help="Report findings without saving")
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    recheck: bool,
    timeout: int,
    dry_run: bool,
):
    """Decide which packages are worth keeping a source checkout of.

    Sets `probe` by asking the two questions that matter: does the git
    remote still answer, and is the project still on PyPI. Neither
    requires a clone, so this is cheap enough to run over the whole
    catalogue and is the thing that makes `probe` mean something.

    Packages are left alone once decided, so the default run only picks
    up new ones. Pass --recheck to revisit.
    """
    queryset = Package.objects.order_by("-score", "title")
    if slugs:
        queryset = queryset.filter(slug__in=slugs)
    elif not recheck:
        queryset = queryset.filter(probe__isnull=True)
    if limit:
        queryset = queryset[:limit]

    host_q = Q()
    for host in CLONEABLE_HOSTS:
        host_q |= Q(repo_url__icontains=host)

    on = off = 0
    reasons: dict[str, int] = {}

    for package in queryset:
        ok, note = repo_is_reachable(package.repo_url, timeout=timeout)
        if ok:
            ok, note = pypi_is_published(package.pypi_url)

        if ok:
            on += 1
        else:
            off += 1
            key = note.split(":")[0][:40]
            reasons[key] = reasons.get(key, 0) + 1
            rprint(f"[dim]off[/dim] {package.slug}: {note}")

        if dry_run:
            continue

        package.probe = ok
        package.probe_note = "" if ok else note[:200]
        package.probe_checked_at = now()
        package.save(update_fields=["probe", "probe_note", "probe_checked_at"])

    rprint(
        f"\nprobe on {on:,}  off {off:,}"
        + ("  [dim](dry run)[/dim]" if dry_run else "")
    )
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1])[:10]:
        rprint(f"   [dim]{count:>5,}[/dim]  {reason}")
