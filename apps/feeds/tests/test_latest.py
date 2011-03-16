from django.test import TestCase
from django.core.urlresolvers import reverse
from package.models import Package

import feedparser

class LatestFeedsTest(TestCase):
    fixtures = ['test_initial_data.json']

    def test_latest_feeds(self):

        packages = Package.objects.all().order_by('-created')[:15]

        for feed_type in ('rss', 'atom'):
            url = reverse('feeds_latest_packages_%s' % feed_type)
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            feed = feedparser.parse(response.content)

            expect_titles = [p.title for p in packages]
            actual_titles = [e['title'] for e in feed.entries]

            for i,j in zip(expect_titles, actual_titles):
                self.assertEqual(i,j)

            expect_summaries = [p.repo_description for p in packages]
            actual_summaries = [e['summary'] for e in feed.entries]

            for i,j in zip(expect_summaries, actual_summaries):
                self.assertEqual(i,j)
