"""One spelling per license, whichever way it reached us."""

from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command

from package import licenses
from package.models import Package, Version
from package.pypi import PyPIPackage, update_package_from_pypi
from package.repos.github import GitHubHandler, detected_license

MIT_TEXT = """The MIT License (MIT)

Copyright (c) 2016-present Somebody

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction..."""


class TestNormalize:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("MIT", "MIT"),
            ("mit", "MIT"),
            ("MIT License", "MIT"),
            ("The MIT License", "MIT"),
            ("BSD", "BSD"),
            ("New BSD License", "BSD-3-Clause"),
            ("3-clause BSD", "BSD-3-Clause"),
            ("BSD-2-Clause", "BSD-2-Clause"),
            ("Apache 2.0", "Apache-2.0"),
            ("Apache License 2.0", "Apache-2.0"),
            ("Apache-2.0", "Apache-2.0"),
            ("GPLv3", "GPL-3.0-only"),
            ("GPL-3.0", "GPL-3.0-only"),
            ("GNU GPLv3", "GPL-3.0-only"),
            ("GPLv3+", "GPL-3.0-or-later"),
            ("LGPL 3", "LGPL-3.0-only"),
            ("AGPLv3", "AGPL-3.0-only"),
            ("MPL 2.0", "MPL-2.0"),
            ("ISC", "ISC"),
            ("CC0", "CC0-1.0"),
        ],
    )
    def test_common_spellings_map_to_one_id(self, text, expected):
        assert licenses.normalize(text) == expected

    def test_an_spdx_expression_is_kept_as_written(self):
        assert licenses.normalize("MIT OR Apache-2.0") == "MIT OR Apache-2.0"
        assert (
            licenses.normalize("GPL-2.0-only OR LGPL-2.1-or-later")
            == "GPL-2.0-only OR LGPL-2.1-or-later"
        )

    def test_an_unknown_short_name_is_kept(self):
        assert licenses.normalize("Repoze Public License") == "Repoze Public License"

    @pytest.mark.parametrize(
        "text",
        [
            None,
            "",
            "   ",
            "UNKNOWN",
            "LICENSE.txt",
            "LICENSE",
            "GNU",
            "Custom",
            "x" * 61,
        ],
    )
    def test_things_that_are_not_a_license(self, text):
        assert licenses.normalize(text) is None

    def test_a_pasted_license_body_is_not_a_name(self):
        assert licenses.normalize(MIT_TEXT) is None


class TestFromClassifier:
    def test_maps_to_spdx(self):
        assert (
            licenses.from_classifier("License :: OSI Approved :: MIT License") == "MIT"
        )
        assert (
            licenses.from_classifier(
                "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
            )
            == "GPL-3.0-only"
        )

    def test_a_family_classifier_gives_the_family(self):
        assert (
            licenses.from_classifier("License :: OSI Approved :: BSD License") == "BSD"
        )

    def test_a_generic_classifier_gives_nothing(self):
        assert licenses.from_classifier("License :: OSI Approved") is None
        assert licenses.from_classifier("Framework :: Django") is None


class TestFromPyPI:
    def test_expression_wins(self):
        found = licenses.from_pypi(
            license_expression="Apache-2.0",
            classifiers=["License :: OSI Approved :: MIT License"],
            legacy="BSD",
        )
        assert found == ["Apache-2.0", "MIT"]

    def test_classifier_beats_pasted_license_text(self):
        """django-freeze: MIT classifier, the whole MIT text in `license`."""
        found = licenses.from_pypi(
            license_expression=None,
            classifiers=["License :: OSI Approved :: MIT License"],
            legacy=MIT_TEXT,
        )
        assert found == ["MIT"]

    def test_legacy_field_only_when_nothing_else(self):
        assert licenses.from_pypi(
            license_expression=None, classifiers=[], legacy="BSD"
        ) == ["BSD"]

    def test_legacy_field_sharpens_a_family_classifier(self):
        """ "BSD License" is a family; "BSD-3-Clause" in the legacy field
        says which member, so it wins. Same for GPL."""
        found = licenses.from_pypi(
            license_expression=None,
            classifiers=["License :: OSI Approved :: BSD License"],
            legacy="BSD-3-Clause",
        )
        assert found == ["BSD-3-Clause", "BSD"]

        found = licenses.from_pypi(
            license_expression=None,
            classifiers=["License :: OSI Approved :: GNU General Public License (GPL)"],
            legacy="GPLv3",
        )
        assert found == ["GPL-3.0-only", "GPL"]

    def test_legacy_field_cannot_override_a_different_family(self):
        found = licenses.from_pypi(
            license_expression=None,
            classifiers=["License :: OSI Approved :: MIT License"],
            legacy="BSD-3-Clause",
        )
        assert found == ["MIT"]

    def test_a_filename_in_the_legacy_field_is_not_a_license(self):
        assert (
            licenses.from_pypi(
                license_expression=None, classifiers=[], legacy="LICENSE.txt"
            )
            == []
        )


class TestPyPIPackage:
    def test_django_freeze_shape(self):
        pkg = PyPIPackage(
            {
                "info": {
                    "license": MIT_TEXT,
                    "license_expression": None,
                    "classifiers": ["License :: OSI Approved :: MIT License"],
                }
            }
        )
        assert pkg.license_list == ["MIT"]


@pytest.mark.django_db
class TestUpdateFromPyPI:
    def _update(self, package, info):
        package.pypi_url = "https://pypi.org/project/deps/"
        package.save()
        with patch("package.pypi.PyPIClient.fetch_package") as fetch:
            fetch.return_value = PyPIPackage(
                {"info": {"version": "1.0", **info}, "urls": []}
            )
            update_package_from_pypi(package)
        package.refresh_from_db()
        return package

    def test_pasted_text_plus_classifier_gives_the_classifier(self, package):
        self._update(
            package,
            {
                "license": MIT_TEXT,
                "classifiers": ["License :: OSI Approved :: MIT License"],
            },
        )
        assert package.pypi_license == "MIT"
        assert package.pypi_licenses == ["MIT"]
        assert package.latest_version.license == "MIT"

    def test_no_license_leaves_the_repo_license_to_decide(self, package):
        package.repo_license = "MIT"
        package.save()

        self._update(package, {"license": MIT_TEXT, "classifiers": []})

        assert package.pypi_license is None
        assert package.license_display == "MIT"

    def test_a_license_that_went_away_is_cleared(self, package):
        package.pypi_license = "BSD"
        package.pypi_licenses = ["BSD"]
        package.save()

        self._update(package, {"license": "", "classifiers": []})

        assert package.pypi_license is None
        assert package.license_display == "UNKNOWN"


@pytest.mark.django_db
class TestGitHubLicense:
    def _repo(self, spdx_id):
        repo = Mock()
        repo.archived = False
        repo.description = "d"
        repo.forks_count = 1
        repo.watchers_count = 2
        repo.homepage = ""
        repo.contributors.return_value = []
        if spdx_id is None:
            repo.original_license = None
        else:
            repo.original_license = Mock(spdx_id=spdx_id)
        return repo

    def _fetch(self, package, repo):
        handler = GitHubHandler()
        with (
            patch.object(handler, "_get_repo", return_value=repo),
            patch.object(handler, "_fetch_commit_stats"),
            patch.object(handler, "manage_ratelimit"),
        ):
            handler.fetch_metadata(package)
        return Package.objects.get(pk=package.pk)

    def test_detected_license_is_stored(self, package):
        package = self._fetch(package, self._repo("MIT"))
        assert package.repo_license == "MIT"
        assert package.license_display == "MIT"

    def test_noassertion_means_nothing_detected(self):
        assert detected_license(self._repo("NOASSERTION")) == ""
        assert detected_license(self._repo(None)) == ""

    def test_pypi_still_wins_over_github(self, package):
        package.pypi_license = "BSD-3-Clause"
        package.save()
        package = self._fetch(package, self._repo("MIT"))
        assert package.license_display == "BSD-3-Clause"


@pytest.mark.django_db
class TestRebuildCommand:
    def test_recomputes_from_stored_pypi_info(self, package):
        package.pypi_license = "Custom"
        package.pypi_licenses = ["Custom", "MIT License"]
        package.pypi_info = {
            "license": MIT_TEXT,
            "classifiers": ["License :: OSI Approved :: MIT License"],
        }
        package.save()
        version = Version.objects.create(
            package=package, number="1.0", license="Custom"
        )
        Package.objects.filter(pk=package.pk).update(latest_version=version)

        call_command("rebuild_licenses")

        package.refresh_from_db()
        assert package.pypi_license == "MIT"
        assert package.pypi_licenses == ["MIT"]
        assert Version.objects.get(pk=version.pk).license == "MIT"

    def test_falls_back_to_stored_classifiers(self, package):
        package.pypi_license = "BSD License"
        package.pypi_info = None
        package.pypi_classifiers = ["License :: OSI Approved :: BSD License"]
        package.save()

        call_command("rebuild_licenses")

        package.refresh_from_db()
        assert package.pypi_license == "BSD"

    def test_dry_run_writes_nothing(self, package):
        package.pypi_license = "MIT License"
        package.save()

        call_command("rebuild_licenses", "--dry-run")

        package.refresh_from_db()
        assert package.pypi_license == "MIT License"
