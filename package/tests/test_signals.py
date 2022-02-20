from package.models import Package
from package.signals import signal_fetch_latest_metadata


def test_signal_fetch_latest_metadata(db, mocker, category):
    # setup our signals
    handle_signal = mocker.Mock()
    signal_fetch_latest_metadata.connect(handle_signal)

    # create a test package and fetch our metadata
    package_obj = Package.objects.create(slug="package", category=category)
    package_obj.fetch_metadata()

    # verify that our signal/function was called
    handle_signal.assert_called()
