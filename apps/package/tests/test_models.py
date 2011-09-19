from django.test import TestCase

from package.models import Package, Version, versioner
from package.tests import data, initial_data

class VersionTests(TestCase):
    def setUp(self):
        data.load()

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

    def test_version_license_length(self):
        v = Version.objects.all()[0]
        v.license = "x"*50
        v.save()
        self.assertEquals(v.license,"Custom")

class PackageTests(TestCase):
    def setUp(self):
        initial_data.load()

    def test_license_latest(self):
        for p in Package.objects.all():
            self.assertEquals("UNKNOWN", p.license_latest)