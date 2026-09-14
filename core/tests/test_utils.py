import re

import pytest

from core import utils


def test_oc_slugify():
    lst = (
        ("test.this.value", "test-this-value"),
        ("Plone.OpenComparison", "plone-opencomparison"),
        ("Run from here", "run-from-here"),
        ("Jump_the shark", "jump_the-shark"),
    )

    for l in lst:
        assert utils.oc_slugify(l[0]) == l[1]


@pytest.mark.httpx2(assert_all_mocked=False)
def test_get_pypi_url_success(httpx2_mock):
    httpx2_mock.get("https://pypi.org/project/django/").respond(status_code=200)
    httpx2_mock.get("https://pypi.org/project/django-uni-form/").respond(
        status_code=200
    )

    lst = (
        ("django", "https://pypi.org/project/django/"),
        ("Django Uni Form", "https://pypi.org/project/django-uni-form/"),
    )
    for l in lst:
        assert utils.get_pypi_url(l[0].lower()) == l[1].lower()


@pytest.mark.httpx2(assert_all_called=False, assert_all_mocked=False)
def test_get_pypi_url_fail(httpx2_mock):
    httpx2_mock.get(re.compile(r"https://pypi\.org/project/.*")).respond(
        status_code=404
    )

    lst = ("ColdFusion is not here", "php is not here")
    for l in lst:
        assert utils.get_pypi_url(l) is None
