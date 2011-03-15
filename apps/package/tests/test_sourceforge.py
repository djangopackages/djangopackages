from django.test import TestCase
from package.repos import sourceforge

class MockPackage(object):
    def __init__(self, home_page):
        self.pypi_home_page = home_page
        
class TestSourceForge(TestCase):
    def test_pull(self):
        package = MockPackage('http://epydoc.sourceforge.net')
        sourceforge.fetch_metadata(package)
        self.assertEqual(package.repo_watchers, 6)
        self.assertEqual(package.repo_url, 'http://epydoc.svn.sourceforge.net/svnroot/epydoc')
