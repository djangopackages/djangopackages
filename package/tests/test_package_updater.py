import pytest

from click import exceptions
from django.core.management import call_command


def test_package_updater_command(db):
    with pytest.raises(exceptions.Exit):
        call_command("package_updater", "--help")
