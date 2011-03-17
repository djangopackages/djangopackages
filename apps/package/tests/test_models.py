from django.test import TestCase

from package.models import Package, Version, versioner

class VersionTests(TestCase):

    fixtures = ['apps/package/tests/test_data/versioner_test_fixture.json',
                'apps/package/tests/test_data/versioner_versions_fixture.json']

    def test_version_order(self):
        p = Package.objects.get(slug='django-cms')
        versions = p.version_set.by_version()
        expected_values = [ '2.0.0',
                            '2.0.1',
                            '2.0.2',
                            '2.1.0',
                            '2.1.0.beta3',
                            '2.1.0.rc1',
                            '2.1.0.rc2',
                            '2.1.0.rc3',
                            '2.1.1',
                            '2.1.2',
                            '2.1.3']
        returned_values = [v.number for v in versions]
        self.assertEquals(returned_values,expected_values)
