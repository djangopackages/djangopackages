"""Metrics from the pypi-data dump that PyPI's own API cannot give us.

https://github.com/sethmlarson/pypi-data publishes a SQLite database of
every project on PyPI a few times a year: requirements, uploads, OpenSSF
Scorecard, known vulnerabilities. The one number worth the 1.6GB is
dependents, how many other projects require ours, which is the closest
thing PyPI has to "used by" and which no per-project endpoint offers.

The dump is fetched once per release and kept on disk; `sync` is cheap
to run again when nothing has changed.
"""

from __future__ import annotations

import gzip
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import httpx2
from django.conf import settings
from django.utils.timezone import now

from package.models import Package
from probes.imports import canonical_name

RELEASES_URL = "https://api.github.com/repos/sethmlarson/pypi-data/releases/latest"
ASSET_NAME = "pypi.db.gz"
DB_NAME = "pypi.db"
TAG_FILE = "release.txt"


@dataclass(frozen=True)
class Release:
    tag: str
    url: str
    published_at: str


def latest_release(*, timeout: float = 30.0) -> Release:
    response = httpx2.get(RELEASES_URL, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    data = response.json()
    asset = next(a for a in data["assets"] if a["name"] == ASSET_NAME)
    return Release(
        tag=data["tag_name"],
        url=asset["browser_download_url"],
        published_at=data["published_at"],
    )


def db_path(root: Path | None = None) -> Path:
    return (root or settings.PYPI_DATA_ROOT) / DB_NAME


def have_release(root: Path | None = None) -> str:
    """The release tag of the dump on disk, or "" if there is none."""
    root = root or settings.PYPI_DATA_ROOT
    try:
        tag = (root / TAG_FILE).read_text().strip()
    except OSError:
        return ""
    return tag if (root / DB_NAME).exists() else ""


def download(release: Release, root: Path | None = None, *, timeout: float = 600.0):
    """Fetch and unpack one release into `root`, replacing what was there.

    The archive lands on disk first and is unpacked from there, so neither
    it nor the database is ever held in memory. Both are written under
    temporary names and renamed at the end, so a failed download never
    leaves a half-written database behind.
    """
    root = root or settings.PYPI_DATA_ROOT
    root.mkdir(parents=True, exist_ok=True)
    archive = root / (ASSET_NAME + ".partial")
    partial = root / (DB_NAME + ".partial")

    with (
        httpx2.stream(
            "GET", release.url, timeout=timeout, follow_redirects=True
        ) as response,
        archive.open("wb") as out,
    ):
        response.raise_for_status()
        for chunk in response.iter_bytes(4 * 1024 * 1024):
            out.write(chunk)

    with gzip.open(archive, "rb") as src, partial.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
    archive.unlink()
    partial.replace(root / DB_NAME)
    (root / TAG_FILE).write_text(release.tag + "\n")


@dataclass
class Metrics:
    dependents: int = 0
    dependencies: int = 0
    scorecard: float | None = None
    has_vulnerabilities: bool | None = None
    last_uploaded_at: str | None = None


def _norm_sql(column: str) -> str:
    # PEP 503 in SQLite: lower-case, and _ and . become -. Runs of
    # separators are rare enough in dep names that this is close enough.
    return f"lower(replace(replace({column}, '_', '-'), '.', '-'))"


def read_metrics(path: Path, names: set[str]) -> dict[str, Metrics]:
    """Metrics for the given canonical project names.

    One pass over `deps` for dependents, since the table has no index on
    the dependency side and four million rows group faster than four
    thousand lookups seek.
    """
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        found: dict[str, Metrics] = {}
        rows = con.execute(
            f"select {_norm_sql('name')}, scorecard_overall, has_vulnerabilities,"
            " last_uploaded_at from packages"
        )
        for name, scorecard, vulnerable, uploaded in rows:
            if name in names:
                found[name] = Metrics(
                    scorecard=scorecard,
                    has_vulnerabilities=None
                    if vulnerable is None
                    else bool(vulnerable),
                    last_uploaded_at=uploaded,
                )

        rows = con.execute(
            f"select {_norm_sql('dep_name')}, count(distinct package_name)"
            " from deps group by 1"
        )
        for name, count in rows:
            if name in found:
                found[name].dependents = count

        rows = con.execute(
            f"select {_norm_sql('package_name')}, count(distinct {_norm_sql('dep_name')})"
            " from deps where extra is null or extra = '' group by 1"
        )
        for name, count in rows:
            if name in found:
                found[name].dependencies = count
        return found
    finally:
        con.close()


@dataclass
class SyncOutcome:
    release: str
    downloaded: bool
    packages: int = 0
    matched: int = 0


def sync(
    *, force: bool = False, path: Path | None = None, save: bool = True
) -> SyncOutcome:
    """Bring the dump up to date and write its metrics onto our packages.

    `path` points at a database already on disk, for a run that should
    not touch the network.
    """
    if path is None:
        release = latest_release()
        downloaded = force or have_release() != release.tag
        if downloaded:
            download(release)
        path = db_path()
        tag = release.tag
    else:
        downloaded = False
        tag = "local"

    packages = list(Package.objects.exclude(pypi_url="").only("pk", "pypi_url", "slug"))
    by_name = {canonical_name(p.pypi_name): p for p in packages if p.pypi_name}
    metrics = read_metrics(path, set(by_name))

    outcome = SyncOutcome(release=tag, downloaded=downloaded, packages=len(by_name))
    stamp = now()
    for name, package in by_name.items():
        m = metrics.get(name)
        if m is None:
            # Not on PyPI any more, or never was under this name. Clear
            # rather than keep a number from a release that had it.
            fields = dict(
                pypi_dependents=None,
                pypi_dependencies=None,
                pypi_scorecard=None,
                pypi_has_vulnerabilities=None,
            )
        else:
            outcome.matched += 1
            fields = dict(
                pypi_dependents=m.dependents,
                pypi_dependencies=m.dependencies,
                pypi_scorecard=m.scorecard,
                pypi_has_vulnerabilities=m.has_vulnerabilities,
            )
        if save:
            Package.objects.filter(pk=package.pk).update(
                pypi_data_synced_at=stamp, **fields
            )
    return outcome
