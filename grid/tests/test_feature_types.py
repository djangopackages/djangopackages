"""Typed features: the parser, the forms that use it, and the report."""

import pytest
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.urls import reverse
from model_bakery import baker

from grid.feature_types import FeatureType, parse
from grid.forms import ElementForm, FeatureForm
from grid.models import Element, Feature
from profiles.models import Profile

pytestmark = pytest.mark.django_db


class TestBooleanParsing:
    @pytest.mark.parametrize(
        "text", ["yes", "Yes", " check ", "+", "+1", "good", "YES"]
    )
    def test_the_legend_words_are_yes(self, text):
        assert parse(FeatureType.BOOLEAN, text) == parse(FeatureType.BOOLEAN, "yes")
        assert parse(FeatureType.BOOLEAN, text).value is True

    @pytest.mark.parametrize("text", ["no", "No", "-", "-1", "bad", "negative"])
    def test_the_legend_words_are_no(self, text):
        assert parse(FeatureType.BOOLEAN, text).value is False

    @pytest.mark.parametrize("text", ["", "  ", "?", "n/a", "unknown", "planned"])
    def test_honest_unknowns_are_unknown_not_errors(self, text):
        result = parse(FeatureType.BOOLEAN, text)
        assert result.ok
        assert result.value is None

    def test_a_note_after_the_word_is_kept(self):
        result = parse(FeatureType.BOOLEAN, "Yes (configured in webpack)")
        assert result.ok
        assert result.value is True
        assert result.note == "configured in webpack"

        result = parse(FeatureType.BOOLEAN, "no, but planned")
        assert result.value is False
        assert result.note == "but planned"

    @pytest.mark.parametrize("text", ["maybe", "partial, via plugin", "4.2", "Vite"])
    def test_anything_else_does_not_parse(self, text):
        assert not parse(FeatureType.BOOLEAN, text).ok


class TestVersionParsing:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("1.8+", ["1.8+"]),
            ("2.7,3.4,3.5", ["2.7", "3.4", "3.5"]),
            ("4.2, 5.1 and 5.2", ["4.2", "5.1", "5.2"]),
            ("3.10 / 3.11", ["3.10", "3.11"]),
            (">=4.2", [">=4.2"]),
            ("1.11 LTS", ["1.11"]),
            ("", []),
        ],
    )
    def test_version_lists_read_as_lists(self, text, expected):
        result = parse(FeatureType.VERSIONS, text)
        assert result.ok
        assert result.value == expected

    @pytest.mark.parametrize("text", ["yes", "latest", "Django 4.2", "4.2 and up"])
    def test_prose_does_not_parse(self, text):
        assert not parse(FeatureType.VERSIONS, text).ok


class TestChoiceAndUrl:
    def test_a_choice_matches_without_case_and_returns_the_canonical_spelling(self):
        result = parse(FeatureType.CHOICE, "postgres", ("PostgreSQL", "MySQL"))
        assert not result.ok
        result = parse(FeatureType.CHOICE, "postgresql", ("PostgreSQL", "MySQL"))
        assert result.ok
        assert result.value == "PostgreSQL"

    def test_a_url_must_be_one_http_link(self):
        assert parse(FeatureType.URL, "https://example.com/docs").ok
        assert not parse(FeatureType.URL, "see the docs").ok
        assert not parse(FeatureType.URL, "ftp://example.com").ok
        assert parse(FeatureType.URL, "").ok

    def test_text_accepts_anything(self):
        assert parse(FeatureType.TEXT, "whatever, really").ok


@pytest.fixture()
def grid():
    return baker.make("grid.Grid", slug="g", title="G")


@pytest.fixture()
def boolean_feature(grid):
    return baker.make(Feature, grid=grid, title="Tests", type=FeatureType.BOOLEAN)


class TestElementForm:
    def test_a_text_feature_takes_anything(self, grid):
        feature = baker.make(Feature, grid=grid, title="Notes")
        element = Element(feature=feature)
        assert ElementForm({"text": "maybe, who knows"}, instance=element).is_valid()

    def test_a_boolean_feature_refuses_prose(self, boolean_feature):
        element = Element(feature=boolean_feature)
        form = ElementForm({"text": "maybe"}, instance=element)
        assert not form.is_valid()
        assert "Yes / no" in form.errors["text"][0]

    def test_a_boolean_feature_takes_the_legend_words_and_notes(self, boolean_feature):
        element = Element(feature=boolean_feature)
        assert ElementForm({"text": "yes, via pytest"}, instance=element).is_valid()
        assert ElementForm({"text": ""}, instance=element).is_valid()

    def test_a_choice_feature_shows_its_choices(self, grid):
        feature = baker.make(
            Feature,
            grid=grid,
            title="Bundler",
            type=FeatureType.CHOICE,
            choices=["Vite", "webpack"],
        )
        form = ElementForm(instance=Element(feature=feature))
        assert "Vite, webpack" in form.fields["text"].help_text
        assert ElementForm(
            {"text": "vite"}, instance=Element(feature=feature)
        ).is_valid()
        assert not ElementForm(
            {"text": "parcel"}, instance=Element(feature=feature)
        ).is_valid()

    def test_the_default_type_is_text(self, grid):
        assert baker.make(Feature, grid=grid).type == FeatureType.TEXT


class TestFeatureForm:
    def test_choices_are_typed_as_a_comma_list(self, grid):
        form = FeatureForm(
            {
                "title": "Bundler",
                "description": "",
                "type": FeatureType.CHOICE,
                "choice_list": "Vite, webpack ,esbuild",
            }
        )
        assert form.is_valid(), form.errors
        feature = form.save(commit=False)
        feature.grid = grid
        feature.save()
        assert feature.choices == ["Vite", "webpack", "esbuild"]

    def test_a_choice_feature_needs_choices(self):
        form = FeatureForm(
            {"title": "Bundler", "description": "", "type": FeatureType.CHOICE}
        )
        assert not form.is_valid()
        assert "choice_list" in form.errors

    def test_existing_choices_fill_the_field(self, grid):
        feature = baker.make(
            Feature, grid=grid, type=FeatureType.CHOICE, choices=["a", "b"]
        )
        assert FeatureForm(instance=feature).fields["choice_list"].initial == "a, b"

    def test_a_plain_feature_still_posts_without_a_type(self, grid):
        form = FeatureForm({"title": "Docs", "description": ""})
        assert form.is_valid(), form.errors


class TestEditViews:
    def test_the_element_edit_page_rejects_a_bad_boolean(
        self, client, boolean_feature, django_user_model
    ):
        user = django_user_model.objects.create_user("editor", password="pw")
        user.user_permissions.add(Permission.objects.get(codename="change_element"))
        Profile.objects.create(user=user)
        package = baker.make(
            "package.Package", slug="p", title="p", repo_url="https://github.com/x/p"
        )
        baker.make("grid.GridPackage", grid=boolean_feature.grid, package=package)
        client.login(username="editor", password="pw")
        url = reverse(
            "edit_element",
            kwargs={
                "grid_slug": "g",
                "feature_id": boolean_feature.pk,
                "package_id": package.pk,
            },
        )
        response = client.post(url, {"text": "sort of"})
        assert response.status_code == 200
        assert Element.objects.get(feature=boolean_feature).text == ""
        response = client.post(url, {"text": "yes"})
        assert response.status_code == 302
        assert Element.objects.get(feature=boolean_feature).text == "yes"


class TestReport:
    def test_it_counts_how_cells_read_and_suggests_a_type(self, grid, capsys):
        feature = baker.make(Feature, grid=grid, title="Has tests")
        package_rows = [
            baker.make(
                "grid.GridPackage",
                grid=grid,
                package=baker.make(
                    "package.Package",
                    slug=f"p{i}",
                    title=f"p{i}",
                    repo_url=f"https://github.com/x/p{i}",
                ),
            )
            for i in range(4)
        ]
        for row, text in zip(package_rows, ["yes", "no", "Yes (pytest)", ""]):
            baker.make(Element, grid_package=row, feature=feature, text=text)

        call_command("feature_type_report", "--slug", "g", "--misses")
        out = capsys.readouterr().out
        assert "Has tests" in out
        assert "boolean" in out

    def test_it_lists_the_cells_that_would_not_parse(self, grid, capsys):
        feature = baker.make(Feature, grid=grid, title="Has tests")
        for i, text in enumerate(["yes", "yes", "yes", "sort of"]):
            row = baker.make(
                "grid.GridPackage",
                grid=grid,
                package=baker.make(
                    "package.Package",
                    slug=f"q{i}",
                    title=f"q{i}",
                    repo_url=f"https://github.com/x/q{i}",
                ),
            )
            baker.make(Element, grid_package=row, feature=feature, text=text)

        call_command(
            "feature_type_report", "--slug", "g", "--type", "boolean", "--misses"
        )
        out = capsys.readouterr().out
        assert "sort of" in out
        assert "1 cells would not parse" in out

    def test_it_writes_nothing(self, grid):
        feature = baker.make(Feature, grid=grid, title="Has tests")
        row = baker.make(
            "grid.GridPackage",
            grid=grid,
            package=baker.make(
                "package.Package",
                slug="w",
                title="w",
                repo_url="https://github.com/x/w",
            ),
        )
        baker.make(Element, grid_package=row, feature=feature, text="yes")
        call_command("feature_type_report", "--slug", "g")
        feature.refresh_from_db()
        assert feature.type == FeatureType.TEXT
