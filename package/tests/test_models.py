from django.test import TestCase

from package.models import Package, Version, versioner
from package.tests import data, initial_data

class VersionTests(TestCase):
    def setUp(self):
        data.load()

    def test_ranking(self):
        p = Package.objects.get(slug='django-cms')
        # The packages is not picked up as a Python 3 at this stage
        self.assertNotEqual(p.ranking, p.repo_watchers)
        # we update, Python 3 should be picked up and stars should be equal
        p.save()
        self.assertEqual(p.ranking, p.repo_watchers)

    def test_ranking_abandoned_package(self):
        p = Package.objects.get(slug='django-divioadmin')
        p.save()  # updates the ranking

        # ranking should be -100
        # abandoned for 2 years = loss 10% for each 3 months = 80% of the stars
        # + a -30% for not supporting python 3
        self.assertEqual(p.ranking, -100, p.ranking)

    def test_version_order(self):
        p = Package.objects.get(slug='django-cms')
        versions = p.version_set.by_version()
        expected_values = [ '2.0.0',
                            '2.0.1',
                            '2.0.2',
                            '2.1.0',
                            '2.1.1',
                            '2.1.2',
                            '2.1.3']
        returned_values = [v.number for v in versions]
        self.assertEqual(returned_values,expected_values)

    def test_version_license_length(self):
        v = Version.objects.all()[0]
        v.license = "x"*50
        v.save()
        self.assertEqual(v.license,"Custom")

class PackageTests(TestCase):
    def setUp(self):
        initial_data.load()

    def test_license_latest(self):
        for p in Package.objects.all():
            self.assertEqual("UNKNOWN", p.license_latest)
