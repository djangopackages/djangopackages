import djclick as click
import gzip
import httpx
import shutil

from package.models import Package
from pathlib import Path
from rich import print
from sqlite_utils import Database


def decompress_gz_file(filename: str):
    if not filename.endswith(".gz"):
        print("File is not a .gz file")
        return

    with gzip.open(filename, "rb") as f_in:
        with open(filename[:-3], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    print("File decompressed successfully")


def download_file(*, url: str, filename: str):
    if Path(filename).exists():
        print("File already exists")
        return

    with httpx.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(
                chunk_size=8192
            ):  # Choose the right chunk size for you
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

    print("File downloaded successfully")


def normalize_pypi_slug(url: str) -> str:
    return url.rstrip("/").rsplit('/', 1)[-1]


@click.command()
@click.argument("url", type=str)
@click.argument("filename", type=str)
@click.option("--limit", type=int, default=None)
def command(filename, limit, url):
    filename = normalize_pypi_slug(url=url)

    download_file(url=url, filename=filename)

    if not Path(filename.replace(".gz", "")).exists():
        decompress_gz_file(filename)

    filename = filename.replace(".gz", "")

    db = Database(filename)

    packages = Package.objects.exclude(pypi_url__in=[None, ""])
    print(f"{packages.count()=}")

    if limit:
        packages = packages[:limit]

    objs = []

    for package in packages:
        pypi_slug = normalize_pypi_slug(package.pypi_url)

        sql = (
            "SELECT name, downloads, requires_python, scorecard_overall "
            "FROM packages "
            "WHERE name = :pypi_slug "
            "LIMIT 1"
        )

        for row in db.query(sql, {"pypi_slug": pypi_slug}):
            if downloads := row["downloads"] > 100_000:
                print(
                    f"{package}=={package.pypi_downloads}, "
                    f"{row['name']}=={row['downloads']}, "
                    f"{row['scorecard_overall']}, "
                    f"{row['requires_python']}"
                )
                package.pypi_downloads = downloads
                objs.append(package)

    if len(objs):
        print(f"bulk updating... {len(objs)} objects")
        Package.objects.bulk_update(objs, ["pypi_downloads"])
