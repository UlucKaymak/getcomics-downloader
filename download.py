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

console = Console()

def download_comics(comic_links, download_path, verbose=False, prompt=True):
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
        file_name = create_file_name(str(download_path / file_name))
        
        if prompt and "n" in Prompt.ask(f"Download '{title}'?", choices=["y", "n"], default="y").lower():
            continue

        download_file(
            url, 
            filename=Path(file_name),
            verbose=True, 
            transient=True
        )
        console.print(f"'{title}' downloaded.")

def download_file(url, filename=None, chunk_size=1024, verbose=False, transient=False):
    response = requests.get(url, stream=True)

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
            transient=False
        )
        with progress:
            task_id = progress.add_task(
                description=destination.name,
                total=total_size_in_bytes,
                visible=verbose
            )
            for chunk in response.iter_content(chunk_size=chunk_size):
                max_length = max(console.width - 40, 15) 
                file_name_divided = "\\n".join(textwrap.wrap(destination.name, width=max_length))

                file.write(chunk)
                progress.update(task_id, description=file_name_divided, advance=chunk_size)
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
