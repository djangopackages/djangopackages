"""A curated list is kept as a checkout even though it is not a package."""

from unittest.mock import patch

import pytest
from model_bakery import baker

from package.models import PackageTag
from probes.checkouts import scannable_packages
from probes.pipeline import check_source

pytestmark = pytest.mark.django_db


def _list(slug="awesome-django", **extra):
    return baker.make(
        "package.Package",
        slug=slug,
        repo_url=f"https://github.com/wsvincent/{slug}",
        pypi_url="",
        score=-40,
        tags=[PackageTag.AWESOME_LIST],
        **extra,
    )


class TestScannablePackages:
    def test_a_tagged_list_is_kept_without_a_release_or_a_score(self):
        _list()
        assert list(scannable_packages().values_list("slug", flat=True)) == [
            "awesome-django"
        ]

    def test_an_untagged_repo_without_a_release_is_still_skipped(self):
        baker.make(
            "package.Package",
            slug="someones-fork",
            repo_url="https://github.com/x/someones-fork",
            pypi_url="",
            score=50,
        )
        assert scannable_packages().count() == 0

    def test_saying_no_still_wins(self):
        _list(probe_wanted=False)
        assert scannable_packages().count() == 0


class TestCheckSource:
    def test_the_repo_answering_is_enough_for_a_list(self):
        package = _list()
        with (
            patch("probes.pipeline.repo_is_reachable", return_value=(True, "")),
            patch("probes.pipeline.pypi_is_published") as pypi,
        ):
            ok, _note = check_source(package)

        assert ok is True
        pypi.assert_not_called()
        package.refresh_from_db()
        assert package.probe is True

    def test_an_ordinary_package_is_still_asked_about_pypi(self):
        package = baker.make(
            "package.Package",
            slug="django-x",
            repo_url="https://github.com/x/django-x",
            pypi_url="https://pypi.org/project/django-x/",
        )
        with (
            patch("probes.pipeline.repo_is_reachable", return_value=(True, "")),
            patch(
                "probes.pipeline.pypi_is_published", return_value=(False, "gone")
            ) as pypi,
        ):
            ok, note = check_source(package)

        pypi.assert_called_once()
        assert (ok, note) == (False, "gone")


class TestTheTag:
    def test_packages_start_with_no_tags(self, package):
        assert package.tags == []
        assert package.is_awesome_list is False

    def test_is_awesome_list_reads_the_tag(self):
        assert _list().is_awesome_list is True


# ---- reading the lists back ------------------------------------------------

from django.core.management import call_command  # noqa: E402

from probes import awesome  # noqa: E402
from probes.tasks import refresh_awesome_lists  # noqa: E402

README = """# Awesome Django

- [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar/) - Debug.
- [django-extensions](https://GitHub.com/django-extensions/django-extensions.git) - Extras.
- [Reactor](https://github.com/edelvalle/reactor/) - LiveView, but for Django.
- [django-nh3](https://pypi.org/project/Django-NH3/) - Sanitiser.
- [the list itself](https://github.com/wsvincent/awesome-django) - meta.
- [Docs](https://docs.djangoproject.com/en/stable/) and (https://github.com/django).
"""


@pytest.fixture
def repo_root(settings, tmp_path):
    settings.PACKAGE_REPO_ROOT = tmp_path
    return tmp_path


def _write_readme(repo_root, list_package, text=README):
    path = repo_root / list_package.slug
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text(text)


def _pkg(slug, repo="", pypi="", **extra):
    return baker.make(
        "package.Package", slug=slug, repo_url=repo, pypi_url=pypi, **extra
    )


class TestLinkKeys:
    @pytest.mark.parametrize(
        ("url", "key"),
        [
            (
                "https://github.com/jazzband/django-debug-toolbar/",
                "github.com/jazzband/django-debug-toolbar",
            ),
            (
                "https://GitHub.com/Jazzband/Django-Debug-Toolbar.git",
                "github.com/jazzband/django-debug-toolbar",
            ),
            ("http://www.github.com/a/b/tree/main/docs", "github.com/a/b"),
            ("https://gitlab.com/a/b", "gitlab.com/a/b"),
            ("https://codeberg.org/trey/bh2", "codeberg.org/trey/bh2"),
            ("https://github.com/django", None),
            ("https://docs.djangoproject.com/en/stable/", None),
        ],
    )
    def test_repo_key(self, url, key):
        assert awesome.repo_key(url) == key

    def test_pypi_key(self):
        assert awesome.pypi_key("https://pypi.org/project/Django_NH3/") == "django-nh3"
        assert awesome.pypi_key("https://pypi.python.org/pypi/x/1.0") == "x"
        assert awesome.pypi_key("https://github.com/a/b") is None

    def test_links_in_a_readme(self):
        links = awesome.links_in(README)
        assert links.repos == {
            "github.com/jazzband/django-debug-toolbar",
            "github.com/django-extensions/django-extensions",
            "github.com/edelvalle/reactor",
            "github.com/wsvincent/awesome-django",
        }
        assert links.pypi == {"django-nh3"}


class TestTagging:
    def test_listed_packages_get_the_tag_and_dropped_ones_lose_it(self, repo_root):
        the_list = _list()
        _write_readme(repo_root, the_list)
        toolbar = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
        )
        extensions = _pkg(
            "django-extensions",
            repo="https://github.com/django-extensions/django-extensions/",
        )
        nh3 = _pkg("django-nh3", pypi="https://pypi.org/project/django-nh3/")
        unlisted = _pkg(
            "django-x", repo="https://github.com/x/django-x", tags=["awesome-django"]
        )

        outcome = awesome.tag_listed_packages(the_list)

        assert (outcome.links, outcome.listed, outcome.added, outcome.removed) == (
            5,
            3,
            3,
            1,
        )
        for p in (toolbar, extensions, nh3):
            p.refresh_from_db()
            assert p.tags == ["awesome-django"]
        unlisted.refresh_from_db()
        assert unlisted.tags == []
        the_list.refresh_from_db()
        assert the_list.tags == ["awesome-list"], "a list does not tag itself"

    def test_other_tags_are_left_alone(self, repo_root):
        the_list = _list()
        _write_readme(repo_root, the_list)
        p = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
            tags=["awesome-wagtail"],
        )

        awesome.tag_listed_packages(the_list)

        p.refresh_from_db()
        assert p.tags == ["awesome-wagtail", "awesome-django"]

    def test_running_twice_changes_nothing(self, repo_root):
        the_list = _list()
        _write_readme(repo_root, the_list)
        _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
        )

        awesome.tag_listed_packages(the_list)
        second = awesome.tag_listed_packages(the_list)

        assert (second.added, second.removed) == (0, 0)

    def test_no_checkout_removes_nothing(self, repo_root):
        the_list = _list()
        p = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
            tags=["awesome-django"],
        )

        outcome = awesome.tag_listed_packages(the_list)

        assert outcome.note == "no README in checkout"
        p.refresh_from_db()
        assert p.tags == ["awesome-django"]

    def test_dry_run_saves_nothing(self, repo_root):
        the_list = _list()
        _write_readme(repo_root, the_list)
        p = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
        )

        outcome = awesome.tag_listed_packages(the_list, save=False)

        assert outcome.added == 1
        p.refresh_from_db()
        assert p.tags == []


class TestCommandAndTask:
    def test_command_tags_every_list(self, repo_root, capsys):
        the_list = _list()
        _write_readme(repo_root, the_list)
        p = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
        )

        call_command("tag_awesome_packages")

        p.refresh_from_db()
        assert p.tags == ["awesome-django"]
        assert "awesome-django" in capsys.readouterr().out

    def test_command_dry_run(self, repo_root):
        the_list = _list()
        _write_readme(repo_root, the_list)
        p = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
        )

        call_command("tag_awesome_packages", "--dry-run")

        p.refresh_from_db()
        assert p.tags == []

    def test_task_syncs_then_tags_and_keeps_tags_when_sync_fails(self, repo_root):
        good = _list()
        bad = _list("awesome-wagtail")
        _write_readme(repo_root, good)
        p = _pkg(
            "django-debug-toolbar",
            repo="https://github.com/jazzband/django-debug-toolbar",
            tags=["awesome-wagtail"],
        )

        def fake_sync(package, **kwargs):
            from probes.pipeline import SyncOutcome

            if package is bad or package.slug == "awesome-wagtail":
                return SyncOutcome("failed", note="git said no")
            return SyncOutcome("updated")

        with patch("probes.tasks.pipeline.sync_package", side_effect=fake_sync):
            report = refresh_awesome_lists()

        assert report["awesome-django"] == "1 listed, +1 -0"
        assert report["awesome-wagtail"] == "failed: git said no"
        p.refresh_from_db()
        assert sorted(p.tags) == ["awesome-django", "awesome-wagtail"]

    def test_the_job_is_scheduled(self):
        from core.management.commands.init_scheduled_jobs import JOBS

        assert JOBS["awesome-lists"]["func"] == "probes.tasks.refresh_awesome_lists"
