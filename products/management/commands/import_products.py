import djclick as click
import requests
from django.template.defaultfilters import slugify
from rich import print

from products.models import Product

ACTIVE_PRODUCTS = ["django", "python", "wagtail"]


@click.command()
def command():
    print("[yellow]import_products[/yellow]")

    url = "https://endoflife.date/api/all.json"
    response = requests.get(url)
    products = response.json()
    for product in products:
        Product.objects.get_or_create(
            title=product,
            defaults={
                "slug": slugify(product),
                "active": True if product in ACTIVE_PRODUCTS else False,
            },
        )
