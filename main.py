#!/usr/bin/env python3
import argparse
import re
import shutil
import sys
import tempfile
import textwrap

from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, unquote

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn


BASE_URL = "https://getcomics.info"

console = Console()

class Query:
    """
    Object to take a user's search string and provide an interface to getcomics.info results 
    """
    def __init__(self, query: str, results: str, verbose: bool, download_path: Path, tag: str = None):
        self.query = query
        self.tag = tag
        self.num_results_desired = results
        self.verbose = verbose
        self.download_path = download_path
        self.page_links = {}  # pages hosting comics, dict[str, str]: url, title
        self.comic_links = {} # actual links to comics, dict[str, str]: url, title

    def find_pages(self, date=None, tag=None):
        """
        Uses the search query or tag to find pages that can later be parsed for download links.

        date (None | datetime): date to look for in search results, or newer
        tag (None | str): tag to search for
        """
        # treat 0 as infinite desired results
        page = 0
        while self.num_results_desired == 0 or len(self.page_links) < self.num_results_desired:
            page += 1
            if self.tag:
                url = f"{BASE_URL}/tag/{self.tag}/page/{page}"
            else:
                url = f"{BASE_URL}/page/{page}?s={quote_plus(self.query)}"
            try:
                if self.verbose: console.print(f"Opening page {url}")
                response = requests.get(url)
            except Exception as e:
                console.print(f"Error contacting URL: {url}")
                console.print(e)
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article")
            if len(articles) == 0:
                return

            for article in articles:
                title_tag = article.find("h1", {"class": "post-title"})
                title = title_tag.text
                link = title_tag.find("a")["href"]
                article_time = article.find("time")["datetime"]
                
                if date:
                    year, month, day = article_time.split("-")  # should be in the format "2023-10-08" for Oct 8 2023
                    if datetime(year=int(year), month=int(month), day=int(day)) < date:
                        return  # don't bother looking at more articles because the articles are sorted by date
                self.page_links[link] = title

        if self.verbose:
            console.print(f"{len(self.page_links):,} pages found containing matching comics.")

    def get_download_links(self):
            # Added header to bypass bot protection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            for url, title in self.page_links.items():
                try:
                    if self.verbose: console.print(f"Opening page {url}")
                    response = requests.get(url, headers=headers) # Header added
                except Exception as e:
                    console.print(f"Error contacting URL: {url}")
                    console.print(e)
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                
                # 1. New Button Structure: The site now usually uses 'aio-redirection' class
                # or hides 'DOWNLOAD NOW' text with different tags.
                
                # Let's do a broader search:
                all_links = soup.find_all("a", href=True)
                found_on_page = False

                for tag in all_links:
                    href = tag['href']
                    link_text = tag.get_text().upper()
                    link_title = tag.get('title', '').upper()

                    # Keywords to catch download links
                    if "DOWNLOAD NOW" in link_text or "DOWNLOAD NOW" in link_title or "MAIN SERVER" in link_text:
                        if "getcomics.info/download" in href or "getcomics.org/download" in href or "getcomics.org/dlds/" in href:
                            self.comic_links[href] = title
                            found_on_page = True
                    
                    # Catch Mediafire alternative
                    elif "MEDIAFIRE" in link_text or "MEDIAFIRE" in link_title:
                        self.comic_links[f"_MEDIAFIRE_{href}"] = title
                        found_on_page = True

                if not found_on_page and self.verbose:
                    console.print(f"No link found: {url}")

    def download_comics(self, prompt=True):
        """
        Downloads comics that have been found 
        """        
        for i, (url, title) in enumerate(self.comic_links.items()):
            if url.startswith("_MEDIAFIRE_"):
                mediafire_url = url[url.index('http'):]
                console.print(f"{title}:\\nPlease download from the following Mediafire link:\\n[link={mediafire_url}]{mediafire_url}[/link]")
                continue
            
            if self.verbose: console.print(f"Downloading {title} from {url}")

            # if url doesn't look like a direct file link (some are encoded) try and get file name from the redirect
            if "." not in url.rpartition("/")[-1]:
                url = requests.head(url, allow_redirects=True).url
            
            file_name = self.safe_filename(unquote(url.rpartition("/")[-1]))
            file_name = self.create_file_name(str(self.download_path / file_name))
            
            if prompt and "n" in Prompt.ask(f"Download '{title}'?", choices=["y", "n"], default="y").lower():
                continue

            self.download_file(
                url, 
                filename=Path(file_name),
                verbose=True, 
                transient=True
            )
            console.print(f"'{title}' downloaded.")

    def download_file(self, url, filename=None, chunk_size=1024, verbose=False, transient=False):
        """
        url (str): url to download
        filename (Path): path to save as
        verbose (bool): whether or not to display the progress bar
        transient: make the progress bar disappear on completion
        
        Downloads file to OS temp directory, then renames to the final given destination
        """
        response = requests.get(url, stream=True)

        # check if a redirect occurred because it could affect the file name being saved (issue #13)
        if response.history:
            filename = Path(unquote(Path(response.url).name))
        destination = filename
        temp_file = Path(tempfile.gettempdir()) / filename.name
        
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        with open(temp_file, "wb") as file:
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                TimeRemainingColumn(compact=True),
                BarColumn(bar_width=20),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(binary_units=True),
                "•",
                TransferSpeedColumn(),
                disable=not verbose,
                transient=transient
            )
            with progress:
                task_id = progress.add_task(
                    description=destination.name,
                    total=total_size_in_bytes,
                    visible=not self.verbose
                )
                for chunk in response.iter_content(chunk_size=chunk_size):
                    # set up the progress bar so it has the best chance to be displayed nicely, allowing for terminal resizing
                    columns_width = 60 # generally, the Text/TimeRemaining/Bar/Download/TransferSpeed Columns take up this much room
                    terminal_width = shutil.get_terminal_size().columns
                    max_length = max(terminal_width - columns_width, 10)
                    file_name_divided = "\n".join(textwrap.wrap(destination.name, width=max_length))

                    file.write(chunk)
                    progress.update(task_id, description=file_name_divided, advance=chunk_size)
        temp_file.replace(destination)

    def safe_filename(self, filename: str) -> str:
        """Returns the filename with characters like \:*?"<>| removed."""
        return re.sub(r"[\/\\\:\*\?\"\<\>\|]", "", filename)

    def create_file_name(self, filename: str) -> str:
        """ 
        Checks to see if a file already exists.
        If it does, returns a string path with a unique name that does not exist
        as per the Windows standard ("temp.py" when exists returns "temp (0).py")
        
        :Parameters:
        filename (str) - path to be checked
        
        :Returns:
        filename (str) - unique filename
        """
        filename = filename.replace("\\", "/")
        if not Path(filename).exists():
            return filename
        
        # account for "." in directory structure
        if "/" in filename:
            directories, _, filename = filename.rpartition("/") 
            directories += "/"
        else:
            directories = ""
        
        # break down the filename into its parts
        if "." in filename:
            stem, _, suffix = filename.rpartition(".")
            suffix = "." + suffix
        else:
            stem, suffix = filename, ""

        num = 0
        while Path(f"{directories}{stem} ({num}){suffix}").exists():
            num += 1
        return f"{directories}{stem} ({num}){suffix}"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Search for and/or download content from getcomics.info."
    )
    parser.add_argument("query", type=str, nargs='?', default=None, help="Search term for comics")
    parser.add_argument("-t", "--tag", dest="tag", type=str, default=None, help="Search by tag")
    parser.add_argument("-date", "--d", dest='date', type=str, default=None, help="Get newer ones (YYYY-MM-DD)")
    parser.add_argument("-output", "--o", dest="download_path", type=str, default="./", help='Download directory')
    parser.add_argument("-min", dest="min", type=int, default=None, help="Minimum issue number")
    parser.add_argument("-max", dest="max", type=int, default=None, help="Maximum issue number")
    parser.add_argument("-results", "--r", dest="results", type=int, default=15, help="Number of results to show")
    parser.add_argument("-verbose", "--v", dest="verbose", action="store_true", default=False, help="Detailed output")

    args = parser.parse_args()
    args.download_path = Path(args.download_path).expanduser()

    if not args.query and not args.tag:
        parser.error("You must provide a search query or a tag.")
    
    if args.query and args.tag:
        parser.error("You can only provide a search query or a tag, not both.")
    
    if args.date:
        # Simple date check
        try:
            args.date = datetime.strptime(args.date.replace("/", "-").replace(".", "-"), "%Y-%m-%d")
        except:
            console.print("[yellow]Warning: Date format should be YYYY-MM-DD. Date filter disabled.[/yellow]")
            args.date = None

    return args

def show_interactive_menu(query_obj, search_term):
    """
    Shows results in a table and lets the user choose.
    """
    if not query_obj.comic_links:
        console.print(f"[bold red]No downloadable links found for '{search_term}'.[/bold red]")
        return []

    table = Table(
        title=f"\n[bold magenta]Results for: {search_term}[/bold magenta]",
        show_header=True, 
        header_style="bold cyan",
        border_style="bright_black"
    )
    table.add_column("No", style="dim", width=4, justify="center")
    table.add_column("Comic Title", style="white")
    table.add_column("Source", width=12, justify="center")

    comics_list = []
    for i, (url, title) in enumerate(query_obj.comic_links.items(), 1):
        is_mediafire = url.startswith("_MEDIAFIRE_")
        source_type = "[yellow]Mediafire[/yellow]" if is_mediafire else "[green]Direct[/green]"
        table.add_row(str(i), title, source_type)
        comics_list.append((url, title))

    console.print(table)
    
    choice = Prompt.ask(
        "\nEnter numbers to download (e.g. [bold]1,3[/bold]), [bold]'a'[/bold] for all, [bold]'q'[/bold] to quit",
        default="q"
    )

    if choice.lower() == 'q':
        return []
    if choice.lower() == 'a':
        return comics_list
    
    try:
        indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()]
        return [comics_list[i] for i in indices if 0 <= i < len(comics_list)]
    except:
        return []

def main():
    args = parse_arguments()
    
    # Directory check
    if not args.download_path.exists():
        args.download_path.mkdir(parents=True, exist_ok=True)

    try:
        if args.tag:
            search_query = args.tag
        else:
            # Adjust search query based on min/max parameters
            search_query = args.query
            if args.min is not None:
                search_query = f"{args.query} {args.min}"
        
        query = Query(search_query, args.results, args.verbose, args.download_path, tag=args.tag)
        
        with console.status(f"[bold green]Scanning GetComics: {search_query}..."):
            query.find_pages(date=args.date)
            query.get_download_links()

        # Interactive Selection Menu
        selected_comics = show_interactive_menu(query, search_query)

        if not selected_comics:
            console.print("[yellow]Exiting without downloading.[/yellow]")
            return

        # Download only selected ones
        for url, title in selected_comics:
            console.print(Panel(f"[bold blue]Processing:[/bold blue] {title}", border_style="blue"))
            
            # Temporarily modify Query object for this file
            temp_query = Query(title, 1, args.verbose, args.download_path)
            temp_query.comic_links = {url: title}
            temp_query.download_comics(prompt=False)

    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()