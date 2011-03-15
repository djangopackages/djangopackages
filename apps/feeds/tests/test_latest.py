from django.test import TestCase
from django.core.urlresolvers import reverse

from package.models import Package


class LatestFeedsTest(TestCase):

    fixtures = ['test_initial_data.json']

    def test_latest_feeds(self):
        url = reverse('feeds_latest_packages_rss')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

