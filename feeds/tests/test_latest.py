from django.test import TestCase
from django.urls import reverse
from package.models import Package

import feedparser

from feeds.tests import data


class LatestFeedsTest(TestCase):
    def setUp(self):
        data.load()

    def test_latest_feeds(self):

        packages = Package.objects.all().order_by('-created')[:15]

        for feed_type in ('rss', 'atom'):
            url = reverse('feeds_latest_packages_%s' % feed_type)
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            feed = feedparser.parse(response.content)

            expect_titles = [p.title for p in packages]
            actual_titles = [e['title'] for e in feed.entries]

            for expected_title, actual_title in zip(expect_titles, actual_titles):
                self.assertEqual(expected_title, actual_title)

            expect_summaries = [p.repo_description for p in packages]
            actual_summaries = [e['summary'] for e in feed.entries]

            for expected_summary, actual_summary in zip(expect_summaries, actual_summaries):
                self.assertEqual(expected_summary, actual_summary)
