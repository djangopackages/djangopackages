from model_bakery import baker
from pathlib import Path


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
