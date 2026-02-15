#!/usr/bin/env python3
import sys

from rich.console import Console
from rich.panel import Panel

from getinfo import GetComics
from download import download_comics
from menu import parse_arguments, interactive_main_menu, show_interactive_menu

console = Console()

def main():
    try:
        console.clear()
        
        # ASCII Art Title
        console.print()
        console.print("=" * 70)
        console.print("""[bold purple]
          ____      _    ____                _                   
         / ___| ___| |_ / ___|___  _ __ ___ (_) ___ ___          
        | |  _ / _ \ __| |   / _ \| '_ ` _ \| |/ __/ __|         
        | |_| |  __/ |_| |__| (_) | | | | | | | (__\__ \         
        \____|\___|\__|\____\___/|_| |_| |_|_|\___|___/         
        |  _ \  _____      ___ __ | | ___   __ _  __| | ___ _ __ 
        | | | |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|
        | |_| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |   
        |____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|  [/bold purple]
                    """)
        console.print("    GetComicsDownloader v1.0 by UlucKaymak")
        console.print()
        console.print("=" * 70)
        console.print()

        args = parse_arguments()
        if args is None:
            args = interactive_main_menu()
            if args is None:
                console.print("[yellow]Exiting.[/yellow]")
                return
        
        # Directory check
        if not args.download_path.exists():
            args.download_path.mkdir(parents=True, exist_ok=True)

        if args.tag:
            search_query = args.tag
        else:
            search_query = args.query
            if args.min is not None:
                search_query = f"{args.query} {args.min}"
        
        comics = GetComics(search_query, args.results, args.verbose, tag=args.tag)
        
        while True:
            with console.status(f"[bold green]Scanning GetComics: {search_query} (Page {comics.page})..."):
                comics.find_pages(date=args.date)
                comics.get_download_links()

            selected_comics = show_interactive_menu(comics.comic_links, search_query)

            if selected_comics == "next":
                comics.comic_links.clear()
                comics.page_links.clear()
                continue
            
            if not selected_comics:
                console.print("[yellow]Exiting without downloading.[/yellow]")
                return

            download_comics(dict(selected_comics), args.download_path, args.verbose, prompt=False)
            break

    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")
        sys.exit(1)
if __name__ == "__main__":
    main()
