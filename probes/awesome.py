"""Read an awesome list back and tag the packages it names.

An awesome list is a README full of links. Each link that points at a
repository or a PyPI project we index earns that package a tag named
after the list (`awesome-django`, `awesome-wagtail`, ...), so the site
can ask which listed packages have gone quiet, and the list can ask
which of its entries we have never heard of.

The tag is the list package's slug. Adding a list is a package on the
site with the `awesome-list` tag; nothing here has to learn its name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from package.models import Package, PackageTag
from probes.checkouts import checkout_path
from probes.imports import canonical_name

# Hosts whose first two path segments name a repository.
REPO_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}

_URL = re.compile(r"https?://[^\s<>()\[\]\"']+")
_README_NAMES = ("README.md", "readme.md", "README.rst", "README", "README.txt")


def repo_key(url: str) -> str | None:
    """`https://github.com/Owner/Repo/tree/main` -> `github.com/owner/repo`.

    One spelling per repository, so a link in the list and the URL we
    stored for the package match however either was typed.
    """
    parsed = urlparse((url or "").strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in REPO_HOSTS:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    owner, repo = parts[0].lower(), parts[1].lower().removesuffix(".git")
    return f"{host}/{owner}/{repo}"


def pypi_key(url: str) -> str | None:
    """`https://pypi.org/project/Django-Debug-Toolbar/` -> `django-debug-toolbar`."""
    parsed = urlparse((url or "").strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in {"pypi.org", "pypi.python.org"}:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] in {"project", "pypi"}:
        return canonical_name(parts[1])
    return None


@dataclass
class ListedLinks:
    repos: set[str] = field(default_factory=set)
    pypi: set[str] = field(default_factory=set)

    def __len__(self) -> int:
        return len(self.repos) + len(self.pypi)


def links_in(text: str) -> ListedLinks:
    """Every repository and PyPI project a README links to."""
    found = ListedLinks()
    for raw in _URL.findall(text):
        url = raw.rstrip(".,;:")
        if key := repo_key(url):
            found.repos.add(key)
        elif key := pypi_key(url):
            found.pypi.add(key)
    return found


def readme_for(package) -> Path | None:
    root = checkout_path(package)
    for name in _README_NAMES:
        path = root / name
        if path.is_file():
            return path
    return None


def awesome_lists():
    return Package.objects.filter(tags__contains=[PackageTag.AWESOME_LIST]).order_by(
        "slug"
    )


def package_index():
    """Every package by its repo key and by its PyPI name, read once.

    Six thousand rows is cheaper than six hundred lookups, and the same
    index serves every list in the run.
    """
    by_repo: dict[str, int] = {}
    by_pypi: dict[str, int] = {}
    for pk, repo_url, pypi_url in Package.objects.values_list(
        "pk", "repo_url", "pypi_url"
    ):
        if key := repo_key(repo_url):
            by_repo.setdefault(key, pk)
        if key := pypi_key(pypi_url):
            by_pypi.setdefault(key, pk)
    return by_repo, by_pypi


@dataclass
class TagOutcome:
    tag: str
    links: int = 0  # repository and PyPI links found in the README
    listed: int = 0  # how many of those are packages we index
    added: int = 0
    removed: int = 0
    note: str = ""

    @property
    def ok(self) -> bool:
        return not self.note


def tag_listed_packages(list_package, *, index=None, save: bool = True) -> TagOutcome:
    """Give every package the list names its tag; take it off the rest.

    The tag follows the list: an entry dropped from the README loses the
    tag on the next run, so `tags__contains` always reads as "listed
    today", not "listed once".
    """
    tag = list_package.slug
    outcome = TagOutcome(tag=tag)

    readme = readme_for(list_package)
    if readme is None:
        outcome.note = "no README in checkout"
        return outcome

    links = links_in(readme.read_text(errors="replace"))
    outcome.links = len(links)

    by_repo, by_pypi = index or package_index()
    listed = {by_repo[k] for k in links.repos if k in by_repo}
    listed |= {by_pypi[k] for k in links.pypi if k in by_pypi}
    listed.discard(list_package.pk)
    outcome.listed = len(listed)

    tagged = set(
        Package.objects.filter(tags__contains=[tag]).values_list("pk", flat=True)
    )
    to_add = listed - tagged
    to_remove = tagged - listed
    outcome.added, outcome.removed = len(to_add), len(to_remove)

    if not save:
        return outcome

    for package in Package.objects.filter(pk__in=to_add):
        package.tags = [*package.tags, tag]
        package.save(update_fields=["tags"])
    for package in Package.objects.filter(pk__in=to_remove):
        package.tags = [t for t in package.tags if t != tag]
        package.save(update_fields=["tags"])
    return outcome


def tag_all_lists(*, save: bool = True) -> list[TagOutcome]:
    index = package_index()
    return [
        tag_listed_packages(list_package, index=index, save=save)
        for list_package in awesome_lists()
    ]
