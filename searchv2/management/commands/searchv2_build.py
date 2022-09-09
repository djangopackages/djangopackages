import djclick as click

from time import gmtime, strftime

from django.conf import settings
from rich import print

from core.utils import healthcheck
from searchv2.builders import build_1


@click.command()
def command():
    """Constructs the search results for the system"""

    start_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    print(f"Commencing search result building now {start_time}")

    build_1()

    end_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    print(f"Finished at {end_time}")

    if getattr(settings, "HEALTHCHECK_ENABLED", False):
        healthcheck(settings.SEARCHV2_HEALTHCHECK_URL)
