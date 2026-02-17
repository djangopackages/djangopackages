from time import gmtime, strftime

import djclick as click

from rich import print

from searchv3.builders import build_search_index


@click.command()
@click.option("--verbose", is_flag=True, default=False)
def command(verbose):
    """Build the SearchV3 full-text search index."""
    start_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    print(f"[bold cyan]🚀 Starting SearchV3 index build at {start_time}[/bold cyan]")

    try:
        build_search_index(verbose=verbose)
        print("[green]✅ SearchV3 index build completed successfully.[/green]")
    except Exception as e:
        print(f"[bold red]❌ SearchV3 index build failed: {e}[/bold red]")
        raise

    end_time = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    print(f"[bold cyan]🏁 Finished at {end_time}[/bold cyan]")
