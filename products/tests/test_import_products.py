import json

from django.core.management import call_command

from products.models import Product


def test_product_import(db, httpx2_mock):
    PRODUCTS = ["django", "python", "wagtail"]
    httpx2_mock.add_response(
        url="https://endoflife.date/api/all.json",
        status_code=200,
        text=json.dumps(PRODUCTS),
    )

    assert Product.objects.count() == 0

    call_command("import_products")

    assert Product.objects.count() == len(PRODUCTS)
