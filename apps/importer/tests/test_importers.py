from django.core.urlresolvers import reverse
from django.test import TestCase

from package.models import Package
from package.tests import data, initial_data
from importer.importers import import_from_github_acct

class ImportPackagesTest(TestCase):  
    
    def setUp(self):
        initial_data.load()

    def test_importer_page_view(self):
        url = reverse('import_github')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
#    def test_import_from_github_acct(self):
#        self.assertEquals(SearchV2.objects.count(), 0)
#        import_from_github_acct()
#        self.assertEquals(SearchV2.objects.count(), 4)