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


def test_get_pypi_url_success(requests_mock):
    requests_mock.get("https://pypi.org/project/django/", status_code=200)
    requests_mock.get("https://pypi.org/project/django-uni-form/", status_code=200)
    requests_mock.get("https://pypi.org/project/Django Uni Form/", status_code=404)
    lst = (
        ("django", "https://pypi.org/project/django/"),
        ("Django Uni Form", "https://pypi.org/project/django-uni-form/"),
    )
    for l in lst:
        assert utils.get_pypi_url(l[0].lower()) == l[1].lower()


def test_get_pypi_url_fail(requests_mock):
    requests_mock.get(
        "https://pypi.org/project/Coldfusion%20Is%20Not%20Here/", status_code=404
    )
    requests_mock.get(
        "https://pypi.org/project/coldfusion-is-not-here/", status_code=404
    )
    requests_mock.get(
        "https://pypi.org/project/php%20is%20not%20here/", status_code=404
    )
    requests_mock.get("https://pypi.org/project/php-is-not-here/", status_code=404)

    lst = ("ColdFusion is not here", "php is not here")
    for l in lst:
        assert utils.get_pypi_url(l) is None
