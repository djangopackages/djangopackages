from core.utils import PackageStatus
from package.templatetags.package_tags import package_dev_status_badge


def test_package_dev_status_badge_stable_is_green():
    html = package_dev_status_badge(PackageStatus.STABLE)
    assert "Production/Stable" in html
    assert "bg-green-50" in html
    assert "ph-check-circle" in html


def test_package_dev_status_badge_hidden_is_muted():
    html = package_dev_status_badge(PackageStatus.BETA, muted=True)
    assert "Beta" in html
    assert "bg-muted" in html
    assert "text-muted-foreground" in html


def test_package_dev_status_badge_beta_has_icon_and_color():
    html = package_dev_status_badge(PackageStatus.BETA)
    assert "Beta" in html
    assert "bg-indigo-50" in html
    assert "ph-test-tube" in html
