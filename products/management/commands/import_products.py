import djclick as click
import requests
from django.template.defaultfilters import slugify
from rich import print

from products.models import Product

ACTIVE_PRODUCTS = ["django", "python", "wagtail"]


@click.command()
def command():
    """Imports all packages from endoflife.date, and sets some packages to active"""
    print("[yellow]import_products[/yellow]")

    url = "https://endoflife.date/api/all.json"
    response = requests.get(url)
    response.raise_for_status()
    products = response.json()
    for product in products:
        Product.objects.get_or_create(
            slug=slugify(product),
            defaults={
                "title": product.title(),
                "active": True if product in ACTIVE_PRODUCTS else False,
            },
        )
