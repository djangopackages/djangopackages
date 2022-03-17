import feedparser

from django.urls import reverse

from feeds.tests import data
from package.models import Package


def test_latest_feeds(db, tp):
    data.load()

    packages = Package.objects.all().order_by("-created")[:15]

    for feed_type in ("rss", "atom"):
        url = reverse(f"feeds_latest_packages_{feed_type}")
        response = tp.get(url)

        assert response.status_code == 200

        feed = feedparser.parse(response.content)

        expect_titles = [p.title for p in packages]
        actual_titles = [e["title"] for e in feed.entries]

        for expected_title, actual_title in zip(expect_titles, actual_titles):
            assert expected_title == actual_title

        expect_summaries = [p.repo_description for p in packages]
        actual_summaries = [e["summary"] for e in feed.entries]

        for expected_summary, actual_summary in zip(expect_summaries, actual_summaries):
            assert expected_summary == actual_summary
