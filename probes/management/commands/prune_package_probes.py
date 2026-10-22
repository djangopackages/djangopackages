from __future__ import annotations

import djclick as click
from django.conf import settings
from rich import print as rprint

from package.models import Package
from probes import stats as probe_stats
from probes.checkouts import checkout_path, discard_checkout, scannable_packages
from probes.models import PackageProbe


@click.command()
@click.option(
    "--keep-checkouts",
    is_flag=True,
    help="Drop the stored profiles but leave the checkouts on disk",
)
@click.option("--dry-run", is_flag=True, help="List what would go")
def command(keep_checkouts: bool, dry_run: bool):
    """Drop profiles and checkouts for packages we no longer probe.

    A package can leave the set after it was scanned: Django itself is
    excluded because its source defines the symbols we count rather
    than using them, a repo can go away, and the size cap marks things
    unwanted. The profile from the last scan would otherwise sit in the
    roll-ups forever, which is worse than never having scanned it,
    because the number looks current.

    Run `build_probe_catalog` afterwards. The catalogue is a summary of
    the profiles, so it keeps counting what this removed until it is
    rebuilt.
    """
    # A subquery, so the database compares the two sets rather than us
    # sending it thousands of ids.
    wanted = scannable_packages(min_score=None).order_by().values("pk")

    stale = (
        PackageProbe.objects.exclude(package_id__in=wanted)
        .select_related("package")
        .order_by("package__slug")
    )

    removed = 0
    freed = 0
    for profile in stale:
        package = profile.package
        path = checkout_path(package)
        size = package.probe_bytes or 0

        rprint(
            f"[yellow]{package.slug}[/yellow] "
            f"profile from {profile.scanned_at:%Y-%m-%d}"
            if profile.scanned_at
            else f"[yellow]{package.slug}[/yellow] profile"
        )

        if dry_run:
            removed += 1
            continue

        profile.delete()
        if not keep_checkouts and path.exists():
            discard_checkout(path)
            freed += size
            Package.objects.filter(pk=package.pk).update(probe_bytes=None)
        removed += 1

    if dry_run:
        rprint(f"[dim]would drop {removed:,} profiles[/dim]")
        return

    if removed:
        probe_stats.invalidate()

    rprint(f"dropped {removed:,} profiles")
    if freed:
        rprint(f"[dim]{freed // (1024 * 1024):,}MB of checkouts removed[/dim]")
    if removed:
        rprint("[dim]run build_probe_catalog to refresh the roll-ups[/dim]")
    rprint(f"[dim]checkouts in {settings.PACKAGE_REPO_ROOT}[/dim]")
