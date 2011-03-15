from django.test import TestCase

class TestRepoHandlers(TestCase):
    def test_repo_registry(self):
        from package.handlers import get_repo, supported_repos
        g = get_repo("github")
        self.assertEqual(g.title, "Github")
        self.assertEqual(g.url, "https://github.com")

        self.assertTrue("github" in supported_repos())

        self.assertRaises(ImportError, lambda: get_repo("xyzzy"))

    def test_github_pull(self):
        # Currently a live tests that access github
        from package.models import Package
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
