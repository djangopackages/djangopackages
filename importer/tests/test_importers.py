from django.core.urlresolvers import reverse
from django.test import TestCase

from package.tests import initial_data


class ImportPackagesTest(TestCase):

    def setUp(self):
        initial_data.load()

    def test_importer_page_view(self):
        url = reverse('import_github')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
