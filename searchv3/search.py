from __future__ import annotations

import re

from django.conf import settings
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db import models
from django.db.models import F, FloatField, Q, Value
from django.db.models.functions import Cast, Greatest

# Pre-compiled regex for detecting single-token alphanumeric inputs that are
# safe to use as a PostgreSQL `tsquery` prefix (`term:*`).
_PREFIX_RE = re.compile(r"\A[A-Za-z0-9_-]+\Z")


def get_search_config() -> str:
    """Return the PostgreSQL text-search configuration name."""
    return getattr(settings, "SEARCHV3_SEARCH_CONFIG", "english")


def build_search_vector(*, config: str | None = None) -> SearchVector:
    """Build the weighted `SearchVector` expression used for indexing.

    Weight assignments:

    * **A** — `title`  (highest relevance)
    * **B** — `slug`
    * **C** — `description`
    * **D** — `category`, `participants`  (lowest relevance)
    """
    cfg = config or get_search_config()

    return (
        SearchVector("title", weight="A", config=cfg)
        + SearchVector("slug", weight="B", config=cfg)
        + SearchVector("description", weight="C", config=cfg)
        + SearchVector("category", weight="D", config=cfg)
        + SearchVector("participants", weight="D", config=cfg)
    )


class SearchV3QuerySet(models.QuerySet):
    """Custom `QuerySet` with PostgreSQL FTS + trigram search capabilities."""

    def search(
        self,
        q: str,
        *,
        use_weight_boost: bool | None = None,
        use_fuzzy: bool | None = None,
    ):
        """Execute a combined FTS + trigram search and return an ordered queryset.

        The search pipeline consists of four stages, each of which can be
        independently enabled/disabled:

        1. **Websearch query** on the persisted `search_vector` column
           (GIN-indexed).
        2. **Prefix query** (`term:*`) for short, single-token, alphanumeric
           inputs — enables typeahead/autocomplete.  Only used when
           `len(q) >= 3` and the query matches `[A-Za-z0-9_-]+`.
        3. **Weight boost** — adds `weight * boost_factor` to the FTS rank so
           high weight items float to the top.  Controlled by
           `SEARCHV3_USE_WEIGHT_BOOST` and `SEARCHV3_WEIGHT_BOOST`.
        4. **Trigram similarity** on `title` and `slug` for typo tolerance.
           Only kicks in for queries of 3+ characters.  Controlled by
           `SEARCHV3_USE_FUZZY` and `SEARCHV3_TRIGRAM_THRESHOLD`.

        All four conditions are combined with `OR` so a row that matches
        *any* of them is returned.  Results are ordered by
        `(-relevance, -similarity, title)`.

        Args:
            q: The raw search string from the user.
            use_weight_boost: Override the `SEARCHV3_USE_WEIGHT_BOOST` setting.
            use_fuzzy: Override the `SEARCHV3_USE_FUZZY` setting.

        Returns:
            A `QuerySet` annotated with `relevance` and `similarity` fields,
            filtered to matching rows, with `search_vector` deferred.
        """
        # normalize input
        q = (q or "").strip()

        if not q:
            return self.none()

        q_len = len(q)
        q_lower = q.lower()

        # resolve settings
        if use_weight_boost is None:
            use_weight_boost = getattr(settings, "SEARCHV3_USE_WEIGHT_BOOST", True)
        if use_fuzzy is None:
            use_fuzzy = getattr(settings, "SEARCHV3_USE_FUZZY", True)

        config = get_search_config()

        # Use standard websearch query which handles quoted phrases,
        # minus-exclusions, and implicit AND between terms out of the box.
        combined_query = SearchQuery(q, search_type="websearch", config=config)

        # Prefix query for single-token typeahead (e.g. "djan" → "djan:*").
        # Restricted to short inputs (< 6 chars) where the token is likely
        # incomplete; for full words the websearch form already covers stems.
        if q_len >= 3 and q_len < 6 and _PREFIX_RE.match(q):
            combined_query |= SearchQuery(f"{q}:*", search_type="raw", config=config)

        # ts_rank against the stored, GIN-indexed column — PostgreSQL reads
        # the pre-computed tsvector rather than re-tokenising every row.
        rank_expr = SearchRank(F("search_vector"), combined_query)

        # Add weight boost to the rank so high-weight items surface higher in results.
        if use_weight_boost:
            boost_factor = float(getattr(settings, "SEARCHV3_WEIGHT_BOOST", 0.02))
            relevance_expr = rank_expr + (
                Cast(F("weight"), output_field=FloatField())
                * Value(boost_factor, output_field=FloatField())
            )
        else:
            relevance_expr = rank_expr

        qs = self.annotate(relevance=relevance_expr)

        # Trigram similarity for typo tolerance and partial-word matching.
        if use_fuzzy and q_len >= 3:
            trigram_threshold = float(
                getattr(settings, "SEARCHV3_TRIGRAM_THRESHOLD", 0.2)
            )
            # Use the greatest similarity between title and slug so typos in either field can surface results.
            similarity_expr = Greatest(
                TrigramSimilarity("title", q_lower),
                TrigramSimilarity("slug", q_lower),
            )
            trigram_filter = (
                Q(title__trigram_similar=q_lower) | Q(slug__trigram_similar=q_lower)
            ) & Q(similarity__gte=trigram_threshold)
        else:
            similarity_expr = Value(0.0, output_field=FloatField())
            trigram_filter = None

        qs = qs.annotate(similarity=similarity_expr)

        # A row qualifies if it satisfies either the FTS condition or the
        # trigram condition, so results still surface for typos and partial
        # inputs that wouldn't produce a tsquery lexeme at all.
        conditions = Q(search_vector=combined_query)
        if trigram_filter is not None:
            conditions |= trigram_filter

        # We never read search_vector in Python — the @@ operator and ts_rank
        # consume it entirely inside the database — so there's no point
        # pulling it.
        return (
            qs.defer("search_vector")
            .filter(conditions)
            .order_by("-relevance", "-similarity", "title")
        )
