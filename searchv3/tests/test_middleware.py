from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag


class SearchVersionMiddlewareTest(TestCase):
    def _resolved_view_module(self, response):
        return response.resolver_match.func.view_class.__module__

    @override_flag("use_searchv3", active=True)
    def test_search_path_uses_searchv3_urls_when_flag_active(self):
        response = self.client.get(reverse("opensearch-description"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._resolved_view_module(response), "searchv3.views")

    # TODO(searchv3): Remove legacy inactive-flag assertion after searchv3 is
    # stable and searchv2 is removed.
    @override_flag("use_searchv3", active=False)
    def test_search_path_uses_searchv2_urls_when_flag_inactive(self):
        response = self.client.get(reverse("opensearch-description"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._resolved_view_module(response), "searchv2.views")

    @override_flag("use_searchv3", active=True)
    def test_non_search_path_uses_default_urlconf(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.view_name, "home")
