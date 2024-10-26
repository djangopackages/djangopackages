from time import gmtime, strftime

import djclick as click
from django.conf import settings
from rich import print

from core.utils import healthcheck
from searchv2.builders_v3 import build_1


@click.command()
@click.option("--verbose", is_flag=True, default=False)
def command(verbose):
    """Constructs the search results for the system"""

    start_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    print(f"Commencing search result building now {start_time}")

    build_1(verbose=verbose)

    end_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    print(f"Finished at {end_time}")

    if getattr(settings, "HEALTHCHECK_ENABLED", False):
        healthcheck(settings.SEARCHV2_HEALTHCHECK_URL)
