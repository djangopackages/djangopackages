from package.utils import (
    normalize_license,
    uniquer,
    extract_documentation_url_from_markdown,
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


def test_extract_documentation_url_from_markdown():
    description = """
    To go beyond the basics, [comprehensive documentation is available](https://www.crummy.com/software/BeautifulSoup/bs4/doc/). # Links * [Homepage](https://www.crummy.com/software/BeautifulSoup/bs4/) * [Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) * [Discussion group](https://groups.google.com/group/beautifulsoup/) * [Development](https://code.launchpad.net/beautifulsoup/) * [Bug tracker](https://bugs.launchpad.net/beautifulsoup/) *
    """
    assert (
        extract_documentation_url_from_markdown(description)
        == "https://www.crummy.com/software/BeautifulSoup/bs4/doc/"
    )
