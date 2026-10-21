"""What Django removed, and when.

Every entry comes from Django's own documentation: the sections of the
release notes that say a name is removed, and the deprecation timeline
in `docs/internals/deprecation.txt`. Nothing is inferred from whether a
name imports, because that answers a different question. A name can
fail to import and be perfectly alive: `django.contrib.gis` without
GDAL, a database backend whose driver we do not install, an app that is
not in INSTALLED_APPS. We used to call all of those removed, and two in
five of the rows on the page were wrong.

The table is deliberately short. A name nobody can point at a release
note for stays off the page, which is the right trade for a page that
tells package authors their code calls a dead API.

`manage check_removals` reads both documents again and reports what
this table is missing, which is how it gets refreshed when a new
Django lands.
"""

from __future__ import annotations

# Dotted path to the Django version that removed it. An entry covers
# everything under it, so `django.core.urlresolvers` also answers for
# `django.core.urlresolvers.reverse`.
REMOVED_IN: dict[str, str] = {
    # Django 1.4
    "django.contrib.gis.db.backend": "1.4",
    "django.core.context_processors.auth": "1.4",
    "django.db.models.fields.XMLField": "1.4",
    "django.test.simple.run_tests": "1.4",
    "django.utils.translation.get_date_formats": "1.4",
    "django.utils.translation.get_partial_date_formats": "1.4",
    # Django 1.5
    "django.contrib.formtools.utils.form_hmac": "1.5",
    "django.contrib.formtools.utils.security_hash": "1.5",
    "django.core.context_processors.PermLookupDict": "1.5",
    "django.core.context_processors.PermWrapper": "1.5",
    "django.core.servers.basehttp.AdminMediaHandler": "1.5",
    "django.db.models.fields.URLField.verify_exists": "1.5",
    "django.http.CompatCookie": "1.5",
    "django.test.simple.DjangoTestRunner": "1.5",
    # Django 1.6
    "django.conf.urls.defaults": "1.6",
    "django.contrib.databrowse": "1.6",
    "django.contrib.localflavor": "1.6",
    "django.contrib.localflavor.uk": "1.6",
    "django.contrib.markup": "1.6",
    "django.core.cache.backends.memcached.CacheClass": "1.6",
    "django.utils.copycompat": "1.6",
    "django.utils.hashcompat": "1.6",
    "django.utils.itercompat.all": "1.6",
    "django.utils.itercompat.any": "1.6",
    "django.utils.text.truncate_html_words": "1.6",
    "django.utils.text.truncate_words": "1.6",
    # Django 1.7
    "django.contrib.auth.views.password_reset_confirm_uidb36": "1.7",
    "django.utils.encoding.StrAndUnicode": "1.7",
    "django.utils.itercompat.product": "1.7",
    "django.utils.simplejson": "1.7",
    # Django 1.8
    "django.contrib.comments": "1.8",
    "django.db.backend": "1.8",
    "django.db.backends.creation.BaseDatabaseCreation.set_autocommit": "1.8",
    "django.db.close_connection": "1.8",
    "django.db.transaction.is_managed": "1.8",
    "django.db.transaction.managed": "1.8",
    "django.forms.widgets.RadioChoiceInput": "1.8",
    "django.forms.widgets.RadioInput": "1.8",
    "django.middleware.doc.XViewMiddleware": "1.8",
    "django.test._doctest": "1.8",
    "django.test.simple": "1.8",
    "django.test.simple.DjangoTestSuiteRunner": "1.8",
    "django.utils.html.clean_html": "1.8",
    "django.utils.html.fix_ampersands": "1.8",
    "django.views.defaults.shortcut": "1.8",
    # Django 1.9
    "django.contrib.admin.util": "1.9",
    "django.contrib.contenttypes.generic": "1.9",
    "django.contrib.gis.db.backends.util": "1.9",
    "django.contrib.sitemaps.FlatPageSitemap": "1.9",
    "django.core.cache.get_cache": "1.9",
    "django.db.backends.DatabaseValidation.validate_field": "1.9",
    "django.db.backends.util": "1.9",
    "django.db.models.Options.app_label": "1.9",
    "django.db.models.loading": "1.9",
    "django.db.models.query.ValuesListQuerySet": "1.9",
    "django.db.models.query.ValuesQuerySet": "1.9",
    "django.db.models.signals.post_syncdb": "1.9",
    "django.db.models.signals.pre_syncdb": "1.9",
    "django.db.models.sql.where.Constraint": "1.9",
    "django.db.models.sql.where.WhereNode.make_atom": "1.9",
    "django.forms.forms.get_declared_fields": "1.9",
    "django.forms.util": "1.9",
    "django.test.utils.TestTemplateLoader": "1.9",
    "django.utils.datastructures.MergeDict": "1.9",
    "django.utils.datastructures.SortedDict": "1.9",
    "django.utils.dictconfig": "1.9",
    "django.utils.functional.memoize": "1.9",
    "django.utils.importlib": "1.9",
    "django.utils.module_loading.import_by_path": "1.9",
    "django.utils.text.javascript_quote": "1.9",
    "django.utils.tzinfo": "1.9",
    "django.utils.unittest": "1.9",
    # Django 1.10
    "django.conf.urls.patterns": "1.10",
    "django.core.context_processors": "1.10",
    "django.core.management.NoArgsCommand": "1.10",
    "django.core.management.base.NoArgsCommand": "1.10",
    "django.db.models.Field.related": "1.10",
    "django.db.models.SubfieldBase": "1.10",
    "django.db.models.field.subclassing.SubfieldBase": "1.10",
    "django.db.models.sql.aggregates": "1.10",
    "django.forms.Form._has_changed": "1.10",
    "django.template.backends.base.Template.render": "1.10",
    "django.template.loader.BaseLoader": "1.10",
    "django.template.resolve_variable": "1.10",
    "django.utils.checksums": "1.10",
    # Django 2.0
    "django.conf.global_settings.MIDDLEWARE_CLASSES": "2.0",
    "django.contrib.auth.tests.utils.skipIfCustomUser": "2.0",
    "django.contrib.gis.geoip": "2.0",
    "django.contrib.gis.geoip.GeoIP": "2.0",
    "django.core.files.storage.Storage.accessed_time": "2.0",
    "django.core.urlresolvers": "2.0",
    "django.db.backends.base.BaseDatabaseOperations.check_aggregate_support": "2.0",
    "django.db.models.fields.add_lazy_relation": "2.0",
    "django.dispatch.signals.Signal.disconnect": "2.0",
    "django.forms.extras": "2.0",
    "django.template.base.StringOrigin": "2.0",
    "django.template.loader.LoaderOrigin": "2.0",
    "django.template.loaders.base.Loader.supports_recursion": "2.0",
    "django.template.loaders.cached.Loader.supports_recursion": "2.0",
    "django.template.loaders.eggs.Loader": "2.0",
    "django.utils.functional.allow_lazy": "2.0",
    "django.views.i18n.javascript_catalog": "2.0",
    "django.views.i18n.json_catalog": "2.0",
    # Django 2.1
    "django.contrib.auth.views.login": "2.1",
    "django.contrib.auth.views.logout": "2.1",
    "django.contrib.auth.views.password_change": "2.1",
    "django.contrib.auth.views.password_change_done": "2.1",
    "django.contrib.auth.views.password_reset": "2.1",
    "django.contrib.auth.views.password_reset_complete": "2.1",
    "django.contrib.auth.views.password_reset_confirm": "2.1",
    "django.contrib.auth.views.password_reset_done": "2.1",
    "django.db.models.permalink": "2.1",
    "django.test.runner.setup_databases": "2.1",
    "django.utils.translation.string_concat": "2.1",
    # Django 3.0
    "django.contrib.staticfiles.templatetags.static": "3.0",
    "django.contrib.staticfiles.templatetags.staticfiles.static": "3.0",
    "django.db.backends.postgresql_psycopg2": "3.0",
    "django.shortcuts.render_to_response": "3.0",
    "django.test.utils.patch_logger": "3.0",
    "django.test.utils.str_prefix": "3.0",
    "django.utils._os.abspathu": "3.0",
    "django.utils._os.upath": "3.0",
    "django.utils.decorators.ContextDecorator": "3.0",
    "django.utils.decorators.available_attrs": "3.0",
    "django.utils.encoding.python_2_unicode_compatible": "3.0",
    "django.utils.functional.curry": "3.0",
    "django.utils.http.cookie_date": "3.0",
    "django.utils.lru_cache.lru_cache": "3.0",
    "django.utils.safestring.SafeBytes": "3.0",
    "django.utils.six": "3.0",
    # Django 3.1
    "django.contrib.postgres.fields.FloatRangeField": "3.1",
    "django.contrib.postgres.forms.FloatRangeField": "3.1",
    "django.contrib.staticfiles.storage.CachedStaticFilesStorage": "3.1",
    "django.core.paginator.QuerySetPaginator": "3.1",
    "django.utils.timezone.FixedOffset": "3.1",
    # Django 4.0
    "django.conf.urls.url": "4.0",
    "django.contrib.postgres.fields.JSONField": "4.0",
    "django.contrib.postgres.fields.jsonb.KeyTextTransform": "4.0",
    "django.contrib.postgres.fields.jsonb.KeyTransform": "4.0",
    "django.contrib.postgres.forms.JSONField": "4.0",
    "django.db.models.query_utils.InvalidQuery": "4.0",
    "django.utils.encoding.force_text": "4.0",
    "django.utils.encoding.smart_text": "4.0",
    "django.utils.http.is_safe_url": "4.0",
    "django.utils.http.urlquote": "4.0",
    "django.utils.http.urlunquote": "4.0",
    "django.utils.text.unescape_entities": "4.0",
    "django.utils.translation.LANGUAGE_SESSION_KEY": "4.0",
    "django.utils.translation.ugettext": "4.0",
    "django.utils.translation.ugettext_lazy": "4.0",
    "django.utils.translation.ugettext_noop": "4.0",
    "django.utils.translation.ungettext": "4.0",
    # Django 4.1
    "django.core.cache.backends.memcached.MemcachedCache": "4.1",
    # Django 5.0
    "django.contrib.auth.hashers.CryptPasswordHasher": "5.0",
    "django.contrib.gis.admin.GeoModelAdmin": "5.0",
    "django.contrib.gis.admin.OSMGeoAdmin": "5.0",
    "django.contrib.sessions.serializers.PickleSerializer": "5.0",
    "django.utils.baseconv": "5.0",
    "django.utils.datetime_safe": "5.0",
    "django.utils.timezone.utc": "5.0",
    # Django 5.1
    "django.contrib.auth.hashers.SHA1PasswordHasher": "5.1",
    "django.contrib.auth.hashers.UnsaltedMD5PasswordHasher": "5.1",
    "django.contrib.auth.hashers.UnsaltedSHA1PasswordHasher": "5.1",
    "django.contrib.postgres.fields.CICharField": "5.1",
    "django.contrib.postgres.fields.CIEmailField": "5.1",
    "django.contrib.postgres.fields.CIText": "5.1",
    "django.contrib.postgres.fields.CITextField": "5.1",
    "django.core.files.storage.get_storage_class": "5.1",
    # Django 6.0
    "django.contrib.gis.geoip2.GeoIP2.coords": "6.0",
    "django.contrib.gis.geoip2.GeoIP2.open": "6.0",
    "django.db.models.enums.ChoicesMeta": "6.0",
    "django.utils.itercompat": "6.0",
    "django.utils.itercompat.is_iterable": "6.0",
}


def removed_in(symbol: str) -> str:
    """The Django version that removed this name, or "" if it is alive.

    An exact entry wins, then the longest module prefix, so one entry
    for a removed module answers for everything that was inside it.
    """
    if symbol in REMOVED_IN:
        return REMOVED_IN[symbol]

    best = ""
    for name in REMOVED_IN:
        if symbol.startswith(f"{name}.") and len(name) > len(best):
            best = name
    return REMOVED_IN[best] if best else ""
