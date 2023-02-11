import djclick as click
import requests
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout, SSLError
from rich import print

from package.models import PackageExample


@click.command()
@click.option("--limit", default=None, type=int)
def command(limit):
    print("[bold]raw stats[/bold]")
    print(f"{PackageExample.objects.filter(active=None).count()=}")
    print(f"{PackageExample.objects.filter(active=True).count()=}")
    print(f"{PackageExample.objects.filter(active=False).count()=}")
    print()

    package_examples = (
        PackageExample.objects.exclude(active=False).order_by("url").distinct("url")
    )

    if limit:
        package_examples = package_examples[:limit]

    print(f"{package_examples.count()=}")

    for example in package_examples:
        url = f"{example.url}"
        if not url.startswith("http"):
            # we are going to assume "https" here for security reasons
            url = f"https://{url}"

        try:
            response = requests.head(url, timeout=2, verify=False)
            response.raise_for_status()
        except (ConnectionError, HTTPError, ReadTimeout, SSLError):
            print(f"[red]marking {example.url} as inactive[/red]")
            PackageExample.objects.filter(url=example.url).update(active=False)

        # TODO: Possibly do a SPAM check on the domain...
