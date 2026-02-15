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
from django.db.models import F, FloatField, Q, TextField, Value
from django.db.models.functions import Coalesce, Greatest

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

    All fields are coalesced to `""` so `NULL` values don't break the
    concatenation.
    """
    cfg = config or get_search_config()
    out = TextField()

    return (
        SearchVector(
            Coalesce("title", Value(""), output_field=out), weight="A", config=cfg
        )
        + SearchVector(
            Coalesce("slug", Value(""), output_field=out), weight="B", config=cfg
        )
        + SearchVector(
            Coalesce("description", Value(""), output_field=out), weight="C", config=cfg
        )
        + SearchVector(
            Coalesce("category", Value(""), output_field=out), weight="D", config=cfg
        )
        + SearchVector(
            Coalesce("participants", Value(""), output_field=out),
            weight="D",
            config=cfg,
        )
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
            A `QuerySet` annotated with `rank`, `relevance`, and
            `similarity` fields, filtered to matching rows.
        """
        # normalize input
        q = (q or "").strip()

        if not q:
            return self.none()

        q_len = len(q)

        # resolve settings
        if use_weight_boost is None:
            use_weight_boost = getattr(settings, "SEARCHV3_USE_WEIGHT_BOOST", True)
        if use_fuzzy is None:
            use_fuzzy = getattr(settings, "SEARCHV3_USE_FUZZY", True)

        config = get_search_config()

        # build `tsquery` objects
        fts_query = SearchQuery(q, search_type="websearch", config=config)

        # Prefix query for single-token typeahead (e.g. "djan" → "djan:*").
        prefix_query = None
        if q_len >= 3 and _PREFIX_RE.match(q):
            prefix_query = SearchQuery(f"{q}:*", search_type="raw", config=config)

        # FTS rank
        # `SearchRank` uses the pre-computed, GIN-indexed `search_vector`
        # column — no per-row re-tokenisation happens at query time.
        rank_expr = SearchRank(F("search_vector"), fts_query)
        if prefix_query is not None:
            # Take the better of the two ranks so a prefix hit is never
            # penalised relative to a full websearch hit.
            rank_expr = Greatest(
                rank_expr, SearchRank(F("search_vector"), prefix_query)
            )

        # weight boost
        if use_weight_boost:
            boost_factor = float(getattr(settings, "SEARCHV3_WEIGHT_BOOST", 0.02))
            boost_expr = F("weight") * Value(boost_factor, output_field=FloatField())
        else:
            boost_expr = Value(0.0, output_field=FloatField())

        # Single annotation pass: rank + boost → relevance.
        qs = self.annotate(
            rank=rank_expr,
            relevance=rank_expr + boost_expr,
        )

        # trigram similarity
        if use_fuzzy and q_len >= 3:
            q_lower = q.lower()
            trigram_threshold = float(
                getattr(settings, "SEARCHV3_TRIGRAM_THRESHOLD", 0.2)
            )
            similarity_expr = Greatest(
                TrigramSimilarity("title", q),
                TrigramSimilarity("slug", q_lower),
            )
            trigram_filter = (
                Q(title__trigram_similar=q) | Q(slug__trigram_similar=q_lower)
            ) & Q(similarity__gte=trigram_threshold)
        else:
            similarity_expr = Value(0.0, output_field=FloatField())
            trigram_filter = None

        qs = qs.annotate(similarity=similarity_expr)

        # combine filter conditions with OR
        conditions = Q(search_vector=fts_query)
        if prefix_query is not None:
            conditions |= Q(search_vector=prefix_query)
        if trigram_filter is not None:
            conditions |= trigram_filter

        return qs.filter(conditions).order_by("-relevance", "-similarity", "title")
