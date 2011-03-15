from django.test import TestCase

class TestRepoHandlers(TestCase):
    def test_repo_registry(self):
        from package.handlers import get_repo, supported_repos
        g = get_repo("github")
        self.assertEqual(g.title, "Github")
        self.assertEqual(g.url, "https://github.com")

        self.assertTrue("github" in supported_repos())
