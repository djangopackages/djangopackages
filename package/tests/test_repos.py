import json

from django.test import TestCase

from package.repos.bitbucket import repo_handler as bitbucket_handler
from package.repos.github import repo_handler as github_handler
from package.repos.base_handler import BaseHandler
from package.models import Commit, Package, Category


class BaseBase(TestCase):

    def setUp(self):

        self.category = Category.objects.create(
            title='dummy',
            slug='dummy'
        )
        self.category.save()


class TestBaseHandler(BaseBase):
    def setUp(self):
        super(TestBaseHandler, self).setUp()
        self.package = Package.objects.create(
            title="Django Piston",
            slug="django-piston",
            repo_url="https://bitbucket.org/jespern/django-piston",
            category=self.category
        )

    def test_not_implemented(self):
        # TODO switch the NotImplemented to the other side
        handler = BaseHandler()
        self.assertEquals(NotImplemented, handler.title)
        self.assertEquals(NotImplemented, handler.url)
        self.assertEquals(NotImplemented, handler.repo_regex)
        self.assertEquals(NotImplemented, handler.slug_regex)
        self.assertEquals(NotImplemented, handler.__str__())
        self.assertEquals(NotImplemented, handler.fetch_metadata(self.package))
        self.assertEquals(NotImplemented, handler.fetch_commits(self.package))

    def test_is_other(self):
        handler = BaseHandler()
        self.assertEquals(handler.is_other, False)


class TestBitbucketRepo(TestBaseHandler):
    def setUp(self):
        super(TestBitbucketRepo, self).setUp()
        self.package = Package.objects.create(
            title="Python packaging guide",
            slug="python-packaging-user-guide",
            repo_url="https://bitbucket.org/pypa/python-packaging-user-guide",
            category=self.category
        )

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        bitbucket_handler.fetch_commits(self.package)
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        package = bitbucket_handler.fetch_metadata(self.package)
        self.assertEqual(package.repo_description,
            "Python Packaging User Guide")
        self.assertTrue(package.repo_watchers > 0)
        self.assertTrue(package.repo_forks > 0)
        self.assertEquals(package.participants, "pypa")


class TestGithubRepo(TestBaseHandler):
    def setUp(self):
        super(TestGithubRepo, self).setUp()
        self.package = Package.objects.create(
            title="Django",
            slug="django",
            repo_url="https://github.com/django/django",
            category=self.category
        )

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        github_handler.fetch_commits(self.package)
        #commit_list = "[%s]" % self.package.commits_over_52()
        #commit_list = json.loads(commit_list)
        self.assertTrue(Commit.objects.count() > 0)

    def test_fetch_metadata(self):
        # Currently a live tests that access github
        package = github_handler.fetch_metadata(self.package)
        self.assertEqual(package.repo_description, "The Web framework for perfectionists with deadlines.")
        self.assertTrue(package.repo_watchers > 100)

        # test what happens when setting up an unsupported repo
        self.package.repo_url = "https://example.com"
        self.package.fetch_metadata()
        self.assertEqual(self.package.repo_description, "")
        self.assertEqual(self.package.repo_watchers, 0)
        self.package.fetch_commits()


class TestRepos(BaseBase):
    def test_repo_registry(self):
        from package.repos import get_repo, supported_repos

        g = get_repo("github")
        self.assertEqual(g.title, "Github")
        self.assertEqual(g.url, "https://github.com")
        self.assertTrue("github" in supported_repos())
        self.assertRaises(ImportError, lambda: get_repo("xyzzy"))
