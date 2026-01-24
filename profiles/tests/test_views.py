from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.tests.data import STOCK_PASSWORD
from favorites.models import Favorite
from package.models import Category, Package
from profiles.models import ExtraField, Profile


class ProfileViewsTestCase(TestCase):
    def create_user_with_profile(
        self,
        *,
        username: str,
        email: str | None = None,
        github_account: str | None = None,
        is_active: bool = True,
    ) -> tuple[User, Profile]:
        user = User.objects.create_user(
            username=username,
            password=STOCK_PASSWORD,
            email=email or f"{username}@example.com",
        )
        user.is_active = is_active
        user.save()

        profile = Profile.objects.create(
            user=user,
            github_account=github_account if github_account is not None else username,
        )
        return user, profile

    def create_category(self, *, slug: str = "test", title: str = "Test") -> Category:
        return Category.objects.create(title=title, slug=slug)

    def create_package(self, *, category: Category, slug: str, title: str) -> Package:
        return Package.objects.create(
            title=title,
            slug=slug,
            category=category,
            repo_url=f"https://example.com/{slug}",
        )

    def login(self, user: User) -> None:
        ok = self.client.login(username=user.username, password=STOCK_PASSWORD)
        self.assertTrue(ok)


class TestProfileDetailView(ProfileViewsTestCase):
    def test_detail_renders_for_anonymous(self):
        _, profile = self.create_user_with_profile(username="user")
        url = reverse(
            "profile_detail", kwargs={"github_account": profile.github_account}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/profile_detail.html")
        self.assertIn("profile", response.context)
        self.assertFalse(response.context["self_profile"])

    def test_detail_sets_self_profile_true_for_owner(self):
        user, profile = self.create_user_with_profile(username="owner")
        self.login(user)

        url = reverse(
            "profile_detail", kwargs={"github_account": profile.github_account}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["self_profile"])
        self.assertEqual(response.context["profile"].pk, profile.pk)
        self.assertEqual(response.context["user"].pk, user.pk)

    def test_detail_sets_self_profile_false_for_other_user(self):
        owner, profile = self.create_user_with_profile(username="owner2")
        other, _ = self.create_user_with_profile(username="other2")
        self.login(other)

        url = reverse(
            "profile_detail", kwargs={"github_account": profile.github_account}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["self_profile"])
        self.assertEqual(response.context["profile"].user, owner)

    def test_detail_includes_extra_fields(self):
        _, profile = self.create_user_with_profile(username="extras")
        ExtraField.objects.create(
            profile=profile, label="Site", url="https://example.com"
        )
        ExtraField.objects.create(
            profile=profile, label="Blog", url="https://blog.example.com"
        )

        url = reverse(
            "profile_detail", kwargs={"github_account": profile.github_account}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        extra_fields = list(response.context["extra_fields"])
        self.assertEqual(len(extra_fields), 2)

    def test_detail_404_when_profile_missing(self):
        url = reverse("profile_detail", kwargs={"github_account": "does-not-exist"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_when_duplicate_github_accounts_returns_latest(self):
        _, profile1 = self.create_user_with_profile(
            username="u1", github_account="dupe"
        )
        _, profile2 = self.create_user_with_profile(
            username="u2", github_account="dupe"
        )

        url = reverse("profile_detail", kwargs={"github_account": "dupe"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["profile"].pk, profile2.pk)
        self.assertNotEqual(profile1.pk, profile2.pk)


class TestProfileUpdateView(ProfileViewsTestCase):
    def test_edit_redirects_when_not_logged_in(self):
        url = reverse("profile_edit")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_renders_and_includes_extra_field_context(self):
        user, profile = self.create_user_with_profile(username="editor")
        ExtraField.objects.create(
            profile=profile, label="One", url="https://one.example.com"
        )
        ExtraField.objects.create(
            profile=profile, label="Two", url="https://two.example.com"
        )

        self.login(user)
        url = reverse("profile_edit")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/profile_edit.html")
        self.assertIn("extra_fields_data", response.context)
        self.assertEqual(len(response.context["extra_fields_data"]), 2)
        self.assertIn("extra_field_form", response.context)

    def test_edit_post_updates_profile_and_redirects_to_detail_with_message(self):
        user, profile = self.create_user_with_profile(username="editor2")
        self.login(user)

        url = reverse("profile_edit")
        data = {
            "bitbucket_url": "bb-user",
            "gitlab_url": "gl-user",
            "share_favorites": True,
        }
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.bitbucket_url, "bb-user")
        self.assertEqual(profile.gitlab_url, "gl-user")
        self.assertTrue(profile.share_favorites)

        expected_detail_url = reverse(
            "profile_detail", kwargs={"github_account": profile.github_account}
        )
        self.assertRedirects(response, expected_detail_url)


class TestLogoutView(ProfileViewsTestCase):
    def test_logout_logs_out_and_redirects_home(self):
        user, _ = self.create_user_with_profile(username="logoutme")
        self.login(user)

        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_works_for_anonymous(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))


class TestProfileContributedPackagesView(ProfileViewsTestCase):
    def setUp(self):
        super().setUp()
        self.user, self.profile = self.create_user_with_profile(username="contrib")
        self.url = reverse(
            "profile_contributed_packages",
            kwargs={"github_account": self.profile.github_account},
        )
        self.category = self.create_category(slug="cat", title="Cat")
        self.pkg1 = self.create_package(
            category=self.category, slug="pkg-1", title="Pkg 1"
        )
        self.pkg2 = self.create_package(
            category=self.category, slug="pkg-2", title="Pkg 2"
        )

    @patch("profiles.models.Profile.my_packages")
    def test_view_renders_card_template_by_default(self, my_packages):
        my_packages.return_value = [self.pkg1, self.pkg2]
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/profile_packages_card.html")
        self.assertEqual(response.context["profile"].pk, self.profile.pk)
        self.assertEqual(list(response.context["packages"]), [self.pkg1, self.pkg2])
        self.assertEqual(response.context["htmx_url"], "profile_contributed_packages")
        self.assertEqual(
            response.context["target_id"], "contributed-packages-table-container"
        )

    @patch("profiles.models.Profile.my_packages")
    def test_htmx_view_renders_table_template(self, my_packages):
        my_packages.return_value = [self.pkg1]
        response = self.client.get(
            self.url,
            headers={"HX-Target": "contributed-packages-table-container"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/profile_packages_table.html")


class TestProfileFavoritePackagesView(ProfileViewsTestCase):
    def setUp(self):
        super().setUp()
        self.user, self.profile = self.create_user_with_profile(username="favuser")
        self.category = self.create_category(slug="favcat", title="FavCat")
        self.pkg = self.create_package(
            category=self.category, slug="fav-pkg", title="Favorite Package"
        )
        Favorite.objects.create(favorited_by=self.user, package=self.pkg)
        self.url = reverse(
            "profile_favorite_packages",
            kwargs={"github_account": self.profile.github_account},
        )

    def test_owner_can_view_favorites_even_when_private(self):
        self.login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorite Package")

    def test_other_user_gets_403_when_private(self):
        other, _ = self.create_user_with_profile(username="other")
        self.login(other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_gets_403_when_private(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_other_user_can_view_when_public(self):
        self.profile.share_favorites = True
        self.profile.save()

        other, _ = self.create_user_with_profile(username="other-public")
        self.login(other)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorite Package")

    def test_anonymous_can_view_when_public(self):
        self.profile.share_favorites = True
        self.profile.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorite Package")

    def test_404_if_profile_user_inactive(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_renders_card_template_by_default(self):
        self.profile.share_favorites = True
        self.profile.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/profile_packages_card.html")

    def test_htmx_renders_table_template(self):
        self.login(self.user)
        response = self.client.get(
            self.url,
            headers={"HX-Target": "favorite-packages-table-container"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/profile_packages_table.html")


class TestProfileExtraFieldViews(ProfileViewsTestCase):
    def setUp(self):
        super().setUp()
        self.user, self.profile = self.create_user_with_profile(username="extrafield")
        self.other, self.other_profile = self.create_user_with_profile(
            username="otherx"
        )

    def test_create_requires_login(self):
        response = self.client.post(
            reverse("profile_add_extra_field"),
            {"label": "X", "url": "https://x.example.com"},
        )
        self.assertEqual(response.status_code, 302)

    def test_create_valid_creates_and_renders_item_partial(self):
        self.login(self.user)
        response = self.client.post(
            reverse("profile_add_extra_field"),
            {"label": "Site", "url": "https://example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/extra_field_item.html")
        self.assertTrue(
            ExtraField.objects.filter(profile=self.profile, label="Site").exists()
        )

    def test_create_invalid_renders_form_partial(self):
        self.login(self.user)
        response = self.client.post(
            reverse("profile_add_extra_field"),
            {"label": "MissingUrl"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/extra_field_form.html")

    def test_update_requires_login(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        response = self.client.post(
            reverse("profile_edit_extra_field", kwargs={"pk": extra.pk}),
            {"label": "New", "url": "https://new.example.com"},
        )
        self.assertEqual(response.status_code, 302)

    def test_update_forbidden_for_non_owner(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        self.login(self.other)
        response = self.client.post(
            reverse("profile_edit_extra_field", kwargs={"pk": extra.pk}),
            {"label": "Hack", "url": "https://hack.example.com"},
        )
        self.assertEqual(response.status_code, 403)

    def test_update_valid_updates_and_renders_item_partial(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        self.login(self.user)
        response = self.client.post(
            reverse("profile_edit_extra_field", kwargs={"pk": extra.pk}),
            {"label": "Blog", "url": "https://blog.example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/extra_field_item.html")
        extra.refresh_from_db()
        self.assertEqual(extra.label, "Blog")
        self.assertEqual(extra.url, "https://blog.example.com")

    def test_update_invalid_renders_item_partial_with_show_form(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        self.login(self.user)
        response = self.client.post(
            reverse("profile_edit_extra_field", kwargs={"pk": extra.pk}),
            {"label": "Bad", "url": "not-a-url"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/extra_field_item.html")
        self.assertTrue(response.context["show_form"])
        self.assertTrue(response.context["form"].errors)

    def test_delete_requires_login(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        response = self.client.post(
            reverse("profile_delete_extra_field", kwargs={"pk": extra.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_forbidden_for_non_owner(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        self.login(self.other)
        response = self.client.post(
            reverse("profile_delete_extra_field", kwargs={"pk": extra.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ExtraField.objects.filter(pk=extra.pk).exists())

    def test_delete_owner_deletes_extra_field(self):
        extra = ExtraField.objects.create(
            profile=self.profile, label="Site", url="https://example.com"
        )
        self.login(self.user)
        response = self.client.delete(
            reverse("profile_delete_extra_field", kwargs={"pk": extra.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ExtraField.objects.filter(pk=extra.pk).exists())


class TestProfileOpenGraphDetailView(ProfileViewsTestCase):
    def test_opengraph_view_renders_image(self):
        _, profile = self.create_user_with_profile(username="oguser")
        profile.bitbucket_url = "og-bb"
        profile.save()

        ExtraField.objects.create(
            profile=profile, label="Site", url="https://example.com"
        )
        ExtraField.objects.create(
            profile=profile, label="Site2", url="https://example2.com"
        )
        ExtraField.objects.create(
            profile=profile, label="Site3", url="https://example3.com"
        )

        url = reverse(
            "profile_opengraph", kwargs={"github_account": profile.github_account}
        )

        with self.assertNumQueries(2):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["opengraph_urls"]), 4)
