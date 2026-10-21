"""When Django dropped the things our scans still find in packages.

Django publishes this in its release notes and nowhere a machine can
read, so this table is copied by hand and every entry names the release
that removed the API. Anything we are not sure about is left out: a
blank removal version reads as "we do not know", which is true, while a
guessed one would be a wrong fact on a page people use to judge
packages.

Keys are matched exactly first, then by longest dotted prefix, so a
module that went as a whole covers everything that lived in it without
listing each name. The curated fields on ProbeSymbol win over anything
here; this only fills what nobody has filled in.
"""

from __future__ import annotations

# Dotted path (or module prefix) -> the Django version that removed it.
KNOWN_REMOVALS: dict[str, str] = {
    # Moved to django.urls in 1.10, gone two releases later.
    "django.core.urlresolvers": "2.0",
    # The ugettext family was renamed to gettext in 3.0 and removed in 4.0.
    "django.utils.translation.ugettext": "4.0",
    "django.utils.translation.ugettext_lazy": "4.0",
    "django.utils.translation.ugettext_noop": "4.0",
    "django.utils.translation.ungettext": "4.0",
    "django.utils.translation.ungettext_lazy": "4.0",
    # Replaced by path()/re_path(); url() lasted until 4.0.
    "django.conf.urls.url": "4.0",
    "django.conf.urls.patterns": "1.10",
    "django.conf.urls.include.patterns": "1.10",
    # The Python 2 compatibility shims.
    "django.utils.six": "3.0",
    "django.utils.encoding.force_text": "4.0",
    "django.utils.encoding.smart_text": "4.0",
    "django.utils.encoding.force_unicode": "1.9",
    "django.utils.encoding.smart_unicode": "1.9",
    "django.utils.encoding.python_2_unicode_compatible": "4.0",
    "django.utils.importlib": "1.9",
    # App loading before the app registry.
    "django.db.models.loading": "1.9",
    # Management command API from before argparse.
    "django.core.management.base.NoArgsCommand": "1.10",
    "django.core.management.base.BaseCommand.option_list": "1.10",
    "django.core.management.setup_environ": "1.6",
    # Superseded by atomic().
    "django.db.transaction.commit_on_success": "1.8",
    "django.db.transaction.commit_manually": "1.8",
    "django.db.transaction.autocommit": "1.8",
    # Removed in 3.0 in favour of render().
    "django.shortcuts.render_to_response": "3.0",
    # Moved to django.contrib.contenttypes.fields in 1.7.
    "django.contrib.contenttypes.generic": "1.9",
    # Moved to django.contrib.sites.requests.
    "django.contrib.sites.models.RequestSite": "1.9",
    "django.contrib.sites.models.get_current_site": "1.9",
    # QuerySet internals that stopped being public.
    "django.db.models.query.ValuesListQuerySet": "1.9",
    "django.db.models.query.ValuesQuerySet": "1.9",
    # Moved to django.core.exceptions in 1.8.
    "django.db.models.fields.FieldDoesNotExist": "3.0",
    # Replaced by datetime.timezone.utc.
    "django.utils.timezone.utc": "5.0",
    # Renamed assertQuerySetEqual in 4.2.
    "django.test.TestCase.assertQuerysetEqual": "5.1",
    "django.test.TransactionTestCase.assertQuerysetEqual": "5.1",
}


def removed_in(symbol: str) -> str:
    """The Django version that removed this symbol, or "" if we do not know.

    Exact match first, then the longest module prefix, so
    `django.core.urlresolvers.reverse` picks up the removal of the
    module it lived in without needing its own entry.
    """
    if symbol in KNOWN_REMOVALS:
        return KNOWN_REMOVALS[symbol]

    best = ""
    for prefix in KNOWN_REMOVALS:
        if symbol.startswith(f"{prefix}.") and len(prefix) > len(best):
            best = prefix
    return KNOWN_REMOVALS.get(best, "")
