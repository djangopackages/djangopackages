from django.core.urlresolvers import reverse
from django.test import TestCase

from importer.importers import import_from_github_acct
from package.models import Package
from package.tests import initial_data


class ImportPackagesTest(TestCase):

    def setUp(self):
        initial_data.load()

    def test_importer_page_view(self):
        url = reverse('import_github')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def working_test_import_from_github_acct(self):
        count = Package.objects.count()
        imported_packages = import_from_github_acct('pydanny', '')