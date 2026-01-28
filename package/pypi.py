from __future__ import annotations

from functools import cached_property
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
class PyPIPackage:
    raw: Mapping[str, Any]

    @cached_property
    def info(self) -> Mapping[str, Any]:
        if info := self.raw.get("info"):
            return info
        return {}

    @cached_property
    def urls(self) -> list[Any]:
        if urls := self.raw.get("urls"):
            return urls
        return []

    @cached_property
    def name(self) -> str:
        return self.info.get("name")

    @cached_property
    def version(self) -> str:
        return self.info.get("version")

    @cached_property
    def classifiers(self) -> list[str]:
        classifiers = self.info.get("classifiers")
        if isinstance(classifiers, list):
            return [str(c) for c in classifiers]
        return []

    @cached_property
    def requires_python(self) -> str | None:
        if requires_python := self.info.get("requires_python"):
            return requires_python
        return None

    @cached_property
    def project_urls(self) -> Mapping[str, str]:
        if urls := self.info.get("project_urls"):
            return urls
        return {}

    @cached_property
    def docs_url(self) -> str | None:
        if docs_url := self.info.get("docs_url"):
            return docs_url

        for key in ("Documentation", "Docs", "docs", "documentation"):
            if value := self.project_urls.get(key):
                return value
        return None

    @cached_property
    def supports_python3(self) -> bool | None:
        classifier_says_py3 = any(
            c.startswith("Programming Language :: Python :: 3")
            for c in self.classifiers
        )

        if self.requires_python:
            try:
                spec = SpecifierSet(self.requires_python)
            except InvalidSpecifier:
                # If requires_python is malformed, fall back to classifier check
                logger.warning(
                    "Invalid requires_python specifier: %s. Falling back to classifiers.",
                    self.requires_python,
                )
                return True if classifier_says_py3 else None

            return any(spec.contains(v, prereleases=True) for v in _PY3_PROBE_VERSIONS)

        return True if classifier_says_py3 else None

    @cached_property
    def version_upload_time(self) -> timezone.datetime | None:
        if not self.urls:
            return None

        first_url = self.urls[0]
        upload_time_str = first_url.get("upload_time")
        return _parse_upload_time(upload_time_str)

    @cached_property
    def license_list(self) -> list[str]:
        """
        Extract license information from multiple sources.

        Priority order (as per PEP 639):
        1. license_expression (preferred)
        2. license field (legacy)
        3. classifiers

        Returns:
            List of unique, non-empty license identifiers
        """
        licenses = []
        legacy_license = self.info.get("license")
        license_expression = self.info.get("license_expression")
        classifiers = self.classifiers

        # PEP 639 license_expression takes precedence
        if license_expression:
            text = normalize_license(license_expression)
            if text:  # Ensure non-empty after normalization
                licenses.append(text)

        # Add legacy license field if not already present
        if not licenses and legacy_license:
            text = normalize_license(legacy_license)
            if text and text not in licenses:
                licenses.append(text)

        # Extract from classifiers
        for classifier in classifiers:
            if classifier.startswith("License"):
                text = classifier.split("::")[-1].strip()
                if text and text not in licenses:
                    licenses.append(text)

        return licenses

    @cached_property
    def development_status(self) -> str | None:
        """
        Extract development status from classifiers.

        Returns:
            Development status choice or None
        """
        for classifier in self.classifiers:
            if classifier.startswith("Development Status"):
                return status_choices_switch(classifier)
        return None


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

    def get_package_json_url(self, package_name: str) -> str:
        package_name = package_name.strip().strip("/")
        return f"https://pypi.org/pypi/{package_name}/json"

    def fetch_package(self, package_name: str) -> PyPIPackage:
        url = self.get_package_json_url(package_name)

        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()

        payload = resp.json()

        return PyPIPackage(raw=payload)


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
        pypi_info = client.fetch_package(pypi_name)
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

    # Update Package fields
    if pypi_info.classifiers:
        package.pypi_classifiers = pypi_info.classifiers

    if pypi_info.requires_python:
        package.pypi_requires_python = pypi_info.requires_python

    if pypi_info.supports_python3 is not None:
        package.supports_python3 = pypi_info.supports_python3

    if pypi_info.docs_url:
        package.documentation_url = pypi_info.docs_url

    # Prepare Version defaults
    defaults = {}

    # Development status
    if pypi_info.development_status:
        defaults["development_status"] = pypi_info.development_status

    if package.supports_python3 is True:
        defaults["supports_python3"] = True

    # License information
    licenses = pypi_info.license_list

    if licenses:
        defaults["license"] = licenses[0]
        defaults["licenses"] = licenses

    # Upload time
    if pypi_info.version_upload_time is not None:
        defaults["upload_time"] = pypi_info.version_upload_time

    # Create or update Version
    version_obj, created = Version.objects.update_or_create(
        package=package,
        number=pypi_info.version,
        defaults=defaults,
    )

    if created:
        logger.info(
            "Created new version %s for package %s", pypi_info.version, pypi_name
        )
    else:
        logger.debug("Updated version %s for package %s", pypi_info.version, pypi_name)

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
