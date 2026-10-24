"""Dependents from deps.dev, Google's open source dependency graph.

PyPI knows what a project requires but not what requires it. deps.dev
has that inverted graph and serves it per package version through a
free, unauthenticated API: two small requests per package, one to find
the default version and one for its dependents. The count is for that
version only, so a package whose users pin an old release reads low;
that is the right bias for a "used today" signal.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx2
from django.utils.timezone import now

from package.models import Package
from probes.imports import canonical_name

PACKAGE_URL = "https://api.deps.dev/v3/systems/pypi/packages/{name}"
# Dependents are only on the alpha surface for now.
DEPENDENTS_URL = "https://api.deps.dev/v3alpha/systems/pypi/packages/{name}/versions/{version}:dependents"
TIMEOUT = 20.0


@dataclass(frozen=True)
class Dependents:
    version: str
    total: int
    direct: int


class NoAnswer(Exception):
    """deps.dev could not be asked right now; try again later."""


def _get(client: httpx2.Client, url: str) -> dict | None:
    """One request with one retry. None means a definite 404."""
    last: Exception | None = None
    for attempt in range(2):
        try:
            response = client.get(url, timeout=TIMEOUT)
        except httpx2.RequestError as exc:
            last = exc
        else:
            if response.status_code == 404:
                return None
            if response.status_code < 400:
                try:
                    return response.json()
                except ValueError as exc:
                    last = exc
            else:
                last = httpx2.HTTPStatusError(
                    f"{response.status_code}",
                    request=response.request,
                    response=response,
                )
        if attempt == 0:
            time.sleep(1)
    raise NoAnswer(str(last))


def fetch(name: str, *, client: httpx2.Client) -> Dependents | None:
    """Dependents of `name`'s default version, or None if deps.dev lacks it."""
    name = canonical_name(name)
    package = _get(client, PACKAGE_URL.format(name=name))
    if not package:
        return None
    default = next((v for v in package.get("versions", []) if v.get("isDefault")), None)
    if default is None:
        return None
    version = default["versionKey"]["version"]
    data = _get(client, DEPENDENTS_URL.format(name=name, version=version))
    if data is None:
        return None
    return Dependents(
        version=version,
        total=int(data.get("dependentCount", 0)),
        direct=int(data.get("directDependentCount", 0)),
    )


@dataclass
class SyncOutcome:
    asked: int = 0
    found: int = 0
    missing: int = 0
    no_answer: int = 0


def sync(packages, *, delay: float = 0.5, save: bool = True, log=None) -> SyncOutcome:
    """Record dependents for each package that has a PyPI name.

    A package deps.dev does not know is cleared rather than left with a
    number from an earlier run. A package it could not answer for is left
    alone, so a bad minute at their end does not blank our column.
    """
    outcome = SyncOutcome()
    with httpx2.Client(follow_redirects=True) as client:
        for package in packages:
            if not package.pypi_name:
                continue
            outcome.asked += 1
            try:
                found = fetch(package.pypi_name, client=client)
            except NoAnswer as exc:
                outcome.no_answer += 1
                if log:
                    log(f"{package.slug}: no answer ({exc})")
                continue

            if found is None:
                outcome.missing += 1
                fields = dict(pypi_dependents=None, pypi_direct_dependents=None)
            else:
                outcome.found += 1
                fields = dict(
                    pypi_dependents=found.total, pypi_direct_dependents=found.direct
                )
            if log:
                log(f"{package.slug}: {found}")
            if save:
                Package.objects.filter(pk=package.pk).update(
                    pypi_dependents_synced_at=now(), **fields
                )
            if delay:
                time.sleep(delay)
    return outcome
