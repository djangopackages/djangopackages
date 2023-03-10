import djclick as click
import requests
from rich import print

from package.models import Package


@click.command()
@click.option("--limit", type=int, default=None)
def command(limit):
    """
    Migrates legacy (http) GitHub packages to https. Migrates existing packages that have moved
    on GitHub, so their data stays up-to-date.
    """
    # fix non-https links
    packages = Package.objects.filter(repo_url__startswith="http://github.com")
    if packages.exists():
        click.secho(
            f"Found {packages.count()} GitHub Packages that need to be migrated",
            fg="yellow",
        )
        for package in packages:
            click.echo(f"    migrating {package.repo_url}")
            package.repo_url = package.repo_url.replace(
                "http://github.com", "https://github.com"
            )
            try:
                package.save()
            except Exception as e:
                click.secho(f"{e}", fg="red")
                # TODO: write migration code...

    packages = Package.objects.filter(repo_url__startswith="https://github.com")

    if limit:
        packages = packages[:limit]

    if packages.exists():
        click.secho(
            f"Found {packages.count()} GitHub Packages to be scanned",
            fg="yellow",
        )
        for package in packages:
            try:
                response = requests.get(package.repo_url, timeout=1.0)
                history = response.history
                if len(history):
                    new_packages = Package.objects.exclude(pk=package.pk).filter(
                        repo_url__startswith=response.url
                    )
                    if new_packages.exists():
                        found_pks = new_packages.values_list("pk", flat=True)
                        click.echo(f"    found {found_pks} <= {package.repo_url}")

                    else:
                        click.echo(
                            f"    migrating {package.repo_url} => {response.url}"
                        )
                        package.repo_url = response.url
                        # TODO: Make a note about migrating the account...
                        package.save()

                    # package.date_deprecated
                    # package.deprecated_by
                    # package.deprecates_package
            except Exception as e:
                print(f"{e} :: {package} :: {package.repo_url}")
