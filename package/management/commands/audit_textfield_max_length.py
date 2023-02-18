import djclick as click
from django.db.models.functions import Length
from rich import print

from grid.models import Element, Feature, Grid
from homepage.models import PSA
from package.models import Category, Package


@click.command()
def command():
    """Identifies objects with a text field greater than the maximum length."""
    TEXT_LIMIT = 500

    items = Element.objects.annotate(text_len=Length("text")).filter(
        text_len__gt=TEXT_LIMIT
    )
    if items.exists():
        print(f"[bold][yellow]Elements: {items.count()}[/yellow][/bold]")
        for item in items:
            print(f"pk={item.pk} :: {len(item.text)}")

    items = Feature.objects.annotate(text_len=Length("description")).filter(
        text_len__gt=TEXT_LIMIT
    )
    if items.exists():
        print(f"[bold][yellow]Feature: {items.count()}[/yellow][/bold]")
        for item in items:
            print(f"pk={item.pk} :: {len(item.description)}")

    items = Grid.objects.annotate(text_len=Length("description")).filter(
        text_len__gt=TEXT_LIMIT
    )
    if items.exists():
        print(f"[bold][yellow]Grid: {items.count()}[/yellow][/bold]")
        for item in items:
            print(
                f"pk={item.pk} :: {len(item.description)} :: {item.get_absolute_url()}"
            )

    items = PSA.objects.annotate(text_len=Length("body_text")).filter(
        text_len__gt=TEXT_LIMIT
    )
    if items.exists():
        print(f"[bold][yellow]PSA: {items.count()}[/yellow][/bold]")
        for item in items:
            print(f"pk={item.pk} :: {len(item.body_text)}")

    items = Category.objects.annotate(text_len=Length("description")).filter(
        text_len__gt=TEXT_LIMIT
    )
    if items.exists():
        print(f"[bold][yellow]Category: {items.count()}[/yellow][/bold]")
        for item in items:
            print(
                f"pk={item.pk} :: {len(item.description)} :: {item.get_absolute_url()}"
            )

    items = Package.objects.annotate(text_len=Length("repo_description")).filter(
        text_len__gt=TEXT_LIMIT
    )
    if items.exists():
        print(
            f"[bold][yellow]Package (repo_description): {items.count()}[/yellow][/bold]"
        )
        for item in items:
            print(
                f"pk={item.pk} :: {len(item.repo_description)} :: {item.get_absolute_url()}"
            )
