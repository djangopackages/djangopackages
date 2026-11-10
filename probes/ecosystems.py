"""One request to ecosyste.ms for what it already knows about a PyPI project.

https://packages.ecosyste.ms indexes PyPI and the forges together. For a
name it returns the repository URL already resolved, the repository's
stars, age and activity, monthly downloads, dependents and advisories.
That is most of what vetting a candidate needs, and it costs one
request instead of a PyPI call plus a rate-limited forge call.

The API is public (https://ecosyste.ms/api). Data is CC BY-SA 4.0.

Coverage lags PyPI by days for brand-new names, so this is a second
source next to the PyPI JSON, never the only one. Anonymous use allows
5,000 requests a day and responses are cached for a day on their side.
"""

from __future__ import annotations

from typing import Any

import httpx2
from django.conf import settings

REGISTRY_URL = "https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages"

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
        contact_email: str | None = None,
    ):
        if contact_email is None:
            contact_email = getattr(settings, "ECOSYSTEMS_CONTACT_EMAIL", "")
        headers = {"Accept": "application/json", "User-Agent": user_agent}
        if contact_email:
            headers["From"] = contact_email
        self._session = httpx2.Client(timeout=timeout, headers=headers)

    def fetch_package(self, name: str) -> dict[str, Any] | None:
        """The trimmed record, or None when ecosyste.ms has not seen the name.

        Raises `httpx2.HTTPError` for anything other than a clean answer
        or a 404, so a caller can tell "unknown to them" from "they are
        down" and only the former is worth remembering.
        """
        response = self._session.get(f"{REGISTRY_URL}/{name.strip()}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error"):
            return None
        return trimmed(payload)


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
