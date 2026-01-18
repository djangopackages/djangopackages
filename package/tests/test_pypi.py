import pytest
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError

from package.models import Package, Version, Category
from package.pypi import (
    PyPIClient,
    _supports_python3,
    update_package_from_pypi,
    PyPIRateLimitError,
)


class TestPyPIClient:
    def test_fetch_project_success(self):
        client = PyPIClient()
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"info": {"name": "test-pkg"}, "urls": []}
            mock_get.return_value = mock_response

            project = client.fetch_project("test-pkg")
            assert project.name == "test-pkg"

    def test_fetch_project_404(self):
        client = PyPIClient()
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError(
                response=mock_response
            )
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError):
                client.fetch_project("non-existent")


class TestSupportPython3:
    def test_classifiers_support(self):
        classifiers = [
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
        ]
        assert _supports_python3(None, classifiers) is True

    def test_requires_python_support(self):
        assert _supports_python3(">=3.6", []) is True
        assert _supports_python3(">=3.0", []) is True

    def test_requires_python_no_support(self):
        # Assuming _PY3_PROBE_VERSIONS are 3.x
        assert _supports_python3("<3.0", []) is False
        assert _supports_python3("==2.7", []) is False

    def test_invalid_specifier_fallback(self):
        # Should fall back to classifiers if specifier is invalid
        classifiers = ["Programming Language :: Python :: 3"]
        assert _supports_python3("invalid-specifier", classifiers) is True
        assert _supports_python3("invalid-specifier", []) is None


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
        with patch("package.pypi.PyPIClient.fetch_project") as mock_fetch:
            mock_fetch.return_value = Mock(
                info=pypi_data["info"],
                classifiers=pypi_data["info"]["classifiers"],
                requires_python=pypi_data["info"]["requires_python"],
                urls=pypi_data["urls"],
                docs_url=pypi_data["info"]["docs_url"],
                version="1.0.0",
                project_urls={},
            )

            updated_pkg = update_package_from_pypi(package)

            assert updated_pkg.pypi_name == "test-package"
            assert updated_pkg.supports_python3 is True
            assert updated_pkg.documentation_url == "https://docs.example.com"
            assert updated_pkg.latest_version.number == "1.0.0"
            assert Version.objects.filter(package=package, number="1.0.0").exists()

    def test_update_404_clears_url(self, package):
        with patch("package.pypi.PyPIClient.fetch_project") as mock_fetch:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_fetch.side_effect = HTTPError(response=mock_response)

            update_package_from_pypi(package, clear_pypi_url_on_404=True)

            package.refresh_from_db()
            assert package.pypi_url == ""

    def test_update_429_raises_error(self, package):
        with patch("package.pypi.PyPIClient.fetch_project") as mock_fetch:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_fetch.side_effect = HTTPError(response=mock_response)

            with pytest.raises(PyPIRateLimitError):
                update_package_from_pypi(package)

    def test_license_extraction(self, package, pypi_data):
        # Test PEP 639 license expression
        pypi_data["info"]["license_expression"] = "Apache-2.0"

        with patch("package.pypi.PyPIClient.fetch_project") as mock_fetch:
            mock_fetch.return_value = Mock(
                info=pypi_data["info"],
                classifiers=[],
                requires_python=None,
                urls=[],
                docs_url=None,
                version="1.0.0",
                project_urls={},
            )

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
        with patch("package.pypi.PyPIClient.fetch_project") as mock_fetch:
            mock_fetch.return_value = Mock(
                info=pypi_data["info"],
                classifiers=[],
                requires_python=None,
                urls=pypi_data["urls"],
                docs_url=None,
                version="2.0.0",
                project_urls={},
            )
            update_package_from_pypi(package)
            v = Version.objects.get(package=package, number="2.0.0")
            assert v.upload_time is not None
