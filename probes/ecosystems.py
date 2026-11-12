"""Ask ecosyste.ms what it already knows about PyPI projects.

https://packages.ecosyste.ms indexes PyPI and the forges together. For a
name it returns the repository URL already resolved, the repository's
stars, age and activity, monthly downloads, dependents and advisories.
That is most of what vetting a candidate needs, without a rate-limited
forge call of our own. `fetch_packages` asks for up to 100 names in one
request through their bulk lookup, which is how a backlog of thousands
fits inside the anonymous quota.

The API is public (https://ecosyste.ms/api). Data is CC BY-SA 4.0.

Coverage lags PyPI by days for brand-new names, so this is a second
source next to the PyPI JSON, never the only one. Anonymous use allows
5,000 requests a day and responses are cached for a day on their side.
Every response says how many requests are left today; the client keeps
the latest figure in `remaining` so a long run can stop before the
quota runs out.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import httpx2
from django.conf import settings

REGISTRY_URL = "https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages"
BULK_URL = "https://packages.ecosyste.ms/api/v1/packages/bulk_lookup"
BULK_SIZE = 100  # their maximum per request
# A bulk lookup of 100 older packages with full repository data took more
# than 10 seconds in production; the whole 18,000-name backfill averaged
# about 3 seconds a batch with a few far slower.
BULK_TIMEOUT = 90.0

# Top-level fields worth keeping, and the repository fields under them.
PACKAGE_KEYS = (
    "repository_url",
    "homepage",
    "documentation_url",
    "normalized_licenses",
    "versions_count",
    "first_release_published_at",
    "latest_release_published_at",
    "latest_release_number",
    "downloads",
    "downloads_period",
    "dependent_packages_count",
    "dependent_repos_count",
    "advisories",
    "funding_links",
    "maintainers",
    "last_synced_at",
)
REPO_KEYS = (
    "full_name",
    "html_url",
    "description",
    "stargazers_count",
    "forks_count",
    "subscribers_count",
    "open_issues_count",
    "archived",
    "fork",
    "created_at",
    "pushed_at",
    "language",
    "license",
    "topics",
    "last_synced_at",
)


class EcosystemsClient:
    """ecosyste.ms asks known users to identify themselves with an email
    address, which puts requests in their "polite pool" with steadier
    response times. `ECOSYSTEMS_CONTACT_EMAIL` is sent as the standard
    `From` header when set; without it we are in the common pool."""

    def __init__(
        self,
        *,
        user_agent: str = "djangopackages/probes (+https://djangopackages.org)",
        timeout: float = 10.0,
        bulk_timeout: float = BULK_TIMEOUT,
        contact_email: str | None = None,
    ):
        if contact_email is None:
            contact_email = getattr(settings, "ECOSYSTEMS_CONTACT_EMAIL", "")
        headers = {"Accept": "application/json", "User-Agent": user_agent}
        if contact_email:
            headers["From"] = contact_email
        self._session = httpx2.Client(timeout=timeout, headers=headers)
        self.bulk_timeout = bulk_timeout
        self.remaining: int | None = None
        self.requests = 0

    def _note(self, response) -> None:
        self.requests += 1
        try:
            self.remaining = int(response.headers["x-ratelimit-remaining"])
        except (KeyError, TypeError, ValueError):
            pass

    def fetch_package(self, name: str) -> dict[str, Any] | None:
        """The trimmed record, or None when ecosyste.ms has not seen the name.

        Raises `httpx2.HTTPError` for anything other than a clean answer
        or a 404, so a caller can tell "unknown to them" from "they are
        down" and only the former is worth remembering.
        """
        response = self._session.get(f"{REGISTRY_URL}/{name.strip()}")
        self._note(response)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error"):
            return None
        return trimmed(payload)

    def fetch_packages(self, names: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Trimmed records for up to `BULK_SIZE` names, in one request.

        Keyed by `canonical(name)`. Names ecosyste.ms has not seen are
        simply absent. Raises `httpx2.HTTPError` when the request fails.
        """
        wanted = sorted({canonical(name) for name in names})
        if len(wanted) > BULK_SIZE:
            raise ValueError(f"at most {BULK_SIZE} names per request")
        if not wanted:
            return {}
        purls = [f"pkg:pypi/{name}" for name in wanted]
        response = self._session.post(
            BULK_URL, json={"purls": purls}, timeout=self.bulk_timeout
        )
        self._note(response)
        response.raise_for_status()
        payload = response.json()
        found = {}
        for record in payload if isinstance(payload, list) else []:
            if not isinstance(record, dict):
                continue
            if (record.get("registry") or {}).get("name") not in (None, "pypi.org"):
                continue
            name = canonical(record.get("name") or "")
            if name in wanted:
                found[name] = trimmed(record)
        return found


def canonical(name: str) -> str:
    """PyPI's normalized form, which is how ecosyste.ms names its records."""
    return re.sub(r"[-_.]+", "-", name).lower()


def trimmed(payload: dict[str, Any]) -> dict[str, Any]:
    data = {key: payload.get(key) for key in PACKAGE_KEYS if key in payload}
    maintainers = data.get("maintainers") or []
    data["maintainers"] = [
        {
            "login": m.get("login"),
            "packages_count": m.get("packages_count"),
            "html_url": m.get("html_url"),
        }
        for m in maintainers
        if isinstance(m, dict)
    ]
    data["advisories"] = len(payload.get("advisories") or [])
    repo = payload.get("repo_metadata") or {}
    data["repo"] = {key: repo.get(key) for key in REPO_KEYS if key in repo}
    stats = repo.get("commit_stats") or {}
    data["repo"]["total_commits"] = stats.get("total_commits")
    data["repo"]["total_committers"] = stats.get("total_committers")
    return data
