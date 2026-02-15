import argparse
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

def parse_arguments():
    if len(sys.argv) == 1:
        return None  # No arguments provided, trigger interactive menu

    parser = argparse.ArgumentParser(
        description="Search for and/or download content from getcomics.info."
    )
    parser.add_argument("query", type=str, nargs='?', default=None, help="Search term for comics")
    parser.add_argument("-t", "--tag", dest="tag", type=str, default=None, help="Search by tag")
    parser.add_argument("-date", "--d", dest='date', type=str, default=None, help="Get newer ones (YYYY-MM-DD)")
    parser.add_argument("-output", "--o", dest="download_path", type=str, default="./Downloaded Comics", help='Download directory')
    parser.add_argument("-min", dest="min", type=int, default=None, help="Minimum issue number")
    parser.add_argument("-max", dest="max", type=int, default=None, help="Maximum issue number")
    parser.add_argument("-results", "--r", dest="results", type=int, default=15, help="Number of results to show")
    parser.add_argument("-verbose", "--v", dest="verbose", action="store_true", default=False, help="Detailed output")

    args = parser.parse_args()
    args.download_path = Path(args.download_path).expanduser()
    
    if args.query and args.tag:
        parser.error("You can only provide a search query or a tag, not both.")
    
    if args.date:
        try:
            args.date = datetime.strptime(args.date.replace("/", "-").replace(".", "-"), "%Y-%m-%d")
        except:
            console.print("[yellow]Warning: Date format should be YYYY-MM-DD. Date filter disabled.[/yellow]")
            args.date = None

    return args

def show_interactive_menu(comic_links, search_term):
    if not comic_links:
        console.print(f"[bold red]No downloadable links found for '{search_term}'.[/bold red]")
        return []

    console.clear()
    table = Table(
        title=f"""
[bold magenta]Results for: {search_term}[/bold magenta]""",
        show_header=True, 
        header_style="bold cyan",
        border_style="bright_black"
    )
    table.add_column("No", style="dim", width=4, justify="center")
    table.add_column("Comic Title", style="white")
    table.add_column("Source", width=12, justify="center")

    comics_list = []
    for i, (url, title) in enumerate(comic_links.items(), 1):
        is_mediafire = url.startswith("_MEDIAFIRE_")
        source_type = "[yellow]Mediafire[/yellow]" if is_mediafire else "[green]Direct[/green]"
        table.add_row(str(i), title, source_type)
        comics_list.append((url, title))

    console.print(table)
    
    choice = Prompt.ask(
        """
Enter numbers to download (e.g. [bold]1,3[/bold]), [bold]'a'[/bold] for all, [bold]'n'[/bold] for next page, or [bold]'q'[/bold] to quit""",
        default="q"
    )

    if choice.lower() == 'q':
        return []
    if choice.lower() == 'a':
        return comics_list
    if choice.lower() == 'n':
        return "next"
    
    try:
        indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()]
        return [comics_list[i] for i in indices if 0 <= i < len(comics_list)]
    except:
        return []

def interactive_main_menu():
    args = argparse.Namespace()

    # Set defaults
    args.tag = None
    args.query = None
    args.date = None
    args.download_path = Path("./Downloaded Comics").expanduser()
    args.min = None
    args.max = None
    args.results = 15
    args.verbose = False

    # console.print(Panel("[bold cyan]Interactive Mode[/bold cyan]", expand=False))
    
    search_type = Prompt.ask("Search by [bold](q)[/bold]uery, [bold](t)[/bold]ag, or [bold](d)[/bold]etailed search?", default="q")
    
    if search_type == 'd':
        search_type = Prompt.ask("Search by [bold](q)[/bold]uery or [bold](t)[/bold]ag?", default="q")
        if search_type == 'q':
            args.query = Prompt.ask("Enter search query")
        else:
            args.tag = Prompt.ask("Enter tag")

        while True:
            console.print("""
    [bold]Current Options:[/bold]""")
            console.print(f"  [cyan]1. Search Query:[/cyan] {args.query or 'Not set'}")
            console.print(f"  [cyan]2. Search Tag:[/cyan] {args.tag or 'Not set'}")
            console.print(f"  [cyan]3. Date (YYYY-MM-DD):[/cyan] {args.date or 'Not set'}")
            console.print(f"  [cyan]4. Download Path:[/cyan] {args.download_path}")
            console.print(f"  [cyan]5. Min Issue:[/cyan] {args.min or 'Not set'}")
            console.print(f"  [cyan]6. Max Issue:[/cyan] {args.max or 'Not set'}")
            console.print(f"  [cyan]7. Results:[/cyan] {args.results}")
            console.print(f"  [cyan]8. Verbose:[/cyan] {args.verbose}")

            choice = Prompt.ask(
                """
    Choose an option to change, or press [bold](s)[/bold] to start search, [bold](q)[/bold] to quit""",
                default="s"
            )

            if choice == 'q':
                return None
            if choice == 's':
                return args
            
            if choice == '1':
                args.query = Prompt.ask("Enter search query", default=args.query)
                args.tag = None
            elif choice == '2':
                args.tag = Prompt.ask("Enter tag", default=args.tag)
                args.query = None
            elif choice == '3':
                date_str = Prompt.ask("Enter date (YYYY-MM-DD)", default=str(args.date) if args.date else "")
                try:
                    args.date = datetime.strptime(date_str.replace("/", "-").replace(".", "-"), "%Y-%m-%d")
                except:
                    console.print("[yellow]Warning: Date format should be YYYY-MM-DD. Date filter disabled.[/yellow]")
                    args.date = None
            elif choice == '4':
                args.download_path = Path(Prompt.ask("Enter download path", default=str(args.download_path))).expanduser()
            elif choice == '5':
                args.min = int(Prompt.ask("Enter min issue number", default=str(args.min) if args.min else ""))
            elif choice == '6':
                args.max = int(Prompt.ask("Enter max issue number", default=str(args.max) if args.max else ""))
            elif choice == '7':
                args.results = int(Prompt.ask("Enter number of results", default=str(args.results)))
            elif choice == '8':
                args.verbose = not args.verbose
                console.print(f"Verbose output set to {args.verbose}")
    elif search_type == 'q':
        args.query = Prompt.ask("Enter search query")
        return args
    elif search_type == 't':
        args.tag = Prompt.ask("Enter tag")
        return args
