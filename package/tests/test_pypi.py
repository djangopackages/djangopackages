import pytest
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError

from package.models import Package, Version, Category
from package.pypi import (
    PyPIClient,
    PyPIPackage,
    update_package_from_pypi,
    PyPIRateLimitError,
)


class TestPyPIClient:
    def test_fetch_package_success(self):
        client = PyPIClient()
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"info": {"name": "test-pkg"}, "urls": []}
            mock_get.return_value = mock_response

            package = client.fetch_package("test-pkg")
            assert isinstance(package, PyPIPackage)
            assert package.name == "test-pkg"

    def test_fetch_package_404(self):
        client = PyPIClient()
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError(
                response=mock_response
            )
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError):
                client.fetch_package("non-existent")


class TestPyPIPackage:
    def test_supports_python3_classifiers(self):
        raw = {
            "info": {
                "classifiers": [
                    "Programming Language :: Python :: 3",
                    "Programming Language :: Python :: 3.10",
                ]
            }
        }
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is True

    def test_supports_python3_requires_python(self):
        raw = {"info": {"requires_python": ">=3.6"}}
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is True

        raw = {"info": {"requires_python": ">=3.0"}}
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is True

    def test_supports_python3_no_support(self):
        raw = {"info": {"requires_python": "<3.0"}}
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is False

        raw = {"info": {"requires_python": "==2.7"}}
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is False

    def test_supports_python3_invalid_specifier_fallback(self):
        raw = {
            "info": {
                "requires_python": "invalid-specifier",
                "classifiers": ["Programming Language :: Python :: 3"],
            }
        }
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is True

        raw = {
            "info": {
                "requires_python": "invalid-specifier",
                "classifiers": [],
            }
        }
        pkg = PyPIPackage(raw)
        assert pkg.supports_python3 is None

    def test_license_list(self):
        # Test PEP 639 license expression
        raw = {"info": {"license_expression": "MIT"}}
        pkg = PyPIPackage(raw)
        assert pkg.license_list == ["MIT"]

        # Test legacy license field
        raw = {"info": {"license": "BSD"}}
        pkg = PyPIPackage(raw)
        assert pkg.license_list == ["BSD"]

        # Test classifiers
        raw = {
            "info": {
                "classifiers": ["License :: OSI Approved :: Apache Software License"]
            }
        }
        pkg = PyPIPackage(raw)
        assert pkg.license_list == ["Apache Software License"]

    def test_license_list_priority(self):
        raw = {
            "info": {
                # Priority 1 if `license_expression` is not present
                # else omit this field
                "license": "BSD",
                # Priority 1
                "license_expression": "MIT",
                # Priority 2
                "classifiers": [
                    "License :: OSI Approved :: Apache Software License",
                    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                ],
            }
        }
        pkg = PyPIPackage(raw)
        assert pkg.license_list == [
            "MIT",
            "Apache Software License",
            "GNU General Public License v3 (GPLv3)",
        ]

    def test_no_license(self):
        raw = {"info": {"license_expression": ""}}
        pkg = PyPIPackage(raw)
        assert pkg.license_list == []

    def test_version_upload_time(self):
        raw = {"urls": [{"upload_time": "2023-01-01T12:00:00"}]}
        pkg = PyPIPackage(raw)
        assert pkg.version_upload_time is not None
        assert pkg.version_upload_time.year == 2023

    def test_development_status(self):
        raw = {
            "info": {
                "classifiers": [
                    "Development Status :: 5 - Production/Stable",
                    "Programming Language :: Python :: 3",
                ]
            }
        }
        pkg = PyPIPackage(raw)
        assert pkg.development_status == 5

    def test_docs_url(self):
        raw = {"info": {"docs_url": "https://example.com/docs"}}
        pkg = PyPIPackage(raw)
        assert pkg.docs_url == "https://example.com/docs"

        raw = {"info": {"project_urls": {"Documentation": "https://example.com/docs"}}}
        pkg = PyPIPackage(raw)
        assert pkg.docs_url == "https://example.com/docs"


@pytest.mark.django_db
class TestUpdatePackageFromPyPI:
    @pytest.fixture
    def category(self):
        return Category.objects.create(title="Test Category", slug="test-category")

    @pytest.fixture
    def package(self, category):
        return Package.objects.create(
            title="Test Package",
            slug="test-package",
            category=category,
            pypi_url="https://pypi.org/project/test-package/",
        )

    @pytest.fixture
    def pypi_data(self):
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "license": "MIT",
                "classifiers": [
                    "Programming Language :: Python :: 3",
                    "License :: OSI Approved :: MIT License",
                ],
                "requires_python": ">=3.8",
                "docs_url": "https://docs.example.com",
            },
            "urls": [
                {"upload_time": "2023-01-01T12:00:00"},
            ],
        }

    def test_update_success(self, package, pypi_data):
        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)

            updated_pkg = update_package_from_pypi(package)

            assert updated_pkg.pypi_name == "test-package"
            assert updated_pkg.supports_python3 is True
            assert updated_pkg.documentation_url == "https://docs.example.com"
            assert updated_pkg.latest_version.number == "1.0.0"
            assert Version.objects.filter(package=package, number="1.0.0").exists()

    def test_update_404_clears_url(self, package):
        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_fetch.side_effect = HTTPError(response=mock_response)

            update_package_from_pypi(package, clear_pypi_url_on_404=True)

            package.refresh_from_db()
            assert package.pypi_url == ""

    def test_update_429_raises_error(self, package):
        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_fetch.side_effect = HTTPError(response=mock_response)

            with pytest.raises(PyPIRateLimitError):
                update_package_from_pypi(package)

    def test_license_extraction(self, package, pypi_data):
        # Test PEP 639 license expression
        pypi_data["info"]["license_expression"] = "Apache-2.0"

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)

            update_package_from_pypi(package)

            version = package.latest_version
            assert "Apache-2.0" in version.licenses

    def test_no_pypi_name(self, category):
        package = Package(
            title="No PyPI", slug="no-pypi", pypi_url="", category=category
        )
        # Should return early without error
        result = update_package_from_pypi(package)
        assert result == package

    def test_create_version_with_upload_time(self, package, pypi_data):
        pypi_data["info"]["version"] = "2.0.0"
        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)
            v = Version.objects.get(package=package, number="2.0.0")
            assert v.upload_time is not None

    def test_update_license_from_legacy(self, package, pypi_data):
        pypi_data["info"]["license"] = "BSD License"
        pypi_data["info"]["license_expression"] = None
        pypi_data["info"]["classifiers"] = []

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            package.refresh_from_db()
            assert package.pypi_license == "BSD License"
            assert package.pypi_licenses == ["BSD License"]

    def test_update_license_from_classifiers(self, package, pypi_data):
        pypi_data["info"]["license"] = None
        pypi_data["info"]["license_expression"] = None
        pypi_data["info"]["classifiers"] = ["License :: OSI Approved :: BSD License"]

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            package.refresh_from_db()
            assert package.pypi_license == "BSD License"
            assert package.pypi_licenses == ["BSD License"]

    def test_update_license_too_long(self, package, pypi_data):
        long_license = "x" * 50
        pypi_data["info"]["license"] = long_license
        pypi_data["info"]["license_expression"] = None
        pypi_data["info"]["classifiers"] = []

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            package.refresh_from_db()
            assert package.pypi_license == "Custom"
            assert package.pypi_licenses == ["Custom"]

    def test_update_development_status(self, package, pypi_data):
        pypi_data["info"]["classifiers"] = ["Development Status :: 3 - Alpha"]

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            version = package.latest_version
            assert version.development_status == 3
            assert version.pretty_status == "Alpha"
            assert package.development_status == "Alpha"

    def test_update_requires_python(self, package, pypi_data):
        pypi_data["info"]["requires_python"] = ">=3.10"
        pypi_data["info"]["classifiers"] = []

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            package.refresh_from_db()
            assert package.pypi_requires_python == ">=3.10"
            assert package.supports_python3 is True

    def test_update_requires_python_unsupported(self, package, pypi_data):
        pypi_data["info"]["requires_python"] = "<3"
        pypi_data["info"]["classifiers"] = []

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            package.refresh_from_db()
            assert package.pypi_requires_python == "<3"
            assert package.supports_python3 is False

    def test_update_classifiers(self, package, pypi_data):
        classifiers = ["Framework :: Django", "Programming Language :: Python :: 3"]
        pypi_data["info"]["classifiers"] = classifiers

        with patch("package.pypi.PyPIClient.fetch_package") as mock_fetch:
            mock_fetch.return_value = PyPIPackage(pypi_data)
            update_package_from_pypi(package)

            package.refresh_from_db()
            assert package.pypi_classifiers == classifiers
