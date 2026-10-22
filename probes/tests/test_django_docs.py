"""What we take from a sentence in Django's documentation."""

from probes.django_docs import names_in

KNOWN = {
    "django.utils.translation.ugettext_lazy",
    "django.db.models.enums.ChoicesMeta",
    "django.conf.global_settings.MIDDLEWARE_CLASSES",
}


class TestReadingABullet:
    def test_a_plain_removal(self):
        assert names_in("* ``django.utils.six`` will be removed.") == [
            "django.utils.six"
        ]

    def test_the_replacement_is_not_removed(self):
        bullet = (
            "* ``django.utils.encoding.force_text()`` will be removed. Use "
            "``force_str()`` instead."
        )

        assert names_in(bullet) == ["django.utils.encoding.force_text"]

    def test_an_argument_going_leaves_the_class(self):
        bullet = (
            "* The ``safe`` parameter of ``django.http.JsonResponse`` will be removed."
        )

        assert names_in(bullet) == []

    def test_support_for_something_leaves_the_thing(self):
        bullet = (
            "* Support for old-style middleware using "
            "``django.contrib.auth.middleware.AuthenticationMiddleware`` "
            "will be removed."
        )

        assert names_in(bullet) == []

    def test_what_lived_in_a_module_is_not_the_module(self):
        bullet = (
            "* The ``remove_tags()`` and ``strip_entities()`` functions in "
            "``django.utils.html`` are removed."
        )

        assert names_in(bullet, KNOWN) == []

    def test_siblings_listed_bare_are_taken(self):
        bullet = (
            "* ``django.utils.translation.ugettext()``, ``ugettext_lazy()`` "
            "will be removed."
        )

        assert names_in(bullet, KNOWN) == [
            "django.utils.translation.ugettext",
            "django.utils.translation.ugettext_lazy",
        ]

    def test_an_alias_goes_and_what_it_pointed_at_stays(self):
        bullet = (
            "* The ``ChoicesMeta`` alias to "
            "``django.db.models.enums.ChoicesType`` will be removed."
        )

        assert names_in(bullet, KNOWN) == ["django.db.models.enums.ChoicesMeta"]

    def test_a_setting_is_found_in_global_settings(self):
        bullet = "* The ``MIDDLEWARE_CLASSES`` setting will be removed."

        assert names_in(bullet, KNOWN) == [
            "django.conf.global_settings.MIDDLEWARE_CLASSES"
        ]

    def test_a_bullet_that_removes_nothing(self):
        bullet = "* ``django.urls.path()`` gains a new argument."

        assert names_in(bullet, KNOWN) == []
