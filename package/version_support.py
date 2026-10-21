"""Work out which Python and Django versions a package claims to support.

Three sources, in descending order of trust:

1. Trove classifiers, which name exact versions and are unambiguous.
2. `requires_python`, a specifier that has to be resolved against the
   versions that actually exist.
3. The Django pin in `requires_dist`, resolved the same way.

The resolving is why this needs the database: a specifier like ">=3.10"
only means something against a list of real releases, and `products.Release`
already tracks those from endoflife.date. Hard-coding the list here would
mean a new Python release silently stopped showing up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from django.utils import timezone
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

EXTRA_MARKER = re.compile(r"""extra\s*==\s*['"]([^'"]+)['"]""")

PYTHON_CLASSIFIER = re.compile(r"^Programming Language :: Python :: (\d+\.\d+)$")
DJANGO_CLASSIFIER = re.compile(r"^Framework :: Django :: (\d+\.\d+)$")


@dataclass(frozen=True)
class VersionSupport:
    """What a package says it runs on, and where we got that from."""

    python: tuple[str, ...] = ()
    django: tuple[str, ...] = ()
    python_source: str = ""
    django_source: str = ""

    @staticmethod
    def _span(versions: tuple[str, ...]) -> str:
        if not versions:
            return ""
        if len(versions) == 1:
            return versions[0]
        return f"{versions[0]} - {versions[-1]}"

    @property
    def python_range(self) -> str:
        return self._span(self.python)

    @property
    def django_range(self) -> str:
        return self._span(self.django)

    def __bool__(self) -> bool:
        return bool(self.python or self.django)


def _sorted(versions) -> tuple[str, ...]:
    def key(v):
        try:
            return Version(v)
        except InvalidVersion:
            return Version("0")

    return tuple(sorted(set(versions), key=key))


@lru_cache(maxsize=2)
def released_cycles(product_slug: str) -> tuple[str, ...]:
    """Version cycles of a product that have actually shipped.

    Unreleased cycles are left out so that resolving ">=3.10" does not
    claim support for a Python that does not exist yet.
    """
    from products.models import Release

    cycles = Release.objects.filter(
        product__slug=product_slug,
        release__isnull=False,
        release__lte=timezone.now().date(),
    ).values_list("cycle", flat=True)

    return _sorted(c for c in cycles if re.fullmatch(r"\d+\.\d+", c or ""))


def _matching(specifier: str, cycles: tuple[str, ...]) -> tuple[str, ...]:
    try:
        spec = SpecifierSet(specifier)
    except InvalidSpecifier:
        return ()
    # prereleases=True so a cycle like "3.14" still matches a specifier
    # written against its alphas.
    return _sorted(c for c in cycles if spec.contains(c, prereleases=True))


def _django_specifier(requires_dist) -> str:
    """The Django pin from a package's real dependencies.

    Dependencies behind an extra do not count. Celery declares
    `Django>=2.2.28; extra == "django"`, which says what its optional
    integration needs, not that Celery is a Django package. Reading
    that as support would put a Django range on half of PyPI.
    """
    for entry in requires_dist or []:
        try:
            requirement = Requirement(entry)
        except InvalidRequirement:
            continue
        if requirement.name.lower().replace("_", "-") != "django":
            continue
        if EXTRA_MARKER.search(str(requirement.marker or "")):
            continue
        return str(requirement.specifier)
    return ""


def version_support(package) -> VersionSupport:
    """Piece together the Python and Django versions a package supports."""
    classifiers = package.pypi_classifiers or []

    python = _sorted(
        m.group(1) for c in classifiers if (m := PYTHON_CLASSIFIER.match(c))
    )
    python_source = "classifiers" if python else ""

    if not python and (requires_python := (package.pypi_requires_python or "").strip()):
        python = _matching(requires_python, released_cycles("python"))
        python_source = "requires_python" if python else ""

    django = _sorted(
        m.group(1) for c in classifiers if (m := DJANGO_CLASSIFIER.match(c))
    )
    django_source = "classifiers" if django else ""

    if not django:
        info = package.pypi_info or {}
        inner = info.get("info") if isinstance(info.get("info"), dict) else info
        if specifier := _django_specifier(inner.get("requires_dist")):
            django = _matching(specifier, released_cycles("django"))
            django_source = "requires_dist" if django else ""

    return VersionSupport(
        python=python,
        django=django,
        python_source=python_source,
        django_source=django_source,
    )


@dataclass(frozen=True)
class Dependency:
    """One entry from requires_dist, pulled apart."""

    name: str
    specifier: str = ""
    extra: str = ""
    marker: str = ""

    @property
    def is_optional(self) -> bool:
        """Whether this only applies to an extra, like `pkg[redis]`."""
        return bool(self.extra)

    def __str__(self) -> str:
        return f"{self.name}{self.specifier}"


def declared_dependencies(package) -> tuple[Dependency, ...]:
    """What a package says it depends on, from its PyPI metadata.

    Only what the latest release declares. It says nothing about what
    the code imports, which is what the AST scan is for: plenty of
    packages import something they never declared, and about half the
    catalogue has no requires_dist at all because the metadata predates
    wheels.

    Dependencies behind an extra are kept and marked rather than
    dropped, since "what does anyone depend on" and "what does a default
    install pull in" are different questions.
    """
    info = package.pypi_info or {}
    inner = info.get("info") if isinstance(info.get("info"), dict) else info

    found: list[Dependency] = []
    for entry in inner.get("requires_dist") or []:
        try:
            requirement = Requirement(entry)
        except InvalidRequirement:
            continue

        marker = str(requirement.marker or "")
        match = EXTRA_MARKER.search(marker)
        found.append(
            Dependency(
                name=requirement.name.lower().replace("_", "-"),
                specifier=str(requirement.specifier),
                extra=match.group(1) if match else "",
                marker=marker,
            )
        )

    return tuple(sorted(found, key=lambda d: (bool(d.extra), d.extra, d.name)))
