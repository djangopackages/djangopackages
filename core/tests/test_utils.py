from django.test import TestCase

from core import utils


class SlugifyOC(TestCase):

    def test_oc_slugify(self):

        lst = (
            ('test.this.value', 'test-this-value'),
            ('Plone.OpenComparison', 'plone-opencomparison'),
            ('Run from here', 'run-from-here'),
            ('Jump_the shark', 'jump_the-shark'),
            )

        for l in lst:
            self.assertEqual(utils.oc_slugify(l[0]), l[1])


class GetPypiUrl(TestCase):

    def test_get_pypi_url_success(self):

        lst = (
            ('django', 'http://pypi.python.org/pypi/django'),
            ('Django Uni Form', 'http://pypi.python.org/pypi/django-uni-form'),
        )
        for l in lst:
            self.assertEqual(utils.get_pypi_url(l[0].lower()), l[1].lower())

    def test_get_pypi_url_fail(self):

        lst = (
            'ColdFusion is not here',
            'php is not here'
        )
        for l in lst:
            self.assertEqual(utils.get_pypi_url(l), None)
