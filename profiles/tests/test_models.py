from django.test import TestCase


class MockGitHubRepo:
    title = "GitHub"


class TestModel(TestCase):
    def test_profile(self):
        from profiles.models import Profile

        p = Profile()
        self.assertEqual(len(p.my_packages()), 0)

        r = MockGitHubRepo()
        self.assertEqual(p.url_for_repo(r), None)
