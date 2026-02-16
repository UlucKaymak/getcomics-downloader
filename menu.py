import argparse
import sys
from datetime import datetime
from pathlib import Path
import json
import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

CONFIG_FILE = Path(".") / ".config.json"

def save_options(args):
    with open(CONFIG_FILE, 'w') as f:
        args_dict = vars(args)
        if 'download_path' in args_dict and isinstance(args_dict['download_path'], Path):
            args_dict['download_path'] = str(args_dict['download_path'])
        json.dump(args_dict, f, indent=4)
    console.print(f"[green]Options saved to {CONFIG_FILE}[/green]")

def load_options():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            try:
                options = json.load(f)
                if 'download_path' in options and isinstance(options['download_path'], str):
                    options['download_path'] = Path(options['download_path'])
                return argparse.Namespace(**options)
            except json.JSONDecodeError:
                console.print(f"[yellow]Warning: Could not read config file {CONFIG_FILE}. Using default options.[/yellow]")
                return None
    return None

def parse_arguments():
    if len(sys.argv) == 1:
        return None  # No arguments provided, trigger interactive menu

    parser = argparse.ArgumentParser(
        description="Search for and/or download content from getcomics.org."
    )
    parser.add_argument("query", type=str, nargs='?', default=None, help="Search term for comics")

    parser.add_argument("-date", "--d", dest='date', type=str, default=None, help="Get newer ones (YYYY)")
    parser.add_argument("-output", "--o", dest="download_path", type=str, default="Downloads/Comics", help='Download directory')
    parser.add_argument("-min", dest="min", type=int, default=None, help="Minimum issue number")
    parser.add_argument("-max", dest="max", type=int, default=None, help="Maximum issue number")
    parser.add_argument("-results", "--r", dest="results", type=int, default=15, help="Number of results to show")
    parser.add_argument("-verbose", "--v", dest="verbose", action="store_true", default=False, help="Detailed output")

    args = parser.parse_args()
    args.download_path = Path(args.download_path).expanduser()
    
    if args.date:
        try:
            args.date = datetime.strptime(args.date, "%Y").year
        except:
            console.print("[yellow]Warning: Date format should be YYYY. Date filter disabled.[/yellow]")
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

    loaded_args = load_options()
    if loaded_args:
        args = loaded_args

    args.query = None if not hasattr(args, 'query') else args.query
    args.date = None if not hasattr(args, 'date') else args.date
    args.download_path = Path("Downloads/Comics").expanduser() if not hasattr(args, 'download_path') else args.download_path
    args.min = None if not hasattr(args, 'min') else args.min
    args.max = None if not hasattr(args, 'max') else args.max
    args.results = 15 if not hasattr(args, 'results') else args.results
    args.verbose = False if not hasattr(args, 'verbose') else args.verbose
    
    while True:
        choice = Prompt.ask("Search by [bold]q[/bold]uery, or [bold]o[/bold]ptions?", default="q")

        if choice.lower() == 'q':
            args.query = Prompt.ask(f"Enter search query (Leave empty to lookup last {args.results} comic)")
            # if args.query:
            return args
            # else:
            #     console.print("[bold red]Please enter a search query.[/bold red]")
            #     Prompt.ask("Press Enter to continue...")
        elif choice.lower() == 'o':
            args = options_menu(args)
            continue 
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")
            Prompt.ask("Press Enter to continue...")

def options_menu(args):
    while True:
        console.print("""
[bold]Current Options:[/bold]""")
        console.print(f"  [cyan]1. Date (YYYY):[/cyan] {args.date or 'Not set'}")
        console.print(f"  [cyan]2. Download Path:[/cyan] {args.download_path}")
        console.print(f"  [cyan]3. Min Issue:[/cyan] {args.min or 'Not set'}")
        console.print(f"  [cyan]4. Max Issue:[/cyan] {args.max or 'Not set'}")
        console.print(f"  [cyan]5. Results:[/cyan] {args.results}")
        console.print(f"  [cyan]6. Display Log:[/cyan] {args.verbose}")

        choice = Prompt.ask(
            """Choose an option to change, or press [bold]b[/bold]ack""",
            default="b"
        )

        if choice == 'b':
            return args
        
        if choice == '1':
            date_str = Prompt.ask("Enter date (YYYY)", default=str(args.date) if args.date else "")
            try:
                args.date = datetime.strptime(date_str, "%Y").year
            except:
                console.print("[yellow]Warning: Date format should be YYYY. Date filter disabled.[/yellow]")
                args.date = None
            save_options(args)
        elif choice == '2':
            args.download_path = Path(Prompt.ask("Enter download path", default=str(args.download_path))).expanduser()
            save_options(args)
        elif choice == '3':
            min_str = Prompt.ask("Enter min issue number", default=str(args.min) if args.min else "")
            args.min = int(min_str) if min_str else None
            save_options(args)
        elif choice == '4':
            max_str = Prompt.ask("Enter max issue number", default=str(args.max) if args.max else "")
            args.max = int(max_str) if max_str else None
            save_options(args)
        elif choice == '5':
            results_str = Prompt.ask("Enter number of results", default=str(args.results))
            args.results = int(results_str) if results_str else 15
            save_options(args)
        elif choice == '6':
            args.verbose = not args.verbose
            console.print(f"Verbose output set to {args.verbose}")
            save_options(args)
