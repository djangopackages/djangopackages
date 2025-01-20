from textwrap import dedent

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

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
        results = search_function("ser")
        self.assertEqual(results[0].title, "Serious Testing")


class ViewTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()
        build_1()

    def test_search(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        url = reverse("search") + "?q=django-uni-form"
        data = {"q": "another-test"}
        response = self.client.get(url, data, follow=True)
        self.assertContains(response, "another-test")

    def test_multiple_items(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        SearchV2.objects.get_or_create(
            item_type="package",
            title="django-uni-form",
            slug="django-uni-form",
            slug_no_prefix="uni-form",
            clean_title="django-uni-form",
        )
        url = reverse("search") + "?q=django-uni-form"
        self.client.get(url)
        # print response

    @override_flag("enabled_packages_score_values", active=True)
    def test_search_results_must_include_the_score(self):
        SearchV2.objects.get_or_create(
            item_type="package",
            title="django-uni-form",
            slug="django-uni-form",
            slug_no_prefix="uni-form",
            clean_title="django-uni-form",
            score=600,
        )
        url = reverse("search") + "?q=django-uni-form"
        response = self.client.get(url)

        self.assertContains(
            response,
            dedent(
                """
                    <th
                        data-testid="search-results-score-header"
                        scope="col"
                        data-toggle="tooltip"
                        data-placement="bottom"
                        container="body"
                        aria-label="Score"
                        title="Scores (0-100) are based on Repository stars, with deductions for inactivity (-10% every 3 months) and lack of Python 3 support (-30%)."
                    >
                        Score
                        <span class="glyphicon glyphicon-stats"></span>
                    </th>
                """
            ),
            html=True,
        )

        # Note:
        # This is a test of the Angular template, not the Django template,
        # it's not really testing anything besides that the Django templates
        # does render the expected Angular template.
        self.assertContains(
            response,
            dedent(
                """
                    <td
                        data-testId="{{ TEST_MODE ? 'search-results-' + item.slug + '-score-cell' : null }}"
                        ng-if="item.item_type=='package' && waffle_flag_is_active('enabled_packages_score_values')"
                    >
                        {{ item.score }}
                    </td>
                    <td
                        data-testId="{{ TEST_MODE ? 'search-results-' + item.slug + '-score-cell' : null }}"
                        ng-if="item.item_type=='grid' && waffle_flag_is_active('enabled_packages_score_values')"
                    >
                        N/A
                    </td>
                """
            ),
            html=True,
        )


class SearchDescriptionTest(TestCase):
    def setUp(self):
        pass
        # build_1()

    def test_description(self):
        url = reverse("opensearch-description")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<Url type="text/html" rel="results" method="get" template="http://testserver/search/?q={searchTerms}"/>',
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
