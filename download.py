import re
import shutil
import tempfile
import textwrap
from pathlib import Path
from urllib.parse import unquote

import requests
from rich.console import Console
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.prompt import Prompt
import subprocess

console = Console()

def is_aria2c_available() -> bool:
    try:
        subprocess.run(
            ["aria2c", "--version"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_comics(comic_links, download_path, verbose=False, prompt=True, use_aria2c=False):
    for i, (url, title) in enumerate(comic_links.items()):
        if url.startswith("_MEDIAFIRE_"):
            mediafire_url = url[url.index('http'):]
            console.print(f"""{title}:
Please download from the following Mediafire link:
[link={mediafire_url}]{mediafire_url}[/link]""")
            continue
        
        if verbose:
            console.print(f"Downloading {title} from {url}")

        if "." not in url.rpartition("/")[-1]:
            url = requests.head(url, allow_redirects=True).url
        
        file_name = safe_filename(unquote(url.rpartition("/")[-1]))
        
        if not use_aria2c: # apply create_file_name if not using aria
            file_name = create_file_name(str(download_path / file_name))
        else:
            file_name = str(download_path / file_name) #full path string for aria
        
        if prompt and "n" in Prompt.ask(f"Download '{title}'?", choices=["y", "n"], default="y").lower():
            continue

        download_file(
            url, 
            filename=Path(file_name),
            verbose=True, 
            transient=True,
            use_aria2c=use_aria2c
        )
        console.print(f"'{title}' downloaded.")

def download_file(url, filename=None, chunk_size=1024, verbose=False, transient=False, use_aria2c=False):
    destination = filename
    temp_file = Path(tempfile.gettempdir()) / filename.name

    if use_aria2c and is_aria2c_available():
        try:
            aria2c_command = [
                "aria2c",
                "--console-log-level=warn",
                "--summary-interval=0",
                "-d", str(destination.parent),
                "-o", destination.name,
                url
            ]
            if not verbose:
                aria2c_command.insert(1, "--quiet")

            console.print(f"[bold green]Downloading with aria2c: {destination.name}[/bold green]")
            subprocess.run(aria2c_command, check=True)
            return
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]aria2c download failed: {e}[/bold red]")
            console.print("[yellow]Falling back to requests download.[/yellow]")
        except FileNotFoundError:
            console.print("[bold red]aria2c not found. Falling back to requests download.[/bold red]")

    response = requests.get(url, stream=True)

    if response.history:
        filename = Path(unquote(Path(response.url).name))
    destination = filename
    temp_file = Path(tempfile.gettempdir()) / filename.name
    
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    
    if verbose:
        console.print(f"[bold cyan]{destination.name}[/bold cyan]")

    with open(temp_file, "wb") as file:
        progress = Progress(
            BarColumn(bar_width=None), 
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(binary_units=True),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(compact=True),
            disable=not verbose,
            transient=transient
        )
        
        with progress:
            task_id = progress.add_task(
                description="", 
                total=total_size_in_bytes,
                visible=verbose
            )
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                progress.update(task_id, advance=len(chunk))
                
    temp_file.replace(destination)

def safe_filename(filename: str) -> str:
    return re.sub(r"[\\/\\:\\*\\?\\\"<>\\|]", "", filename)

def create_file_name(filename: str) -> str:
    filename = filename.replace("\\\\", "/")
    if not Path(filename).exists():
        return filename
    
    if "/" in filename:
        directories, _, filename = filename.rpartition("/") 
        directories += "/"
    else:
        directories = ""
    
    if "." in filename:
        stem, _, suffix = filename.rpartition(".")
        suffix = "." + suffix
    else:
        stem, suffix = filename, ""

    num = 0
    while Path(f"{directories}{stem} ({num}){suffix}").exists():
        num += 1
    return f"{directories}{stem} ({num}){suffix}"
