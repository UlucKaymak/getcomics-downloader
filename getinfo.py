import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from rich.console import Console

BASE_URL = "https://getcomics.org"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

console = Console()

class GetComics:
    def __init__(self, query: str, results: str, verbose: bool):
        self.query = query
        # self.tag = tag
        self.num_results_desired = results
        self.verbose = verbose
        self.page = 1
        self.page_links = {}
        self.comic_links = {}

    def find_pages(self, date=None):
        url = f"{BASE_URL}/page/{self.page}?s={quote(self.query)}"

        try:
            if self.verbose:
                console.print(f"Opening page {url}")
            response = requests.get(url, headers=HEADERS, timeout=15)
        except Exception as e:
            console.print(f"Error contacting URL: {url}")
            console.print(e)
            return

        if response.status_code != 200:
            if self.verbose:
                console.print(f"[bold red]Request failed with status {response.status_code} for {url}[/bold red]")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article")
        if len(articles) == 0:
            if self.verbose:
                console.print(f"[bold red]No <article> elements found on {url} (page layout may have changed or request was blocked).[/bold red]")
            return

        for article in articles:
            title_tag = article.find("h1", {"class": "post-title"})
            if not title_tag:
                title_tag = article.find("h1")
            if not title_tag:
                continue
            link_tag = title_tag.find("a")
            if not link_tag or not link_tag.get("href"):
                continue
            title = title_tag.text.strip()
            link = link_tag["href"]
            self.page_links[link] = title

        self.page += 1

    def get_download_links(self):
        for url, title in self.page_links.items():
            try:
                if self.verbose:
                    console.print(f"Opening page {url}")
                response = requests.get(url, headers=HEADERS, timeout=15)
            except Exception as e:
                console.print(f"Error contacting URL: {url}")
                console.print(e)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            all_links = soup.find_all("a", href=True)
            direct_links_found = False
            for tag in all_links:
                href = tag['href']
                link_text = tag.get_text().upper()
                link_title = tag.get('title', '').upper()
                if "DOWNLOAD NOW" in link_text or "DOWNLOAD NOW" in link_title or "MAIN SERVER" in link_text:
                    if "getcomics.org/download" in href or "getcomics.org/dlds/" in href or "getcomics.org/dls/" in href:
                        self.comic_links[href] = title
                        direct_links_found = True
            if not direct_links_found:
                for tag in all_links:
                    href = tag['href']
                    link_text = tag.get_text().upper()
                    link_title = tag.get('title', '').upper()
                    if "MEDIAFIRE" in link_text or "MEDIAFIRE" in link_title:
                        self.comic_links[f"_MEDIAFIRE_{href}"] = title
            if not self.comic_links and self.verbose:
                console.print(f"No link found: {url}")
