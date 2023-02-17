import djclick as click
import requests
from dirty_equals import IsDate, IsTrueLike
from rich import print

from products.models import Product, Release


@click.command()
def command():
    print("[yellow]import_releases[/yellow]")

    products = Product.objects.filter(active=True).order_by("slug")
    for product in products:
        url = f"https://endoflife.date/api/{product.slug}.json"
        response = requests.get(url)
        release_list = response.json()
        for release_data in release_list:
            print(f"{product} == {release_data}")

            eol = release_data.get("eol")
            release = release_data.get("releaseDate")
            support = release_data.get("support")
            lts = release_data.get("lts")

            Release.objects.update_or_create(
                product=product,
                cycle=release_data.get("cycle"),
                defaults={
                    "codename": release_data.get("codename"),
                    "cycle_short_hand": release_data.get("cycleShortHand"),
                    "discontinued": release_data.get("discontinued"),
                    "eol": eol if eol == IsDate(iso_string=True) else None,
                    "latest": release_data.get("latest"),
                    "link": release_data.get("link"),
                    "lts": True if lts == IsTrueLike else False,
                    "release": release if release == IsDate(iso_string=True) else None,
                    "support": support if support == IsDate(iso_string=True) else None,
                },
            )
