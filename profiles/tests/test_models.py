from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from social_django.models import UserSocialAuth

from grid.models import Grid
from profiles.models import Profile


class MockGitHubRepo:
    title = "GitHub"


class TestModel(TestCase):
    def test_profile(self):
        from profiles.models import Profile

        p = Profile()
        self.assertEqual(len(p.my_packages()), 0)

        r = MockGitHubRepo()
        self.assertEqual(p.url_for_repo(r), None)


@pytest.fixture()
def make_profile(db):
    def _make_profile(*, joined_days_ago, github_days_ago=None, **user_kwargs):
        now = timezone.now()
        user = User.objects.create_user(
            username=f"user-{User.objects.count()}",
            date_joined=now - timedelta(days=joined_days_ago),
            **user_kwargs,
        )
        if github_days_ago is not None:
            created_at = now - timedelta(days=github_days_ago)
            UserSocialAuth.objects.create(
                user=user,
                provider="github",
                uid=str(user.pk),
                extra_data={"created_at": created_at.strftime("%Y-%m-%dT%H:%M:%SZ")},
            )
        return Profile.objects.create(user=user)

    return _make_profile


@pytest.mark.parametrize(
    "joined_days_ago,github_days_ago,expected",
    [
        (0, 1000, False),  # brand new Django Packages account
        (6, 1000, False),
        (7, 1000, True),
        (30, 5, False),  # brand new GitHub account
        (30, 89, False),
        (30, 90, True),
        (30, None, True),  # no stored GitHub date: judged on date_joined alone
    ],
)
@override_settings(NEW_ACCOUNT_REVIEW_DAYS=7, NEW_GITHUB_ACCOUNT_REVIEW_DAYS=90)
def test_profile_is_trusted(make_profile, joined_days_ago, github_days_ago, expected):
    profile = make_profile(
        joined_days_ago=joined_days_ago, github_days_ago=github_days_ago
    )
    assert profile.is_trusted is expected


@pytest.mark.parametrize(
    "user_kwargs,profile_kwargs",
    [
        ({"is_staff": True}, {}),
        ({"is_superuser": True}, {}),
        ({}, {"is_trusted_override": True}),
    ],
)
def test_profile_is_trusted_bypass(make_profile, user_kwargs, profile_kwargs):
    profile = make_profile(joined_days_ago=0, github_days_ago=0, **user_kwargs)
    for name, value in profile_kwargs.items():
        setattr(profile, name, value)
    assert profile.is_trusted is True


@override_settings(RESTRICT_GRID_EDITORS=False)
def test_untrusted_profile_grid_permissions(make_profile):
    profile = make_profile(joined_days_ago=0)
    assert profile.can_add_grid is True
    assert profile.can_edit_grid is False
    assert profile.can_add_grid_feature is False
    assert profile.can_edit_grid_feature is False
    assert profile.can_add_grid_package is False
    assert profile.can_edit_grid_element is False


def test_can_edit_pending_grid(make_profile):
    profile = make_profile(joined_days_ago=0)
    other = make_profile(joined_days_ago=0)

    pending = Grid.objects.create(
        title="Pending", slug="pending", is_approved=False, created_by=profile.user
    )
    approved = Grid.objects.create(
        title="Approved", slug="approved", created_by=profile.user
    )

    assert profile.can_edit_pending_grid(pending) is True
    assert profile.can_edit_pending_grid(approved) is False
    assert other.can_edit_pending_grid(pending) is False
