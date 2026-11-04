"""`pypi_import`: a PyPI name becomes a filled-in Package, or a reason why not."""

from __future__ import annotations

from unittest.mock import Mock, patch

import httpx2
import pytest
from django.core.management import call_command
from model_bakery import baker

from package import importer
from package.models import Category, Package, PackageTag
from package.pypi import PyPIPackage

pytestmark = pytest.mark.django_db


def pypi_json(name, project_urls=None, **info):
    data = {
        "name": name,
        "version": "1.2.0",
        "summary": f"{name} does things",
        "classifiers": ["Framework :: Django", "Framework :: Django :: 5.2"],
        "requires_python": ">=3.10",
        "project_urls": project_urls
        if project_urls is not None
        else {"Source": f"https://github.com/example/{name}"},
    }
    data.update(info)
    return {"info": data, "urls": [], "releases": {}}


class FakePyPI:
    """Answers `fetch_package` from a dict of canned JSON; 404 otherwise."""

    def __init__(self, projects):
        self.projects = projects

    def fetch_package(self, name):
        if name not in self.projects:
            response = Mock(status_code=404)
            raise httpx2.HTTPStatusError("404", request=Mock(), response=response)
        return PyPIPackage(self.projects[name])


@pytest.fixture()
def apps():
    return Category.objects.get_or_create(slug="apps", defaults={"title": "App"})[0]


@pytest.fixture(autouse=True)
def no_repo_fetch():
    """Repository metadata is the network; stand it in with a stars count."""

    def fetch(package, save=True):
        package.repo_watchers = 7
        package.repo_description = "from the repo"
        return package

    with patch("package.repos.github.GitHubHandler.fetch_metadata", side_effect=fetch):
        yield


class TestRepoUrlFromPyPI:
    def test_source_label_wins_over_homepage(self):
        info = PyPIPackage(
            pypi_json(
                "x",
                project_urls={
                    "Homepage": "https://github.com/example/x-site",
                    "Source": "https://GitHub.com/Example/X/",
                },
            )
        )
        assert importer.repo_url_from_pypi(info) == "https://github.com/example/x"

    def test_any_forge_link_will_do_when_labels_are_odd(self):
        info = PyPIPackage(
            pypi_json(
                "x",
                project_urls={
                    "Homepage": "https://x.example.com",
                    "Bug Tracker": "https://github.com/example/x/issues",
                    "Download": "https://codeberg.org/example/x",
                },
            )
        )
        # The issues page is on the repo but is not the repo; the Codeberg link is.
        assert importer.repo_url_from_pypi(info) == "https://codeberg.org/example/x"

    def test_a_docs_site_is_not_a_repo(self):
        info = PyPIPackage(
            pypi_json("x", project_urls={"Homepage": "https://x.readthedocs.io"})
        )
        assert importer.repo_url_from_pypi(info) is None


class TestImportFromPyPI:
    def test_it_creates_and_fills_in_the_package(self, apps):
        client = FakePyPI({"django-shiny": pypi_json("django-shiny")})

        result = importer.import_from_pypi("Django_Shiny", category=apps, client=client)

        assert result.status == "created"
        package = Package.objects.get(slug="django-shiny")
        assert package.title == "django-shiny"
        assert package.pypi_url == "https://pypi.org/project/django-shiny/"
        assert package.repo_url == "https://github.com/example/django-shiny"
        assert package.category == apps
        assert package.tags == [PackageTag.PYPI_IMPORT]
        # Filled in: PyPI classifiers, repo stars, a version row, a score.
        assert "Framework :: Django :: 5.2" in package.pypi_classifiers
        assert package.repo_watchers == 7
        assert package.version_set.filter(number="1.2.0").exists()
        assert package.last_fetched is not None

    def test_it_does_not_duplicate_by_pypi_name(self, apps):
        baker.make(
            "package.Package",
            slug="old",
            pypi_url="https://pypi.org/project/Old_Thing/",
            repo_url="https://github.com/x/old",
        )
        client = FakePyPI({"old-thing": pypi_json("old-thing")})

        result = importer.import_from_pypi("old-thing", category=apps, client=client)

        assert result.status == "exists"
        assert result.package.slug == "old"
        assert Package.objects.count() == 1

    def test_it_does_not_duplicate_by_repository(self, apps):
        baker.make(
            "package.Package",
            slug="old",
            pypi_url="",
            repo_url="https://github.com/example/renamed",
        )
        client = FakePyPI({"renamed": pypi_json("renamed")})

        result = importer.import_from_pypi("renamed", category=apps, client=client)

        assert result.status == "exists"
        assert Package.objects.count() == 1

    def test_no_repository_link_means_no_package(self, apps):
        client = FakePyPI(
            {
                "lonely": pypi_json(
                    "lonely", project_urls={"Homepage": "https://lonely.dev"}
                )
            }
        )

        result = importer.import_from_pypi("lonely", category=apps, client=client)

        assert result.status == "no_repo"
        assert not Package.objects.exists()

    def test_not_on_pypi(self, apps):
        result = importer.import_from_pypi("ghost", category=apps, client=FakePyPI({}))

        assert result.status == "not_on_pypi"

    def test_dry_run_creates_nothing(self, apps):
        client = FakePyPI({"maybe": pypi_json("maybe")})

        result = importer.import_from_pypi(
            "maybe", category=apps, client=client, dry_run=True
        )

        assert result.status == "dry_run"
        assert "https://github.com/example/maybe" in result.note
        assert not Package.objects.exists()

    def test_a_taken_slug_gets_a_suffix(self, apps):
        baker.make(
            "package.Package",
            slug="twin",
            pypi_url="",
            repo_url="https://github.com/other/twin",
        )
        client = FakePyPI({"twin": pypi_json("twin")})

        result = importer.import_from_pypi("twin", category=apps, client=client)

        assert result.status == "created"
        assert result.package.slug == "twin-2"

    def test_a_repo_host_that_fails_still_leaves_a_package(self, apps):
        client = FakePyPI({"flaky": pypi_json("flaky")})
        with patch(
            "package.repos.github.GitHubHandler.fetch_metadata",
            side_effect=RuntimeError("GitHub is down"),
        ):
            result = importer.import_from_pypi("flaky", category=apps, client=client)

        assert result.status == "created"
        assert result.package.pypi_classifiers


class TestCommand:
    def test_it_imports_the_new_rows_of_a_discovery_csv(self, apps, tmp_path):
        path = tmp_path / "django-7d.csv"
        path.write_text(
            "status,name,pypi_url,package_slug\n"
            "new,fresh-one,https://pypi.org/project/fresh-one/,\n"
            "indexed,old-one,https://pypi.org/project/old-one/,old-one\n"
            "new,fresh-two,https://pypi.org/project/fresh-two/,\n"
        )
        fake = FakePyPI(
            {"fresh-one": pypi_json("fresh-one"), "fresh-two": pypi_json("fresh-two")}
        )
        with patch(
            "package.management.commands.pypi_import.PyPIClient", return_value=fake
        ):
            call_command("pypi_import", "--csv", str(path))

        assert set(Package.objects.values_list("slug", flat=True)) == {
            "fresh-one",
            "fresh-two",
        }

    def test_queue_hands_each_name_to_the_cluster(self, apps):
        with patch("package.management.commands.pypi_import.async_task") as queued:
            call_command("pypi_import", "a", "b", "--queue")

        assert [call.args for call in queued.call_args_list] == [
            ("package.tasks.import_from_pypi_task", "a", "apps"),
            ("package.tasks.import_from_pypi_task", "b", "apps"),
        ]
        assert not Package.objects.exists()

    def test_an_unknown_category_is_refused(self, apps):
        import click

        with pytest.raises(click.BadParameter, match="nope"):
            call_command("pypi_import", "a", "--category", "nope")

    def test_nothing_to_do_is_an_error(self, apps):
        import click

        with pytest.raises(click.UsageError):
            call_command("pypi_import")


class TestTask:
    def test_the_task_imports_one_name(self, apps):
        from package.tasks import import_from_pypi_task

        fake = FakePyPI({"queued": pypi_json("queued")})
        with patch("package.importer.PyPIClient", return_value=fake):
            summary = import_from_pypi_task("queued", "apps")

        assert summary == "queued: created"
        assert Package.objects.filter(slug="queued").exists()
