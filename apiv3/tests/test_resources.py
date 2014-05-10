from django.core.urlresolvers import reverse

from apiv3 import resources
from apiv3.tests.data import BaseData


class ResourceTests(BaseData):

    def test_package_resource(self):
        r = resources.package_resource(self.pkg1)
        self.assertEqual(r['last_fetched'], self.now)
        self.assertEqual(r['repo_watchers'], 0)
        self.assertEqual(r['documentation_url'], '')
        self.assertEqual(r['created_by'], None)

    def test_package_resource_created_by(self):
        r = resources.package_resource(self.pkg3)
        self.assertEqual(r['created_by'], reverse("apiv3:user_detail", kwargs={"github_account": "user"}))

    def test_category_resource(self):
        r = resources.category_resource(self.app)
        self.assertEqual(r['description'], "")
        self.assertEqual(r['title'], "App")
        self.assertEqual(r['slug'], "app")
