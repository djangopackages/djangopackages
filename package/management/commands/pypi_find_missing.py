import djclick as click
import logging

from django.db.models import Q

from package.models import Package

logger = logging.getLogger(__name__)


@click.command()
def command():
    total_empty_packages = Package.objects.filter(
        ~Q(pypi_url__startswith="http")
    ).count()
    total_packages = Package.objects.all().count()
    packages = Package.objects.filter(~Q(pypi_url__startswith="http") & ~Q(pypi_url=""))

    click.echo(f"total_packages: {total_packages}")
    click.echo(f"total_empty_packages: {total_empty_packages}")
    click.echo(f"packages needing fixed: {packages.count()}")

    for package in packages:
        click.echo(f"- {package.pypi_url}")
