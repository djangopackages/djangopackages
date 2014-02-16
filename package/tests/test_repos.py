import json

from django.test import TestCase

from package.repos import get_repo_for_repo_url
from package.repos.bitbucket import repo_handler as bitbucket_handler
from package.repos.github import repo_handler as github_handler
from package.repos.base_handler import BaseHandler
from package.repos.unsupported import UnsupportedHandler
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

    def test_get_repo_for_repo_url(self):
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
            self.assertTrue(isinstance(get_repo_for_repo_url(sample), UnsupportedHandler))


class TestBitbucketRepo(TestBaseHandler):
    def setUp(self):
        super(TestBitbucketRepo, self).setUp()
        self.package = Package.objects.create(
            title="django",
            slug="django",
            repo_url="https://bitbucket.org/django/django",
            category=self.category
        )

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        bitbucket_handler.fetch_commits(self.package)
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        package = bitbucket_handler.fetch_metadata(self.package)
        self.assertTrue(
            package.repo_description.startswith("Official clone of the Subversion repo")
        )
        self.assertTrue(package.repo_watchers > 0)
        self.assertTrue(package.repo_forks > 0)
        self.assertEquals(package.participants, "django")


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
