"""One package at a time: the steps the probe commands and tasks share.

Each function here does the work for a single package and reports what
happened, without printing or deciding which packages to visit. The
management commands wrap them in a loop with a progress report; the
Django Q tasks in `probes.tasks` wrap them one package per task so the
cluster can fan the work out.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils.timezone import now

from probes.checkouts import (
    CheckoutError,
    ScanResult,
    checkout_commit,
    checkout_path,
    checkout_size,
    discard_checkout,
    pypi_is_published,
    repo_is_reachable,
    scan_checkout,
    sync_checkout,
)
from probes.imports import canonical_name, detect_import_names
from probes.models import Library, PackageProbe

MB = 1024 * 1024


def check_source(package, *, timeout: int = 30, save: bool = True):
    """Decide whether a package's source is worth keeping a checkout of.

    Returns (ok, note). `ok` is None when neither question could be
    answered, in which case nothing is saved and the package keeps its
    previous verdict.
    """
    ok, note = repo_is_reachable(package.repo_url, timeout=timeout)
    # A curated list has no release to check; the repo answering is enough.
    if ok and not package.is_awesome_list:
        ok, note = pypi_is_published(package.pypi_url)

    if ok is None or not save:
        return ok, note

    package.probe = ok
    package.probe_note = "" if ok else note[:200]
    package.probe_checked_at = now()
    package.save(update_fields=["probe", "probe_note", "probe_checked_at"])
    return ok, note


@dataclass
class SyncOutcome:
    action: str  # cloned, updated, failed or too_big
    size: int = 0
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.action in ("cloned", "updated")


def sync_package(
    package, *, depth: int = 1, timeout: int = 300, max_mb: int | None = None
) -> SyncOutcome:
    """Clone or update one checkout, measure it, and apply the size cap."""
    try:
        path, action = sync_checkout(package, depth=depth, timeout=timeout)
    except CheckoutError as exc:
        return SyncOutcome("failed", note=str(exc))

    # Measured every time, not just against a cap: the size is worth
    # knowing on its own, and it is what any later cap reads.
    size = checkout_size(path)
    package.probe_bytes = size

    if max_mb is not None and size > max_mb * MB:
        # Cloning it was the only way to find out how big it is, so the
        # cost is already paid; what the cap saves is keeping it and
        # fetching it again on every run after this.
        discard_checkout(path)
        note = f"checkout is {size // MB:,}MB"
        package.probe_wanted = False
        package.probe_wanted_note = note
        package.save(update_fields=["probe_wanted", "probe_wanted_note", "probe_bytes"])
        return SyncOutcome("too_big", size=size, note=note)

    package.save(update_fields=["probe_bytes"])
    return SyncOutcome(action, size=size)


def record_import_names(package, *, save: bool = True) -> Library | None:
    """Read what the package is imported as out of its checkout.

    Returns the Library row, unsaved when `save` is False, or None when
    there is no checkout to read.
    """
    pypi_name = canonical_name(package.pypi_name or package.slug)
    names = detect_import_names(checkout_path(package), pypi_name=pypi_name)
    if not names:
        return None

    if not save:
        return Library(
            pypi_name=pypi_name, import_name=names[0], also_imports=names[1:]
        )

    library, _created = Library.objects.update_or_create(
        pypi_name=pypi_name,
        defaults={
            "import_name": names[0],
            "also_imports": names[1:],
            "source": Library.Source.CHECKOUT,
            "package": package,
        },
    )
    return library


def libraries_to_scan(scan_packages: tuple[str, ...] = ()) -> tuple[str, ...]:
    """An explicit list wins; otherwise the libraries toggled on, which
    is how this grows without a code change. Django is the fallback so a
    fresh install still scans something."""
    return tuple(scan_packages) or Library.scan_for() or ("django",)


def scan_package(
    package,
    scan_packages: tuple[str, ...] = (),
    *,
    force: bool = False,
    save: bool = True,
) -> tuple[str, ScanResult | None]:
    """Count the API use in one checkout and store it as the profile.

    Returns (status, result). Status is "missing" when there is no
    checkout, "unchanged" when the checkout is still on the commit the
    profile was read from for the same libraries, or "scanned".
    """
    scan_packages = libraries_to_scan(scan_packages)
    path = checkout_path(package)
    if not (path / ".git").is_dir():
        return "missing", None

    commit = checkout_commit(path)
    # Reverse one-to-one access raises when there is no profile yet.
    profile = getattr(package, "probe_profile", None)
    if (
        not force
        and commit
        and profile is not None
        and profile.scanned_at is not None
        and profile.commit == commit
        and tuple(profile.libraries) == scan_packages
    ):
        return "unchanged", None

    result = scan_checkout(path, scan_packages)

    if save:
        # Sorted most used first, since the list keeps its order and the
        # first thing anyone wants is the top of it.
        symbols = [
            {
                "symbol": symbol,
                "count": count,
                "library": result.library_of(symbol),
            }
            for symbol, count in result.usage.most_common()
        ]
        patterns = [
            {"pattern": pattern, "count": count}
            for pattern, count in result.patterns.most_common()
        ]
        PackageProbe.objects.update_or_create(
            package=package,
            defaults={
                "symbols": symbols,
                "patterns": patterns,
                "libraries": list(result.libraries),
                "files_scanned": result.files_scanned,
                "files_skipped": result.files_skipped,
                "commit": commit,
                "scanned_at": now(),
            },
        )

    return "scanned", result
