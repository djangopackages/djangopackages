from django.test import TestCase, override_settings
from model_bakery import baker

from searchv3.models import ItemType, SearchV3


class _SearchTestMixin:
    """Helpers shared by all search test classes."""

    @staticmethod
    def _make(title: str, slug: str, **kwargs):
        defaults = {
            "item_type": ItemType.PACKAGE,
            "weight": 0,
            "score": 0,
            "description": "",
        }
        defaults.update(kwargs)
        obj = baker.make(SearchV3, title=title, slug=slug, **defaults)
        return obj


class EmptyQueryTest(_SearchTestMixin, TestCase):
    """Queries that should always return zero results."""

    def test_empty_string(self):
        self.assertEqual(SearchV3.objects.search("").count(), 0)

    def test_whitespace_only(self):
        self.assertEqual(SearchV3.objects.search("   ").count(), 0)

    def test_none_value(self):
        self.assertEqual(SearchV3.objects.search(None).count(), 0)


@override_settings(SEARCHV3_USE_FUZZY=False, SEARCHV3_USE_WEIGHT_BOOST=False)
class FullTextSearchTest(_SearchTestMixin, TestCase):
    """Core full-text matching without fuzzy or weight boost."""

    def test_single_word_match(self):
        self._make("Framework", "framework")
        results = list(SearchV3.objects.search("Framework"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Framework")

    def test_multi_word_match(self):
        self._make("Django REST Framework", "django-rest-framework")
        results = list(SearchV3.objects.search("Django REST"))
        self.assertEqual(len(results), 1)

    def test_description_match(self):
        self._make("Unrelated Title", "unrelated", description="Handles authentication")
        results = list(SearchV3.objects.search("authentication"))
        self.assertEqual(len(results), 1)

    def test_no_match_returns_empty(self):
        self._make("Framework", "framework")
        results = list(SearchV3.objects.search("zzzznonexistent"))
        self.assertEqual(len(results), 0)

    def test_search_vector_populated(self):
        self._make("Framework", "framework")
        obj = SearchV3.objects.get()
        self.assertIsNotNone(obj.search_vector)


@override_settings(SEARCHV3_USE_FUZZY=False, SEARCHV3_USE_WEIGHT_BOOST=False)
class PrefixSearchTest(_SearchTestMixin, TestCase):
    """Prefix / typeahead matching for short single-token inputs."""

    def test_prefix_match_three_chars(self):
        self._make("Serious Testing", "serious-testing")
        results = list(SearchV3.objects.search("ser"))
        titles = [r.title for r in results]
        self.assertIn("Serious Testing", titles)

    def test_two_char_query_returns_list(self):
        self._make("Serious Testing", "serious-testing")
        results = list(SearchV3.objects.search("se"))
        self.assertIsInstance(results, list)


@override_settings(SEARCHV3_USE_FUZZY=False, SEARCHV3_USE_WEIGHT_BOOST=False)
class RankingTest(_SearchTestMixin, TestCase):
    """Title matches should rank above description-only matches."""

    def test_title_match_ranks_above_description(self):
        title_hit = self._make("Framework", "framework-title", description="")
        desc_hit = self._make(
            "Something Else", "framework-desc", description="Framework"
        )
        results = list(SearchV3.objects.search("framework")[:5])
        self.assertEqual(results[0].pk, title_hit.pk)
        result_pks = {r.pk for r in results}
        self.assertTrue({title_hit.pk, desc_hit.pk}.issubset(result_pks))


@override_settings(SEARCHV3_USE_FUZZY=False)
class WeightBoostTest(_SearchTestMixin, TestCase):
    """Weight-boost raises high-weight items in relevance ordering."""

    @override_settings(SEARCHV3_USE_WEIGHT_BOOST=False)
    def test_no_boost_title_wins(self):
        title_hit = self._make("Framework", "framework-title", description="", weight=0)
        self._make(
            "Something Else",
            "framework-desc",
            description="Framework",
            weight=10_000,
        )
        results = list(SearchV3.objects.search("framework")[:2])
        self.assertEqual(results[0].pk, title_hit.pk)

    @override_settings(SEARCHV3_USE_WEIGHT_BOOST=True, SEARCHV3_WEIGHT_BOOST=0.01)
    def test_boost_promotes_high_weight(self):
        self._make("Framework", "framework-title", description="", weight=0)
        heavy = self._make(
            "Something Else",
            "framework-desc",
            description="Framework",
            weight=10_000,
        )
        results = list(SearchV3.objects.search("framework")[:2])
        self.assertEqual(results[0].pk, heavy.pk)

    @override_settings(SEARCHV3_USE_WEIGHT_BOOST=True, SEARCHV3_WEIGHT_BOOST=0.001)
    def test_custom_boost_factor(self):
        title_hit = self._make("Framework", "framework-title", description="", weight=0)
        self._make(
            "Something Else",
            "framework-desc",
            description="Framework",
            weight=100,
        )
        results = list(SearchV3.objects.search("framework")[:2])
        self.assertEqual(results[0].pk, title_hit.pk)


class FuzzySearchTest(_SearchTestMixin, TestCase):
    """Trigram similarity for typo-tolerant matching."""

    @override_settings(
        SEARCHV3_USE_FUZZY=True,
        SEARCHV3_TRIGRAM_THRESHOLD=0.05,
        SEARCHV3_USE_WEIGHT_BOOST=False,
    )
    def test_typo_tolerance(self):
        self._make("Framework", "framework")
        results = list(SearchV3.objects.search("Framewrok")[:5])
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].title, "Framework")

    @override_settings(
        SEARCHV3_USE_FUZZY=True,
        SEARCHV3_TRIGRAM_THRESHOLD=0.05,
        SEARCHV3_USE_WEIGHT_BOOST=False,
    )
    def test_fuzzy_ordered_by_similarity(self):
        better = self._make("Framework", "framework")
        worse = self._make("Frameworks", "frameworks")
        results = list(SearchV3.objects.search("Framewrok")[:2])
        self.assertEqual({r.pk for r in results}, {better.pk, worse.pk})
        self.assertEqual(results[0].pk, better.pk)

    @override_settings(SEARCHV3_USE_FUZZY=False)
    def test_fuzzy_disabled_no_typo_match(self):
        self._make("Framework", "framework")
        results = list(SearchV3.objects.search("Framewrok"))
        self.assertEqual(len(results), 0)


@override_settings(SEARCHV3_USE_FUZZY=False, SEARCHV3_USE_WEIGHT_BOOST=False)
class CategoryAndParticipantsSearchTest(_SearchTestMixin, TestCase):
    """Lower-weighted fields (category, participants) are still searchable."""

    def test_category_match(self):
        self._make(
            "Some Package",
            "some-package",
            category="Authentication",
        )
        results = list(SearchV3.objects.search("Authentication"))
        self.assertGreaterEqual(len(results), 1)

    def test_participants_match(self):
        self._make(
            "Some Package",
            "some-package",
            participants="saadmk11,johndoe",
        )
        results = list(SearchV3.objects.search("saadmk11"))
        self.assertGreaterEqual(len(results), 1)
