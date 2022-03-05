import djclick as click

from django.db.models.functions import Length
from rich import print

from grid.models import Element, Feature, Grid
from homepage.models import PSA
from package.models import Category, Package

# from searchv2.models import SearchV2


@click.command()
def command():
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

    # items = Package.objects.annotate(text_len=Length("participants")).filter(
    #     text_len__gt=TEXT_LIMIT
    # )
    # if items.exists():
    #     print(f"[bold][yellow]Package (participants): {items.count()}[/yellow][/bold]")
    #     for item in items:
    #         print(f"pk={item.pk} :: {len(item.participants)}")

    # items = Package.objects.annotate(text_len=Length("commit_list")).filter(
    #     text_len__gt=TEXT_LIMIT
    # )
    # if items.exists():
    #     print(f"[bold][yellow]Package (commit_list): {items.count()}[/yellow][/bold]")
    #     for item in items:
    #         print(f"pk={item.pk} :: {len(item.commit_list)}")

    # items = SearchV2.objects.annotate(text_len=Length("description")).filter(
    #     text_len__gt=TEXT_LIMIT
    # )
    # if items.exists():
    #     print(f"[bold][yellow]SearchV2 (description): {items.count()}[/yellow][/bold]")
    #     for item in items:
    #         print(f"pk={item.pk} :: {len(item.description)}")

    # items = SearchV2.objects.annotate(text_len=Length("participants")).filter(
    #     text_len__gt=TEXT_LIMIT
    # )
    # if items.exists():
    #     print(f"[bold][yellow]SearchV2 (participants): {items.count()}[/yellow][/bold]")
    #     for item in items:
    #         print(f"pk={item.pk} :: {len(item.participants)}")
