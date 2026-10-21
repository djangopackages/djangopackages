"""Work out what a checkout's distribution is imported as.

PyPI's JSON API does not say. The only places the import name is
recorded are the built artefacts, a wheel's top_level.txt or RECORD,
which means downloading and unpacking a wheel per package. The source we
already have on disk answers it nearly as well: a repo's top-level
importable directories are right there, and the one that is not tests or
docs is what the distribution is imported as.
"""

from __future__ import annotations

import re
from pathlib import Path

# Directories that sit beside the real package rather than being it.
NOT_THE_PACKAGE = frozenset(
    {
        "benchmarks",
        "bin",
        "build",
        "ci",
        "contrib",
        "demo",
        "demoproject",
        "dist",
        "doc",
        "docs",
        "example",
        "example_project",
        "examples",
        "migrations",
        "requirements",
        "sample",
        "samples",
        "scripts",
        "setup",
        "site",
        "src",
        "test",
        "testapp",
        "test_app",
        "testing",
        "testproject",
        "test_project",
        "tests",
        "tools",
        "utils",
        "vendor",
    }
)

# Where a project keeps its package, in the order worth looking.
SOURCE_DIRS = ("", "src")

# Modules that live at the root of a repo without being the package. A
# loose .py file here is a script, not something anyone imports.
ROOT_SCRIPTS = frozenset(
    {
        "asgi",
        "conftest",
        "fabfile",
        "hatch_build",
        "manage",
        "noxfile",
        "publish",
        "release",
        "runshell",
        "runtests",
        "run_tests",
        "settings",
        "setup",
        "tasks",
        "urls",
        "versioneer",
        "wsgi",
    }
)

# Prefixes a distribution adds that the import name usually drops:
# django-taggit imports as taggit.
DROPPED_PREFIXES = ("django_", "dj_", "python_", "py_")


def _is_package_dir(entry: Path) -> bool:
    return entry.is_dir() and (entry / "__init__.py").is_file()


def _candidates(directory: Path) -> tuple[list[str], list[str]]:
    """Importable names inside one directory, as (packages, modules).

    Kept apart because a directory with an __init__.py is almost always
    the real thing and a loose module almost never is.
    """
    packages: list[str] = []
    modules: list[str] = []
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return packages, modules

    for entry in entries:
        name = entry.name
        if name.startswith((".", "_")) or name in NOT_THE_PACKAGE:
            continue
        if _is_package_dir(entry):
            packages.append(name)
        elif (
            entry.is_file()
            and name.endswith(".py")
            and name.removesuffix(".py") not in ROOT_SCRIPTS
        ):
            modules.append(name.removesuffix(".py"))
    return packages, modules


def normalize(pypi_name: str) -> str:
    """The import name a naive guess would produce."""
    return (pypi_name or "").strip().lower().replace("-", "_").replace(".", "_")


def canonical_name(pypi_name: str) -> str:
    """PEP 503 distribution name, so Django and django are one row."""
    return re.sub(r"[-_.]+", "-", (pypi_name or "").strip()).lower()


def _rank(name: str, normalized: str) -> tuple[int, str]:
    """How likely a candidate is to be what you import.

    The distribution name is the strongest signal there is, whether it
    matches outright or after the prefix a distribution added for the
    shelf: django-taggit ships taggit, django-ninja ships ninja.
    """
    if name == normalized:
        return 0, name
    stripped = normalized
    for prefix in DROPPED_PREFIXES:
        stripped = stripped.removeprefix(prefix)
    if name == stripped:
        return 1, name
    if normalized.startswith(name) or name.startswith(normalized):
        return 2, name
    if name in normalized or normalized in name:
        return 3, name
    return 4, name


def detect_import_names(root: Path, *, pypi_name: str = "") -> list[str]:
    """Top-level import names a checkout ships, best guess first.

    Directories win over loose modules, and a name that echoes the
    distribution wins over one that does not, so a repo holding both
    ``taggit`` and a ``sample_taggit`` demo reports the one someone
    would import.
    """
    # Candidates from every source directory are pooled and then ranked
    # together. Taking the first directory that held anything would
    # report django-oscar as `sandbox`, because the demo project sits at
    # the root while the package people import lives under src/.
    packages: list[str] = []
    modules: list[str] = []
    for relative in SOURCE_DIRS:
        directory = root / relative if relative else root
        if not directory.is_dir():
            continue
        found_packages, found_modules = _candidates(directory)
        packages += found_packages
        modules += found_modules

    packages = list(dict.fromkeys(packages))
    modules = list(dict.fromkeys(modules))

    normalized = normalize(pypi_name)
    ranked = sorted(packages, key=lambda name: _rank(name, normalized))
    # Modules only ever come after packages, and only when there are no
    # packages at all do they get to be the answer.
    ranked += sorted(modules, key=lambda name: _rank(name, normalized))
    return ranked
