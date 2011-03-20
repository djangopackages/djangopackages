# TODO: mock these tests so no network access is required

from django.conf import settings
from django.test import TestCase

from package.repos.bitbucket import repo_handler as bitbucket_handler
from package.repos.github import repo_handler as github_handler
from package.repos.launchpad import repo_handler as launchpad_handler
#from package.repos.sourceforge import repo_handler as sourceforge_handler
from package.models import Commit, Package, Category

class BaseBase(TestCase):
    
    def setUp(self):
        
        self.category = Category.objects.create(
            title='dummy',
            slug='dummy'            
        )
        self.category.save()


class TestBitbucketRepo(BaseBase):
    def setUp(self):
        super(TestBitbucketRepo, self).setUp()
        self.package = Package.objects.create(
            title="Django Piston",
            slug="django-piston",
            repo_url="https://bitbucket.org/jespern/django-piston",
            category=self.category
        )


    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        bitbucket_handler.fetch_commits(self.package)
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        package = bitbucket_handler.fetch_metadata(self.package)
        self.assertEqual(package.repo_description,
            "Piston is a Django mini-framework creating APIs.")
        self.assertTrue(package.repo_watchers > 0)
        self.assertTrue(package.repo_forks > 0)
        self.assertTrue(package.participants, "")


class TestGithubRepo(BaseBase):
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
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        # Currently a live tests that access github
        package = github_handler.fetch_metadata(self.package)
        self.assertEqual(package.repo_description, "Official clone of the Subversion repository.")
        self.assertTrue(package.repo_watchers > 100)

        # test what happens when setting up an unsupported repo
        self.package.repo_url = "https://example.com"
        self.package.fetch_metadata()
        self.assertEqual(self.package.repo_description, "")
        self.assertEqual(self.package.repo_watchers, 0)
        self.package.fetch_commits()    


if settings.LAUNCHPAD_ACTIVE:
    class TestLaunchpadRepo(BaseBase):
        def setUp(self):
            super(TestLaunchpadRepo, self).setUp()            
            self.package = Package.objects.create(
                title="Django-PreFlight",
                slug="django-preflight",
                repo_url="https://code.launchpad.net/~canonical-isd-hackers/django-preflight/trunk",
                category=self.category
            )
                
            super(TestGithubRepo, self).setUp(*args, **kwargs)
        
        def test_fetch_commits(self):
            self.assertEqual(Commit.objects.count(), 0)
            launchpad_handler.fetch_commits(self.package)
            self.assertNotEqual(Commit.objects.count(), 0)

        def test_fetch_metadata(self):
            package = launchpad_handler.fetch_metadata(self.package)
            self.assertTrue(package.repo_watchers > 0)
            self.assertTrue(package.repo_forks > 0)
            self.assertEqual(package.participants, 'canonical-isd-hackers')

'''
class TestSourceforgeRepo(TestCase):
    def setUp(self):
        self.package = Package.objects.create(
            title="django-ui",
            slug="django-ui",
            repo_url="http://sourceforge.net/projects/django-ui/",
        )

    def test_fetch_commits(self):
	self.assertEqual(Commit.objects.count(), 0)
	sourceforge_handler.fetch_commits(self.package)
        self.assertEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        package = sourceforge_handler.fetch_metadata(self.package)
        self.assertTrue(package.repo_watchers > 0)
        self.assertTrue(package.repo_forks > 0)
        self.assertEqual(package.participants, '')'''

class TestRepos(BaseBase):
    def test_repo_registry(self):
        from package.repos import get_repo, supported_repos

        g = get_repo("github")
        self.assertEqual(g.title, "Github")
        self.assertEqual(g.url, "https://github.com")
        self.assertTrue("github" in supported_repos())

        if settings.LAUNCHPAD_ACTIVE:
            l = get_repo("launchpad")
            self.assertEqual(l.title, "Launchpad")
            self.assertEqual(l.url, "https://code.launchpad.net")
            self.assertTrue("launchpad" in supported_repos())

        self.assertRaises(ImportError, lambda: get_repo("xyzzy"))
