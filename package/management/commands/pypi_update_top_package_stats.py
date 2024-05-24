import djclick as click
import httpx

from package.models import Package
from rich import print


DOWNLOAD_URL = "https://raw.githubusercontent.com/hugovk/top-pypi-packages/main/top-pypi-packages-30-days.min.json"


def normalize_pypi_slug(url: str) -> str:
    url = url.replace("http:", "https:")
    url = url.strip("/")
    url = url.split("/")[-1]
    return url


@click.command()
@click.argument("url", type=str, default=DOWNLOAD_URL)
def command(url):
    package_lookup = {}

    request = httpx.get(url)
    request.raise_for_status()

    data = request.json()
    print(f"last_update: {data['last_update']}")

    rows = data["rows"]
    for row in rows:
        project = row["project"]
        download_count = row["download_count"]
        package_lookup[project] = download_count

    objs = []
    packages = (
        Package.objects.exclude(pypi_url="")
        .only("pypi_url", "pypi_downloads")
        .order_by("pypi_url")
    )
    for package in packages.iterator():
        pypi_slug = normalize_pypi_slug(package.pypi_url)
        if pypi_slug in package_lookup:
            package.pypi_downloads = package_lookup.get("pypi_slug")
            objs.append(package)

    if len(objs):
        print(f"bulk updating... {len(objs)} objects")
        Package.objects.bulk_update(objs, ["pypi_downloads"])
