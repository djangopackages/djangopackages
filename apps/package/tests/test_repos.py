from django.test import TestCase

from package.repos.launchpad import repo_handler as launchpad_handler
from package.models import Commit, Package


class TestLaunchpadRepo(TestCase):
    def setUp(self):
        self.package = Package.objects.create(
            title="Django-PreFlight",
            slug="django-preflight",
            repo_url="https://code.launchpad.net/~canonical-isd-hackers/django-preflight/trunk")
    
    def test_fetch_commits(self):
        # TODO: mock these so no network access is required
        self.assertEqual(Commit.objects.count(), 0)
        launchpad_handler.fetch_commits(self.package)
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        # TODO: mock these so no network access is required
        p_ret = launchpad_handler.fetch_metadata(self.package)
        self.assertTrue(p_ret.repo_watchers > 0)
        self.assertTrue(p_ret.repo_forks > 0)
        self.assertEqual(p_ret.participants, 'canonical-isd-hackers')


class TestRepoHandlers(TestCase):
    def test_repo_registry(self):
        from package.repos import get_repo, supported_repos

        g = get_repo("github")
        self.assertEqual(g.title, "Github")
        self.assertEqual(g.url, "https://github.com")

        l = get_repo("launchpad")
        self.assertEqual(l.title, "Launchpad")
        self.assertEqual(l.url, "https://code.launchpad.net")

        self.assertTrue("github" in supported_repos())
        self.assertTrue("launchpad" in supported_repos())

        self.assertRaises(ImportError, lambda: get_repo("xyzzy"))

    def test_github_pull(self):
        # Currently a live tests that access github
        p = Package(
            title="Django",
            slug="django",
            repo_url="https://github.com/django/django",
        )
        p.fetch_metadata()
        self.assertEqual(p.repo_description, "Official clone of the Subversion repository.")
        self.assertTrue(p.repo_watchers > 100)

        # test what happens when setting up an unsupported repo
        p.repo_url = "https://example.com"
        p.fetch_metadata()
        self.assertEqual(p.repo_description, "")
        self.assertEqual(p.repo_watchers, 0)
        p.fetch_commits()
