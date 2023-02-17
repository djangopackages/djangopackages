import json

import pytest
from django.core.management import call_command
from model_bakery import baker

from products.models import Product, Release


@pytest.fixture()
def eol_release_data():
    return [
        {
            "cycle": "4.0",
            "support": "2022-08-01",
            "eol": "2023-04-01",
            "latest": "4.0.4",
        },
        {
            "cycle": "3.2",
            "support": "2021-12-01",
            "eol": "2024-04-01",
            "latest": "3.2.13",
            "lts": True,
        },
        {
            "cycle": "3.1",
            "support": "2021-04-05",
            "eol": "2021-12-07",
            "latest": "3.1.14",
        },
        {
            "cycle": "3.0",
            "support": "2020-08-01",
            "eol": "2021-04-06",
            "latest": "3.0.14",
        },
        {
            "cycle": "2.2",
            "lts": True,
            "support": "2019-12-01",
            "eol": "2022-04-01",
            "latest": "2.2.28",
        },
        {
            "cycle": "2.1",
            "support": "2019-04-01",
            "eol": "2019-12-02",
            "latest": "2.1.15",
        },
        {
            "cycle": "2.0",
            "support": "2018-08-01",
            "eol": "2019-04-01",
            "latest": "2.0.13",
        },
        {
            "cycle": "1.11",
            "lts": True,
            "support": "2017-12-02",
            "eol": "2020-04-01",
            "latest": "1.11.29",
        },
        {
            "cycle": "3.10",
            "release": "2021-10-04",
            "eol": "2026-10-04",
            "latest": "3.10.4",
        },
        {
            "cycle": "3.9",
            "release": "2020-10-05",
            "eol": "2025-10-05",
            "latest": "3.9.13",
        },
        {
            "cycle": "3.8",
            "release": "2019-10-14",
            "eol": "2024-10-14",
            "latest": "3.8.13",
        },
        {
            "cycle": "3.7",
            "release": "2018-06-27",
            "eol": "2023-06-27",
            "latest": "3.7.13",
        },
        {
            "cycle": "3.6",
            "release": "2016-12-23",
            "eol": "2021-12-23",
            "latest": "3.6.15",
        },
        {
            "cycle": "3.5",
            "release": "2015-09-13",
            "eol": "2020-09-13",
            "latest": "3.5.10",
        },
        {
            "cycle": "3.4",
            "release": "2014-03-16",
            "eol": "2019-03-18",
            "latest": "3.4.10",
        },
        {
            "cycle": "3.3",
            "release": "2012-09-29",
            "eol": "2017-09-29",
            "latest": "3.3.7",
        },
        {
            "cycle": "2.7",
            "release": "2010-07-03",
            "eol": "2020-01-01",
            "latest": "2.7.18",
        },
    ]


def test_release_import(db, requests_mock, eol_release_data):
    requests_mock.get(
        "https://endoflife.date/api/django.json",
        status_code=200,
        text=json.dumps(eol_release_data),
    )

    assert Product.objects.all().count() == 0
    assert Release.objects.all().count() < len(eol_release_data)

    baker.make("products.Product", title="django", slug="django", active=True)

    call_command("import_releases")

    assert Product.objects.all().count() == 1
    assert Release.objects.all().count() == len(eol_release_data)
