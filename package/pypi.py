from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING
from collections.abc import Mapping

import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from requests.exceptions import HTTPError, RequestException

from core.utils import status_choices_switch
from package.utils import normalize_license

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from package.models import Package


class PyPIRateLimitError(Exception):
    pass


_PY3_PROBE_VERSIONS = [
    # Keep this list current-ish; used only to answer "does it support *any* Python 3".
    "3.14",
    "3.13",
    "3.12",
    "3.11",
    "3.10",
    "3.9",
    "3.8",
    "3.7",
    "3.6",
    "3.5",
    "3.4",
    "3.3",
    "3.2",
    "3.1",
    "3.0",
]


@dataclass(frozen=True)
class PyPIProject:
    raw: Mapping[str, Any]

    @property
    def info(self) -> Mapping[str, Any]:
        try:
            info = self.raw["info"]
        except KeyError:
            return {}
        return info if isinstance(info, Mapping) else {}

    @property
    def urls(self) -> list[Any]:
        try:
            urls = self.raw["urls"]
        except KeyError:
            return []
        return urls if isinstance(urls, list) else []

    @property
    def docs_url(self) -> str | None:
        return self.raw.get("docs_url")

    @property
    def name(self) -> str:
        return self.info.get("name")

    @property
    def version(self) -> str:
        return self.info.get("version")

    @property
    def classifiers(self) -> list[str]:
        classifiers = self.info.get("classifiers")
        if isinstance(classifiers, list):
            return [str(c) for c in classifiers]
        return []

    @property
    def requires_python(self) -> str | None:
        requires_python = self.info.get("requires_python")
        return str(requires_python) if requires_python else None

    @property
    def project_urls(self) -> Mapping[str, Any]:
        urls = self.info.get("project_urls")
        return urls if isinstance(urls, Mapping) else {}


class PyPIClient:
    """Small, robust client for the public PyPI JSON API.

    Endpoint: https://pypi.org/pypi/<project>/json
    """

    def __init__(
        self,
        *,
        user_agent: str = "djangopackages/py-pypi-client",
        timeout: float | tuple[float, float] = 10.0,
    ):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": user_agent,
            }
        )
        self._timeout = timeout

    def get_project_json_url(self, project: str) -> str:
        project = project.strip().strip("/")
        return f"https://pypi.org/pypi/{project}/json"

    def fetch_project(self, project: str) -> PyPIProject:
        url = self.get_project_json_url(project)

        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()

        # Prefer requests' JSON decoding, fall back to stdlib in edge cases.
        try:
            payload = resp.json()
        except ValueError:
            payload = json.loads(resp.content)

        if not isinstance(payload, Mapping):
            raise ValueError("PyPI JSON response is not an object")

        return PyPIProject(raw=payload)


def _first_documentation_url(project_urls: Mapping[str, Any]) -> str | None:
    for key in ("Documentation", "Docs", "docs", "documentation"):
        value = project_urls.get(key)
        if value:
            return str(value)
    return None


def _supports_python3(
    requires_python: str | None, classifiers: list[str]
) -> bool | None:
    """
    Determine if a package supports Python 3.

    Returns:
        True if Python 3 is supported
        False if only Python 2 is supported
        None if support cannot be determined
    """
    classifier_says_py3 = any(
        c.startswith("Programming Language :: Python :: 3") for c in classifiers
    )

    if requires_python:
        try:
            spec = SpecifierSet(requires_python)
        except InvalidSpecifier:
            # If requires_python is malformed, fall back to classifier check
            logger.warning(
                "Invalid requires_python specifier: %s. Falling back to classifiers.",
                requires_python,
            )
            return True if classifier_says_py3 else None

        return any(spec.contains(v, prereleases=True) for v in _PY3_PROBE_VERSIONS)

    return True if classifier_says_py3 else None


def _parse_upload_time(value: str | None) -> timezone.datetime | None:
    """Parse upload time string to timezone-aware datetime."""
    if not value:
        return None

    if isinstance(value, str):
        dt = parse_datetime(value)
        if dt is None:
            return None
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    return None


def _extract_license_list(
    info_license: str | None,
    info_license_expression: str | None,
    classifiers: list[str],
) -> list[str]:
    """
    Extract license information from multiple sources.

    Priority order (as per PEP 639):
    1. license_expression (preferred)
    2. license field (legacy)
    3. classifiers

    Args:
        info_license: Legacy license field from package info
        info_license_expression: PEP 639 license expression from package info
        classifiers: List of trove classifiers

    Returns:
        List of unique, non-empty license identifiers
    """
    licenses = []

    # PEP 639 license_expression takes precedence
    if info_license_expression:
        text = normalize_license(info_license_expression)
        if text and text.strip():  # Ensure non-empty after normalization
            licenses.append(text)

    # Add legacy license field if not already present
    if info_license:
        text = normalize_license(info_license)
        if text and text.strip() and text not in licenses:
            licenses.append(text)

    # Extract from classifiers
    for classifier in classifiers:
        if classifier.startswith("License"):
            text = classifier.split("::")[-1].strip()
            if text and text not in licenses:
                licenses.append(text)

    return licenses


def _extract_upload_time(urls: list[Any]) -> timezone.datetime | None:
    """
    Safely extract upload_time from the first URL entry.

    Args:
        urls: List of URL entries from PyPI JSON

    Returns:
        Parsed upload time or None
    """
    if not urls:
        return None

    first_url = urls[0]
    if not isinstance(first_url, Mapping):
        return None

    upload_time_str = first_url.get("upload_time")
    return _parse_upload_time(upload_time_str)


def _extract_development_status(classifiers: list[str]) -> str | None:
    """
    Extract development status from classifiers.

    Args:
        classifiers: List of trove classifiers

    Returns:
        Development status choice or None
    """
    for classifier in classifiers:
        if classifier.startswith("Development Status"):
            return status_choices_switch(classifier)
    return None


def update_package_from_pypi(
    package: Package,
    *,
    client: PyPIClient | None = None,
    clear_pypi_url_on_404: bool = True,
    save: bool = True,
) -> Package:
    """
    Fetch PyPI JSON metadata for a Package and update Package + Version.

    Returns the updated Package instance on a successful fetch + update, or the original
    Package instance when no fetch occurred or when the project does not exist on PyPI (404).

    Notes:
    - This function may update and save the related Version row.
    - Package is modified in-memory and saved by default.
    - Set save=False to defer persisting package changes.

    Args:
        package: Package model instance to update
        clear_pypi_url_on_404: If True, clear pypi_url when package not found
        save: If True, save the package model after updating

    Returns:
        The updated Package instance on a successful fetch + update, or the original
        Package instance when no fetch occurred or when the project does not exist on PyPI (404).
    """
    from package.models import Version

    pypi_name = package.pypi_name

    if not pypi_name:
        logger.debug("Package has no pypi_name set, skipping PyPI update")
        return package

    client = client or PyPIClient()

    try:
        project = client.fetch_project(pypi_name)
    except HTTPError as exc:
        response = exc.response
        status_code = response.status_code if response is not None else None

        if status_code == 429:
            logger.warning("PyPI rate limit reached for %s", pypi_name)
            raise PyPIRateLimitError("pypi rate limit reached")

        if status_code == 404:
            logger.info("Package %s not found on PyPI (404)", pypi_name)
            if clear_pypi_url_on_404:
                package.pypi_url = ""
                if save:
                    package.save(update_fields=["pypi_url"])
            return package

        logger.exception("PyPI HTTP error for %s (%s): %s", pypi_name, status_code, exc)
        return package
    except RequestException:
        logger.exception("PyPI request failed for %s", pypi_name)
        return package

    info = project.info
    classifiers = project.classifiers

    # Update Package fields
    if classifiers:
        package.pypi_classifiers = classifiers

    requires_python = project.requires_python
    if requires_python:
        package.pypi_requires_python = requires_python

    supports_py3 = _supports_python3(requires_python, classifiers)
    if supports_py3 is not None:
        package.supports_python3 = supports_py3

    if not package.documentation_url:
        docs_url = project.docs_url or _first_documentation_url(project.project_urls)
        if docs_url:
            package.documentation_url = docs_url

    # Prepare Version defaults
    version_number = project.version
    defaults = {}

    # Development status
    dev_status = _extract_development_status(classifiers)
    if dev_status:
        defaults["development_status"] = dev_status

    if supports_py3 is True:
        defaults["supports_python3"] = True

    # License information
    licenses = _extract_license_list(
        info.get("license"), info.get("license_expression"), classifiers
    )

    if licenses:
        defaults["licenses"] = licenses
        defaults["license"] = licenses[0]

    # Upload time
    upload_time = _extract_upload_time(project.urls)
    if upload_time is not None:
        defaults["upload_time"] = upload_time

    # Create or update Version
    version_obj, created = Version.objects.update_or_create(
        package=package,
        number=version_number,
        defaults=defaults,
    )

    if created:
        logger.info("Created new version %s for package %s", version_number, pypi_name)
    else:
        logger.debug("Updated version %s for package %s", version_number, pypi_name)

    # Sync license information back to Package
    if licenses:
        if package.pypi_license != version_obj.license:
            package.pypi_license = version_obj.license

        if package.pypi_licenses != version_obj.licenses:
            package.pypi_licenses = version_obj.licenses

    # Update latest version reference
    package.latest_version = version_obj

    if save:
        package.save()

    return package
