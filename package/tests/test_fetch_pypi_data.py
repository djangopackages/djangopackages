import json
from pathlib import Path

from model_bakery import baker


def pypi_package(
    author: str | None = None,
    author_email: str | None = None,
    classifiers: list[str] | None = [],
    documentation_url: str | None = None,
    license: str | None = None,
    package_name: str = "example-package",
    requires_python: str = None,
    version: str | None = "1.0.0",
):
    return {
        "info": {
            "author": author,
            "author_email": author_email,
            "bugtrack_url": None,
            "classifiers": classifiers,
            "description": "",
            "description_content_type": "text/markdown",
            "docs_url": None,
            "download_url": "",
            "downloads": {"last_day": -1, "last_month": -1, "last_week": -1},
            "home_page": "",
            "keywords": "",
            "license": license,
            "maintainer": "",
            "maintainer_email": "",
            "name": f"{package_name}",
            "package_url": f"https://pypi.org/project/{package_name}/",
            "platform": "",
            "project_url": f"https://pypi.org/project/{package_name}/",
            "project_urls": {
                "Changelog": None,
                "Documentation": documentation_url,
                "Funding": None,
                "Homepage": None,
                "Source": None,
            },
            "release_url": f"https://pypi.org/project/{package_name}/{version}/",
            "requires_dist": [],
            "requires_python": requires_python,
            "summary": "",
            "version": f"{version}",
            "yanked": False,
            "yanked_reason": None,
        },
        "last_serial": 12314011,
        "releases": {},
        "urls": [
            {
                "downloads": -1,
                "upload_time": "2022-02-01T07:56:23",
            }
        ],
    }


def test_pypi_documentation_url_valid(db, faker, requests_mock):
    package_name = "valid-documentation"
    documentation_url = "https://docs.djangopackages.org/en/latest/"

    package = baker.make(
        "package.Package",
        title=package_name,
        pypi_url=package_name,
        documentation_url=documentation_url,
    )

    pypi_data = pypi_package(
        documentation_url=documentation_url, package_name=package_name
    )

    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.documentation_url == documentation_url


def test_pypi_license_valid(db, faker, requests_mock):
    package_name = "valid-license"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(
        license="BSD License",
        package_name=package_name,
    )
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.license_latest == "UNKNOWN"

    package.fetch_pypi_data()

    assert package.pypi_license == "BSD License"
    assert package.pypi_licenses == ["BSD License"]
    assert package.license_latest == "BSD License"


def test_pypi_license_valid_with_classifiers(db, faker, requests_mock):
    package_name = "valid-license"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(
        classifiers=["License :: OSI Approved :: BSD License"],
        package_name=package_name,
    )
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.license_latest == "UNKNOWN"

    package.fetch_pypi_data()

    assert package.pypi_license == "BSD License"
    assert package.pypi_licenses == ["BSD License"]
    assert package.license_latest == "BSD License"


def test_pypi_license_too_long(db, faker, requests_mock):
    package_name = "license-too-long"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(
        license=faker.paragraph(nb_sentences=5),
        package_name=package_name,
    )
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.license_latest == "UNKNOWN"

    package.fetch_pypi_data()

    assert package.pypi_license == "Custom"
    assert package.pypi_licenses == ["Custom"]
    assert package.license_latest == "Custom"


def test_pypi_development_status_alpha(db, faker, requests_mock):
    package_name = "development-status"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(
        classifiers=[
            "Development Status :: 3 - Alpha",
        ],
        package_name=package_name,
    )
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.development_status is None
    assert package.version_set.exists() is False

    package.fetch_pypi_data()

    assert package.version_set.exists() is True

    assert package.version_set.first().development_status == 3
    assert package.version_set.first().pretty_status == "Alpha"
    assert package.development_status == "Alpha"


def test_pypi_development_status_stable(db, faker, requests_mock):
    package_name = "development-status"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(
        classifiers=[
            "Development Status :: 5 - Production/Stable",
        ],
        package_name=package_name,
    )
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.development_status is None
    assert package.version_set.exists() is False

    package.fetch_pypi_data()

    assert package.version_set.exists() is True
    assert package.last_released()
    assert package.version_set.first().development_status == 5
    assert package.version_set.first().pretty_status == "Production/Stable"
    assert package.development_status == "Production/Stable"


def test_pypi_requires_python(db, faker, requests_mock):
    package_name = "requires-python"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(
        # classifiers=[
        #     "Development Status :: 5 - Production/Stable",
        # ],
        package_name=package_name,
        requires_python=">=3.8",
    )
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.pypi_requires_python is None
    assert package.supports_python3 is None

    package.fetch_pypi_data()

    assert package.pypi_requires_python == ">=3.8"
    assert package.supports_python3


def test_pypi_requires_python_two(db, faker, requests_mock):
    package_name = "requires-python-two"
    package = baker.make("package.Package", title=package_name, pypi_url=package_name)

    pypi_data = pypi_package(package_name=package_name, requires_python="<3")
    requests_mock.get(
        f"https://pypi.org/pypi/{package_name}/json",
        text=json.dumps(pypi_data),
    )

    assert package.pypi_requires_python is None
    assert package.supports_python3 is None

    package.fetch_pypi_data()

    assert package.pypi_requires_python == "<3"
    assert package.supports_python3 is False


def test_django(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/django/json",
        text=Path("package", "tests", "test_data", "pypi-django.json").read_text(),
    )

    package = baker.make("package.Package", title="django", pypi_url="django")
    assert package.get_pypi_json_uri() == "https://pypi.org/pypi/django/json"
    assert package.get_pypi_uri() == "https://pypi.org/project/django/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.documentation_url == ""
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "django"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "django"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status == "Production/Stable"
    assert package.documentation_url == "https://docs.djangoproject.com/"
    assert package.license_latest == "BSD-3-Clause"
    assert len(package.pypi_classifiers) == 17
    assert package.pypi_license == "BSD-3-Clause"
    assert package.pypi_licenses == ["BSD-3-Clause", "BSD License"]
    assert package.pypi_requires_python == ">=3.8"
    assert package.score == 0.0
    assert package.supports_python3 is True
    assert package.version_set.count() == 1


def test_djangorestframework(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/djangorestframework/json",
        text=Path(
            "package", "tests", "test_data", "pypi-djangorestframework.json"
        ).read_text(),
    )

    package = baker.make(
        "package.Package", title="djangorestframework", pypi_url="djangorestframework"
    )
    assert (
        package.get_pypi_json_uri() == "https://pypi.org/pypi/djangorestframework/json"
    )
    assert package.get_pypi_uri() == "https://pypi.org/project/djangorestframework/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.documentation_url == ""
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "djangorestframework"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "djangorestframework"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status == "Production/Stable"
    assert package.documentation_url == ""
    assert package.license_latest == "BSD"
    assert len(package.pypi_classifiers) == 20
    assert package.pypi_license == "BSD"
    assert package.pypi_licenses == ["BSD", "BSD License"]
    assert package.pypi_requires_python == ">=3.6"
    assert package.score == 0.0
    assert package.supports_python3 is True
    assert package.version_set.count() == 1


def test_django_crispy_forms_data(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/django-crispy-forms/json",
        text=Path(
            "package", "tests", "test_data", "pypi-django-crispy-forms.json"
        ).read_text(),
    )

    package = baker.make(
        "package.Package", title="django-crispy-forms", pypi_url="django-crispy-forms"
    )
    assert (
        package.get_pypi_json_uri() == "https://pypi.org/pypi/django-crispy-forms/json"
    )
    assert package.get_pypi_uri() == "https://pypi.org/project/django-crispy-forms/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.documentation_url == ""
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "django-crispy-forms"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "django-crispy-forms"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert len(package.pypi_classifiers) == 17
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status == "Production/Stable"
    assert package.documentation_url == ""
    assert package.license_latest == "MIT"
    assert package.pypi_license == "MIT"
    assert package.pypi_licenses == ["MIT", "MIT License"]
    assert package.pypi_requires_python == ">=3.7"
    assert package.score == 0.0
    assert package.supports_python3 is True
    assert package.version_set.count() == 1


def test_nango_data(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/nango/json",
        text=Path("package", "tests", "test_data", "pypi-nango.json").read_text(),
    )

    package = baker.make("package.Package", title="nango", pypi_url="nango")
    assert package.get_pypi_json_uri() == "https://pypi.org/pypi/nango/json"
    assert package.get_pypi_uri() == "https://pypi.org/project/nango/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.documentation_url == ""
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "nango"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "nango"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert len(package.pypi_classifiers) == 3
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status == "Unknown"
    assert package.documentation_url == ""
    assert package.license_latest == "MIT License"
    assert package.pypi_license == "MIT License"
    assert package.pypi_licenses == ["MIT License"]
    assert package.pypi_requires_python == ">=3.8"
    assert package.score == 0.0
    assert package.supports_python3 is True
    assert package.version_set.count() == 1


def test_django_minify_html_data(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/django-minify-html/json",
        text=Path(
            "package", "tests", "test_data", "pypi-django-minify-html.json"
        ).read_text(),
    )

    package = baker.make(
        "package.Package", title="django-minify-html", pypi_url="django-minify-html"
    )
    assert (
        package.get_pypi_json_uri() == "https://pypi.org/pypi/django-minify-html/json"
    )
    assert package.get_pypi_uri() == "https://pypi.org/project/django-minify-html/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "django-minify-html"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "django-minify-html"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert len(package.pypi_classifiers) == 15
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status == "Production/Stable"
    assert package.license_latest == "MIT"
    assert package.pypi_license == "MIT"
    assert package.pypi_licenses == ["MIT", "MIT License"]
    assert package.pypi_requires_python == ">=3.8"
    assert package.score == 0.0
    assert package.supports_python3 is True
    assert package.version_set.count() == 1


def test_pypi_not_found(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/django-fett/json",
        status_code=404,
        text=Path("package", "tests", "test_data", "pypi-django-fett.json").read_text(),
    )

    package = baker.make("package.Package", title="django-fett", pypi_url="django-fett")
    assert package.get_pypi_json_uri() == "https://pypi.org/pypi/django-fett/json"
    assert package.get_pypi_uri() == "https://pypi.org/project/django-fett/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "django-fett"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "django-fett"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_requires_python is None
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0


def test_wagtail(db, requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/wagtail/json",
        text=Path("package", "tests", "test_data", "pypi-wagtail.json").read_text(),
    )

    package = baker.make("package.Package", title="wagtail", pypi_url="wagtail")
    assert package.get_pypi_json_uri() == "https://pypi.org/pypi/wagtail/json"
    assert package.get_pypi_uri() == "https://pypi.org/project/wagtail/"
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status is None
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == "wagtail"
    assert package.pypi_requires_python is None
    assert package.pypi_url == "wagtail"
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0

    package.fetch_pypi_data()

    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.development_status == "Production/Stable"
    assert package.license_latest == "BSD"
    assert len(package.pypi_classifiers) == 16
    assert package.pypi_license == "BSD"
    assert package.pypi_licenses == ["BSD", "BSD License"]
    assert package.pypi_requires_python == ">=3.7"
    assert package.score == 0.0
    assert package.supports_python3 is True
    assert package.version_set.count() == 1
