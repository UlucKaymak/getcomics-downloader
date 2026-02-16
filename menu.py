import argparse
import sys
from datetime import datetime
from pathlib import Path
import json
import os
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from download import is_aria2c_available

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
                if 'use_aria2c' not in options:
                    options['use_aria2c'] = False
                return argparse.Namespace(**options)
            except json.JSONDecodeError:
                console.print(f"[yellow]Warning: Could not read config file {CONFIG_FILE}. Using default options.[/yellow]")
                return None
    return None

def parse_arguments():
    if len(sys.argv) == 1:
        return None  # if no arguments provided trigger the menu

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
    parser.add_argument("-aria2c", "--a", dest="use_aria2c", action="store_true", default=False, help="Use aria2c for downloads")

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
    if hasattr(args, 'download_path'):
        args.download_path = Path(args.download_path).expanduser()
    else:
        args.download_path = Path("Downloads/Comics").expanduser()
    args.min = None if not hasattr(args, 'min') else args.min
    args.max = None if not hasattr(args, 'max') else args.max
    args.results = 15 if not hasattr(args, 'results') else args.results
    args.verbose = False if not hasattr(args, 'verbose') else args.verbose
    args.use_aria2c = False if not hasattr(args, 'use_aria2c') else args.use_aria2c
    
    while True:
        menu_choices = {"q": "Search by [bold]Q[/bold]uery", "o": "[bold]O[/bold]ptions"}
        if args.use_aria2c and is_aria2c_available():
            menu_choices["c"] = "[bold]C[/bold]ontinue interrupted downloads"
        
        choice_str = ", or ".join(menu_choices.values())
        choice = Prompt.ask(choice_str + "?", default="q")

        if choice.lower() == 'q':
            args.query = Prompt.ask(f"Enter search query (Leave empty to lookup last {args.results} comic)")
            return args
        elif choice.lower() == 'o':
            args = options_menu(args)
            continue 
        elif choice.lower() == 'c' and args.use_aria2c and is_aria2c_available():
            handle_interrupted_downloads(args.download_path, args.verbose)
            Prompt.ask("Press any key to return to the main menu")
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
        console.print(f"  [cyan]7. Use aria2c:[/cyan] {args.use_aria2c}")

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
        elif choice == '7':
            args.use_aria2c = not args.use_aria2c
            console.print(f"Use aria2c set to {args.use_aria2c}")
            save_options(args)

def handle_interrupted_downloads(download_path: Path, verbose: bool):
    console.print(f"[bold green]Scanning for interrupted downloads in {download_path}...[/bold green]")
    aria2_files = list(download_path.glob("*.aria2"))

    if not aria2_files:
        console.print("[yellow]No interrupted downloads (.aria2 files) found in this directory.[/yellow]")
        return

    aria2c_command = [
        "aria2c",
        "--continue",
    ]
    if not verbose:
        aria2c_command.append("--quiet")
    
    for aria2_file in aria2_files:
        aria2c_command.append(str(aria2_file))

    try:
        console.print(f"[bold green]Attempting to resume {len(aria2_files)} download(s) using aria2c...[/bold green]")

        subprocess.run(aria2c_command, check=True, cwd=download_path)
        console.print("[bold green]aria2c resume process completed.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]aria2c resume failed: {e}[/bold red]")
    except FileNotFoundError:
        console.print("[bold red]aria2c not found. Cannot resume downloads.[/bold red]")
