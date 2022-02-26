import pytest

from django.test import TestCase

from package.repos import get_repo, get_repo_for_repo_url, supported_repos
from package.repos.base_handler import BaseHandler
from package.repos.unsupported import UnsupportedHandler
from package.repos.bitbucket import BitbucketHandler
from package.repos.github import GitHubHandler
from package.models import Package, Category, Commit


class TestBaseHandler(TestCase):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(title="dummy", slug="dummy")
        self.category.save()
        self.package = Package.objects.create(
            title="Django Piston",
            slug="django-piston",
            repo_url="https://bitbucket.org/jespern/django-piston",
            category=self.category,
        )


def test_base_handler_not_implemented(package):
    handler = BaseHandler()
    assert handler.title == NotImplemented
    assert handler.url == NotImplemented
    assert handler.repo_regex == NotImplemented
    assert handler.slug_regex == NotImplemented
    assert handler.__str__() == NotImplemented
    assert handler.fetch_metadata(package) == NotImplemented
    assert handler.fetch_commits(package) == NotImplemented


def test_base_handler_is_other():
    handler = BaseHandler()
    assert handler.is_other is False


def test_base_handler_get_repo_for_repo_url():
    samples = """u'http://repos.entrouvert.org/authentic.git/tree
http://code.basieproject.org/
http://znc-sistemas.github.com/django-municipios
http://django-brutebuster.googlecode.com/svn/trunk/BruteBuster/
http://hg.piranha.org.ua/byteflow/
http://code.google.com/p/classcomm
http://savannah.nongnu.org/projects/dina-project/
tyrion/django-acl/
izi/django-admin-tools/
bkonkle/django-ajaxcomments/
http://django-ajax-selects.googlecode.com/svn/trunk/
http://django-antivirus.googlecode.com/svn/trunk/
codekoala/django-articles/
https://launchpad.net/django-audit
https://django-audit.googlecode.com/hg/
tyrion/django-autocomplete/
http://code.google.com/p/django-autocomplete/
http://pypi.python.org/pypi/django-autoreports
https://pypi.org/project/django-autoreports/
http://code.google.com/p/django-basic-tumblelog/
schinckel/django-biometrics/
discovery/django-bitly/
bkroeze/django-bursar/src
http://hg.mornie.org/django/c5filemanager/
https://code.launchpad.net/django-cachepurge
http://code.google.com/p/django-campaign/
http://code.google.com/p/django-cas/
http://code.google.com/p/django-chat
http://code.google.com/p/django-compress/
https://launchpad.net/django-configglue
dantario/djelfinder/
ubernostrum/django-contact-form/
http://bitbucket.org/smileychris/django-countries/
http://code.google.com/p/django-courier
http://django-cube.googlecode.com/hg
http://launchpad.net/django-debian
http://pypi.python.org/pypi/django-debug-toolbar-extra
http://code.playfire.com/django-debug-toolbar-user-panel
http://svn.os4d.org/svn/djangodevtools/trunk
http://code.google.com/p/django-dynamic-formset
http://code.google.com/p/django-evolution/
http://pypi.python.org/pypi/django-form-admin
muhuk/django-formfieldset/
http://code.google.com/p/django-forum/
http://code.google.com/p/django-generic-confirmation
http://pypi.python.org/pypi/django-genericforeignkey
https://launchpad.net/django-genshi
http://code.google.com/p/django-gmapi/
http://code.google.com/p/django-ids
http://pypi.python.org/pypi/django-inlinetrans
http://www.github.com/rosarior/django-inventory
codekoala/django-ittybitty/overview
http://bitbucket.org/mrpau/django-jobsboard
http://code.google.com/p/django-jqchat
http://code.google.com/p/djangokit/
http://code.google.com/p/django-ldap-groups/
carljm/django-localeurl/
http://code.google.com/p/django-messages/
robcharlwood/django-mothertongue/
fivethreeo/django-mptt-comments/
http://code.google.com/p/django-multilingual
http://code.google.com/p/django-navbar/
http://code.larlet.fr/django-oauth-plus/wiki/Home
http://django-observer.googlecode.com/svn/trunk/
aaronmader/django-parse_rss/tree/master/parse_rss
http://bitbucket.org/fhahn/django-permission-backend-nonrel
https://code.google.com/p/django-pgsql-interval-field
http://code.google.com/p/django-profile/
lukaszb/django-projector/
http://pypi.python.org/pypi/django-proxy-users
https://bitbucket.org/dias.kev/django-quotidian
nabucosound/django-rbac/
http://djangorestmodel.sourceforge.net/index.html
kmike/django-robokassa/
http://code.google.com/p/django-selectreverse/
http://code.google.com/p/django-simple-newsletter/
http://code.google.com/p/django-simplepages/
http://code.google.com/p/django-simple-wiki
http://pypi.python.org/pypi/django-smart-extends
vgavro/django-smsgate/
schinckel/django-sms-gateway/
http://pypi.python.org/pypi/django-staticmedia
http://opensource.washingtontimes.com/projects/django-supertagging/
http://code.google.com/p/django-tagging-autocomplete
https://source.codetrax.org/hgroot/django-taggit-autocomplete-modified
feuervogel/django-taggit-templatetags/
http://code.google.com/p/django-tasks/
http://code.google.com/p/djangotechblog/
https://launchpad.net/django-testscenarios/
http://django-thumbs.googlecode.com/svn/trunk/
http://code.google.com/p/django-trackback/
http://code.google.com/p/django-transmeta
http://sourceforge.net/projects/django-ui
daks/django-userthemes/
https://django-valuate.googlecode.com/hg
kmike/django-vkontakte-iframe/
http://code.google.com/p/django-voice
http://code.google.com/p/django-wikiapp
cleemesser/django-wsgiserver/
http://code.google.com/p/djapian/
http://code.google.com/p/djfacet
http://code.google.com/p/dojango-datable
http://evennia.googlecode.com/svn/trunk
http://feedjack.googlecode.com/hg
http://code.google.com/p/fullhistory
http://code.google.com/p/goflow
https://launchpad.net/django-jsonfield
https://launchpad.net/linaro-django-xmlrpc/
http://linkexchange.org.ua/browser
http://code.google.com/p/mango-py
http://dev.merengueproject.org/
http://code.google.com/p/django-inoutboard/
http://svn.osqa.net/svnroot/osqa/trunk
http://peach3.nl/trac/
jespern/django-piston/
http://code.google.com/p/django-provinceitaliane/
http://bitbucket.org/kmike/pymorphy
schinckel/django-rest-api/
chris1610/satchmo/
spookylukey/semanticeditor/
http://code.google.com/p/sorethumb/
andrewgodwin/south/
http://source.sphene.net/svn/root/django/communitytools/trunk
http://source.sphene.net/svn/root/django/communitytools
sebpiq/spiteat/
schinckel/django-timedelta-field/
http://projects.unbit.it/hg/uwsgi
http://www.dataportal.it"""
    for sample in samples.split("\n"):
        assert isinstance(get_repo_for_repo_url(sample), UnsupportedHandler)


def test_get_repo_registry(package):
    g = get_repo("github")
    assert g.title == "GitHub"
    assert g.url == "https://github.com"
    assert "github" in supported_repos()
    with pytest.raises(ImportError):
        get_repo("xyzzy")


# TODO: Convert all of these to pytest tests and re-write them since
# they were already commented out.

class TestBitbucketRepo(TestBaseHandler):
    def setUp(self):
        super(TestBitbucketRepo, self).setUp()
        self.package = Package.objects.create(
            category=self.category,
            title="django-mssql",
            slug="django-mssql",
            repo_url="https://bitbucket.org/Manfre/django-mssql/"
        )
        self.bitbucket_handler = BitbucketHandler()

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        self.bitbucket_handler.fetch_commits(self.package)
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        package = self.bitbucket_handler.fetch_metadata(self.package)
        self.assertTrue(
            package.repo_description.startswith("Microsoft SQL server backend for Django running on windows")
        )
        self.assertTrue(package.repo_watchers > 0)
        self.assertTrue(package.repo_forks > 0)
        self.assertEquals(package.participants, "Manfre")


class TestGithubRepo(TestBaseHandler):
    def setUp(self):
        super().setUp()
        self.package = Package.objects.create(
            title="Django",
            slug="django",
            repo_url="https://github.com/django/django",
            category=self.category,
        )
        self.github_handler = GitHubHandler()

        self.invalid_package = Package.objects.create(
            title="Invalid Package",
            slug="invldpkg",
            repo_url="https://example.com",
            category=self.category,
        )

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        self.github_handler.fetch_commits(self.package)
        self.assertTrue(Commit.objects.count() > 0)

    def test_fetch_metadata(self):
        # Currently a live tests that access github
        package = self.github_handler.fetch_metadata(self.package)
        self.assertEqual(package.repo_description, "The Web framework for perfectionists with deadlines.")
        self.assertTrue(package.repo_watchers > 100)

    def test_fetch_metadata_unsupported_repo(self):
        # test what happens when setting up an unsupported repo
        self.package.repo_url = "https://example.com"
        package = self.github_handler.fetch_metadata(self.invalid_package)

        self.assertEqual(package.repo_description, "")
        self.assertEqual(package.repo_watchers, 0)
        self.invalid_package.fetch_commits()
        self.assertEqual(package.commit_set.count(), 0)


class TestGitlabRepo(TestBaseHandler):
    def setUp(self):
        super().setUp()
        self.package = Package.objects.create(
            title="Django",
            slug="django",
            repo_url="https://gitlab.com/delta10/kees",
            category=self.category,
        )


class TestRepos(TestBaseHandler):
    def test_repo_registry(self):
        from package.repos import get_repo, supported_repos

        g = get_repo("github")
        self.assertEqual(g.title, "GitHub")
        self.assertEqual(g.url, "https://github.com")
        self.assertTrue("github" in supported_repos())
        self.assertRaises(ImportError, lambda: get_repo("xyzzy"))
