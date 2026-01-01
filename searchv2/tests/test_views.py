from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from package.tests import initial_data
from profiles.models import Profile
from searchv2.builders import build_1
from searchv2.models import SearchV2
from searchv2.views import search_function


class FunctionalPackageTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

    def test_build_search(self):
        count = SearchV2.objects.count()
        url = reverse("build_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(count, 0)

        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SearchV2.objects.count(), 0)

        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SearchV2.objects.count(), 0)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SearchV2.objects.count(), 6)

    def test_search_function(self):
        build_1()
        results_1 = search_function("ser")
        results_2 = search_function("wax")
        self.assertEqual(results_1[0].title, "Serious Testing")
        self.assertEqual(
            results_2[0].description, "Make testing as painless as waxing your legs."
        )


class SearchDescriptionTest(TestCase):
    def test_description(self):
        url = reverse("opensearch-description")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<Url type="text/html" rel="results" method="get" template="http://testserver/packages/?q={searchTerms}"/>',
        )

    def test_suggestions(self):
        SearchV2.objects.get_or_create(
            item_type="package",
            title="django-uni-form",
            slug="django-uni-form",
            slug_no_prefix="uni-form",
            clean_title="django-uni-form",
        )
        url = reverse("opensearch-suggestions") + "?q=django-uni-form"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '["django-uni-form"]')


class TestSearchSuggestionsView(TestCase):
    def setUp(self):
        initial_data.load()
        build_1()
        self.url = reverse("search_suggestions")

    def test_view_status_code(self):
        response = self.client.get(self.url, {"q": "test"})
        self.assertEqual(response.status_code, 200)

    def test_view_template_used(self):
        response = self.client.get(self.url, {"q": "test"})
        self.assertTemplateUsed(response, "new/partials/suggestions.html")

    def test_search_results(self):
        response = self.client.get(self.url, {"q": "testability"})
        self.assertContains(response, "testability")
        self.assertTrue(len(response.context["search_results"]) > 0)

    def test_no_results(self):
        response = self.client.get(self.url, {"q": "nonexistentpackage"})
        self.assertNotContains(response, "testability")
        self.assertEqual(len(response.context["search_results"]), 0)

    def test_context_data(self):
        response = self.client.get(self.url, {"q": "test"})
        self.assertIn("query", response.context)
        self.assertIn("total_count", response.context)
        self.assertIn("shown_count", response.context)
        self.assertIn("has_more", response.context)
        self.assertIn("next_page", response.context)
        self.assertIn("dropdown_id", response.context)
        self.assertIn("is_load_more", response.context)

        self.assertEqual(response.context["query"], "test")
        self.assertEqual(response.context["dropdown_id"], "suggestions-dropdown")
        self.assertFalse(response.context["is_load_more"])
