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


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_get_pypi_url_success(httpx_mock):
    httpx_mock.add_response(url="https://pypi.org/project/django/", status_code=200)
    httpx_mock.add_response(
        url="https://pypi.org/project/django-uni-form/", status_code=200
    )

    lst = (
        ("django", "https://pypi.org/project/django/"),
        ("Django Uni Form", "https://pypi.org/project/django-uni-form/"),
    )
    for l in lst:
        assert utils.get_pypi_url(l[0].lower()) == l[1].lower()


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_get_pypi_url_fail(httpx_mock):
    httpx_mock.add_response(
        url="https://pypi.org/project/coldfusion-is-not-here/", status_code=404
    )
    httpx_mock.add_response(
        url="https://pypi.org/project/php-is-not-here/", status_code=404
    )

    lst = ("ColdFusion is not here", "php is not here")
    for l in lst:
        assert utils.get_pypi_url(l) is None
