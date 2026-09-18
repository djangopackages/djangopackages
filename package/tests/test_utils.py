from package.utils import (
    maybe_set_documentation_url,
    normalize_license,
    uniquer,
    usable_homepage_url,
)


def test_uniquer():
    items = ["apple", "apple", "apple", "banana", "cherry"]
    unique_items = ["apple", "banana", "cherry"]
    assert uniquer(items), unique_items


def test_normalize_license():
    assert normalize_license(None) == "UNKNOWN"
    assert (
        normalize_license(
            """License :: OSI Approved :: MIT License
            """
        )
        == "License :: OSI Approved :: MIT License"
    )
    assert normalize_license("Pow" * 80) == "Custom"
    assert normalize_license("MIT") == "MIT"

    # TODO: fix in #888
    assert normalize_license("GPL-2.0-only OR LGPL-2.1-or-later") == "Custom"


def test_usable_homepage_url():
    repo_url = "https://github.com/tim-schilling/django-probe"
    assert (
        usable_homepage_url("https://djangoprobe.org", repo_url=repo_url)
        == "https://djangoprobe.org"
    )
    assert (
        usable_homepage_url(
            "https://github.com/tim-schilling/django-probe/", repo_url=repo_url
        )
        is None
    )
    assert (
        usable_homepage_url("https://pypi.org/project/django-probe/", repo_url=repo_url)
        is None
    )
    assert usable_homepage_url("", repo_url=repo_url) is None
    assert usable_homepage_url(None, repo_url=repo_url) is None


def test_maybe_set_documentation_url_only_fills_blank(package):
    package.documentation_url = ""
    package.repo_url = "https://github.com/tim-schilling/django-probe"
    package.save()

    assert maybe_set_documentation_url(package, "https://djangoprobe.org") is True
    assert package.documentation_url == "https://djangoprobe.org"

    assert maybe_set_documentation_url(package, "https://other.example.com") is False
    assert package.documentation_url == "https://djangoprobe.org"
