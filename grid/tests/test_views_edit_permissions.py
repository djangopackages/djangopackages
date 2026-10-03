"""The grid detail page must offer the controls its views actually allow.

This file was named to sort after test_views.py, back when
FunctionalGridTest.setUp mutated settings.RESTRICT_GRID_EDITORS globally and
its assertNumQueries counts depended on test order. #1690 replaced that with
override_settings, so the name no longer matters and can be shortened.

See #1687: the templates used to gate on Django model permissions while the
views gate on Profile.can_*, so trusted users never saw the buttons.
"""

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker

from grid.models import Grid
from profiles.models import Profile

CONTROLS = (
    "can_edit_grid",
    "can_add_grid_package",
    "can_add_grid_feature",
    "can_edit_grid_feature",
    "can_edit_grid_element",
)


@pytest.fixture()
def approved_grid(db) -> Grid:
    return baker.make(
        Grid,
        slug="editable-grid",
        title="Editable Grid",
        is_approved=True,
        created_by=None,
    )


@pytest.fixture()
def trusted_user(db) -> User:
    user = baker.make(User, username="trusted-user", is_staff=False, is_superuser=False)
    Profile.objects.update_or_create(user=user, defaults={"is_trusted_override": True})
    return user


@override_settings(RESTRICT_GRID_EDITORS=False)
@pytest.mark.django_db
def test_trusted_user_gets_the_edit_controls(client, approved_grid, trusted_user):
    client.force_login(trusted_user)
    response = client.get(reverse("grid", kwargs={"slug": approved_grid.slug}))

    assert response.status_code == 200
    for name in CONTROLS:
        assert response.context[name] is True, f"{name} should be offered"


@override_settings(RESTRICT_GRID_EDITORS=False)
@pytest.mark.django_db
def test_anonymous_user_gets_no_edit_controls(client, approved_grid):
    response = client.get(reverse("grid", kwargs={"slug": approved_grid.slug}))

    assert response.status_code == 200
    for name in (*CONTROLS, "can_edit_pending_grid"):
        assert response.context[name] is False, f"{name} should not be offered"


@override_settings(RESTRICT_GRID_EDITORS=True)
@pytest.mark.django_db
def test_restricted_mode_still_defers_to_model_permissions(
    client, approved_grid, trusted_user
):
    client.force_login(trusted_user)
    response = client.get(reverse("grid", kwargs={"slug": approved_grid.slug}))

    assert response.status_code == 200
    for name in CONTROLS:
        assert response.context[name] is False, f"{name} needs an explicit permission"
