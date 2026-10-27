"""The one-off cleanup for documentation URLs that are not documentation."""

import pytest
from django.core.management import call_command
from model_bakery import baker

from package.models import Package

pytestmark = pytest.mark.django_db


def make(slug, documentation_url, repo_url=None):
    return baker.make(
        Package,
        slug=slug,
        repo_url=repo_url or f"https://github.com/t/{slug}",
        documentation_url=documentation_url,
    )


def test_it_clears_links_back_to_the_repository_and_pypi(capsys):
    make("repo", "https://github.com/t/repo")
    make("readme", "https://github.com/t/readme/blob/main/README.md")
    make("pypi", "https://pypi.org/project/pypi/")
    make("forge", "https://github.com/elsewhere/forge")
    make("site", "https://site.readthedocs.io/")
    make("wiki", "https://github.com/t/wiki/wiki")
    make("blank", "")

    call_command("clean_documentation_urls")

    cleared = set(
        Package.objects.filter(documentation_url="").values_list("slug", flat=True)
    )
    assert cleared == {"repo", "readme", "pypi", "forge", "blank"}
    out = capsys.readouterr().out
    assert "checked 6" in out
    assert "cleared 4" in out


def test_a_dry_run_only_reports(capsys):
    make("repo", "https://github.com/t/repo")

    call_command("clean_documentation_urls", "--dry-run")

    assert Package.objects.get(slug="repo").documentation_url == (
        "https://github.com/t/repo"
    )
    out = capsys.readouterr().out
    assert "would clear 1" in out
    assert "cleared 0" in out
    assert "(dry run)" in out
