from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from waffle.testutils import override_flag

from package.tests import initial_data
from profiles.models import Profile
from searchv3.builders import build_search_index
from searchv3.models import ItemType, SearchV3


# TODO(searchv3): Remove class-level waffle overrides after searchv3 is the
# only search implementation and searchv2 is removed.
@override_flag("use_searchv3", active=True)
class BuildSearchViewTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

    def test_anonymous_redirected(self):
        url = reverse("build_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_regular_user_forbidden(self):
        self.assertTrue(self.client.login(username="user", password="user"))
        url = reverse("build_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_get_returns_200(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        url = reverse("build_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "searchv3/build_search.html")
        self.assertEqual(SearchV3.objects.count(), 0)

    def test_post_builds_index(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        url = reverse("build_search")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SearchV3.objects.count(), 6)


@override_flag("use_searchv3", active=True)
class SearchSuggestionsViewTest(TestCase):
    def setUp(self):
        initial_data.load()
        build_search_index()
        self.url = reverse("search_suggestions")

    def test_status_code(self):
        response = self.client.get(self.url, {"q": "test"})
        self.assertEqual(response.status_code, 200)

    def test_template_used(self):
        response = self.client.get(self.url, {"q": "test"})
        self.assertTemplateUsed(response, "partials/suggestions.html")

    def test_returns_results_for_matching_query(self):
        response = self.client.get(self.url, {"q": "testability"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["total_count"] > 0)

    def test_no_results_for_nonexistent_query(self):
        response = self.client.get(self.url, {"q": "zzzzznonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 0)

    def test_context_has_required_keys(self):
        response = self.client.get(self.url, {"q": "test"})
        for key in [
            "query",
            "total_count",
            "shown_count",
            "has_more",
            "next_page",
            "dropdown_id",
            "is_load_more",
        ]:
            self.assertIn(key, response.context)

        self.assertEqual(response.context["query"], "test")
        self.assertEqual(response.context["dropdown_id"], "suggestions-dropdown")
        self.assertFalse(response.context["is_load_more"])

    def test_load_more_flag(self):
        response = self.client.get(self.url, {"q": "test", "load_more": "1"})
        self.assertTrue(response.context["is_load_more"])

    def test_custom_dropdown_id(self):
        response = self.client.get(self.url, {"q": "test", "dropdown_id": "custom-id"})
        self.assertEqual(response.context["dropdown_id"], "custom-id")

    def test_empty_query(self):
        response = self.client.get(self.url, {"q": ""})
        self.assertEqual(response.status_code, 200)


@override_flag("use_searchv3", active=True)
class OpenSearchDescriptionTest(TestCase):
    def test_status_code(self):
        url = reverse("opensearch-description")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_type(self):
        url = reverse("opensearch-description")
        response = self.client.get(url)
        self.assertIn("application/opensearchdescription+xml", response["Content-Type"])

    def test_contains_search_url(self):
        url = reverse("opensearch-description")
        response = self.client.get(url)
        self.assertContains(
            response,
            '<Url type="text/html" rel="results" method="get" template="http://testserver/packages/?q={searchTerms}"/>',
        )


@override_flag("use_searchv3", active=True)
class OpenSearchSuggestionsTest(TestCase):
    def test_returns_json(self):
        baker.make(
            SearchV3,
            item_type=ItemType.PACKAGE,
            title="django-uni-form",
            slug="django-uni-form",
        )

        url = reverse("opensearch-suggestions")
        response = self.client.get(url, {"q": "django-uni-form"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0], "django-uni-form")

    def test_empty_query_returns_empty_titles(self):
        url = reverse("opensearch-suggestions")
        response = self.client.get(url, {"q": ""})
        data = response.json()
        self.assertEqual(data[1], [])
