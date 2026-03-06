import logging
from time import gmtime, strftime

import djclick as click

from searchv3.builders import build_search_index

logger = logging.getLogger(__name__)


@click.command()
@click.option("--verbose", is_flag=True, default=False)
def command(verbose):
    """Build the SearchV3 full-text search index."""
    start_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    logger.info(f"Starting SearchV3 index build at {start_time}")

    try:
        build_search_index(verbose=verbose)
        logger.info("SearchV3 index build completed successfully.")
    except Exception as e:
        logger.error(f"SearchV3 index build failed: {e}")
        raise

    end_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    logger.info(f"Finished at {end_time}")
