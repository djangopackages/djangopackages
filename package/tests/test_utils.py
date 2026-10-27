from package.utils import (
    documentation_url_problem,
    maybe_set_documentation_url,
    normalize_license,
    uniquer,
    usable_homepage_url,
    usable_documentation_url,
)


def test_uniquer():
    items = ["apple", "apple", "apple", "banana", "cherry"]
    unique_items = ["apple", "banana", "cherry"]
    assert uniquer(items), unique_items


def test_normalize_license():
    assert normalize_license(None) == "UNKNOWN"
    assert normalize_license("Pow" * 80) == "UNKNOWN"
    assert normalize_license("MIT") == "MIT"
    assert normalize_license("MIT License") == "MIT"
    assert (
        normalize_license("GPL-2.0-only OR LGPL-2.1-or-later")
        == "GPL-2.0-only OR LGPL-2.1-or-later"
    )


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


def test_usable_homepage_url_skips_paths_inside_the_repo():
    repo_url = "https://github.com/tim-schilling/django-probe"

    for path in ("/blob/main/README.md", "/tree/main/docs", "/wiki"):
        assert usable_homepage_url(f"{repo_url}{path}", repo_url=repo_url) is None

    # A different repository is just another README, so it is not
    # documentation either; its wiki or docs folder still is.
    assert (
        usable_homepage_url(
            "https://github.com/tim-schilling/django-probe-docs", repo_url=repo_url
        )
        is None
    )
    assert (
        usable_homepage_url(
            "https://github.com/other/thing/blob/main/README.md", repo_url=repo_url
        )
        is None
    )
    assert (
        usable_homepage_url("https://github.com/other/thing/wiki", repo_url=repo_url)
        == "https://github.com/other/thing/wiki"
    )


def test_documentation_url_problem_names_what_is_wrong():
    repo_url = "https://github.com/tim-schilling/django-probe"
    cases = {
        "": "",
        None: "",
        "https://djangoprobe.org": "",
        "https://django-probe.readthedocs.io/en/latest/": "",
        # Separate things to read inside the repository still count.
        f"{repo_url}/wiki": "",
        f"{repo_url}/tree/main/docs": "",
        "https://github.com/tim-schilling/django-probe-docs/blob/main/guide.md": "",
        # The package page already links these.
        "https://pypi.org/project/django-probe/": "pypi",
        "https://pypi.org/project/django-probe/1.0/": "pypi",
        repo_url: "repo",
        f"{repo_url}/": "repo",
        f"{repo_url}.git": "repo",
        "http://www.github.com/Tim-Schilling/Django-Probe": "repo",
        f"{repo_url}#readme": "repo",
        f"{repo_url}#installation": "repo",
        f"{repo_url}/blob/main/README.md": "readme",
        f"{repo_url}/blob/master/README": "readme",
        f"{repo_url}/raw/main/readme.rst": "readme",
        "https://gitlab.com/bfa/bfa_django/-/blob/master/README.md": "readme",
        # A different bare repository page only shows a README too.
        "https://github.com/eudicots/Cactus": "forge",
        "http://github.com/koenbok/Cactus/": "forge",
        "https://gitlab.com/levit/other.git": "forge",
        "https://codeberg.org/someone/thing": "forge",
        "https://git.sr.ht/~someone/thing": "",
        "https://sr.ht/~someone/thing": "forge",
        # Pages and groups on a forge are not repositories.
        "https://tim-schilling.github.io/django-probe/": "",
        "https://github.com/tim-schilling": "",
    }
    for url, expected in cases.items():
        assert documentation_url_problem(url, repo_url=repo_url) == expected, url

    assert usable_documentation_url(" https://djangoprobe.org ", repo_url=repo_url) == (
        "https://djangoprobe.org"
    )
    assert usable_documentation_url(repo_url, repo_url=repo_url) == ""
    assert usable_documentation_url(None, repo_url=repo_url) == ""


def test_documentation_url_problem_without_a_repo_url():
    assert documentation_url_problem("https://github.com/a/b") == "forge"
    assert documentation_url_problem("https://github.com/a/b/blob/main/README.md") == (
        "readme"
    )
    assert documentation_url_problem("https://a.example.com/docs") == ""


def test_maybe_set_documentation_url_skips_urls_that_do_not_fit(package):
    package.documentation_url = ""
    package.save()

    max_length = package._meta.get_field("documentation_url").max_length
    too_long = "https://example.com/" + "a" * max_length

    assert maybe_set_documentation_url(package, too_long) is False
    assert package.documentation_url == ""


def test_maybe_set_documentation_url_only_fills_blank(package):
    package.documentation_url = ""
    package.repo_url = "https://github.com/tim-schilling/django-probe"
    package.save()

    assert maybe_set_documentation_url(package, "https://djangoprobe.org") is True
    assert package.documentation_url == "https://djangoprobe.org"

    assert maybe_set_documentation_url(package, "https://other.example.com") is False
    assert package.documentation_url == "https://djangoprobe.org"
