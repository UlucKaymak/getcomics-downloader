import requests
from bs4 import BeautifulSoup
from rich.console import Console

BASE_URL = "https://getcomics.info"

console = Console()

class GetComics:
    def __init__(self, query: str, results: str, verbose: bool, tag: str = None):
        self.query = query
        self.tag = tag
        self.num_results_desired = results
        self.verbose = verbose
        self.page = 1
        self.page_links = {}
        self.comic_links = {}

    def find_pages(self, date=None):
        if self.tag:
            url = f"{BASE_URL}/tag/{self.tag}/page/{self.page}"
        else:
            url = f"{BASE_URL}/page/{self.page}?s={self.query}"
        
        try:
            if self.verbose:
                console.print(f"Opening page {url}")
            response = requests.get(url)
        except Exception as e:
            console.print(f"Error contacting URL: {url}")
            console.print(e)
            return

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article")
        if len(articles) == 0:
            return

        for article in articles:
            title_tag = article.find("h1", {"class": "post-title"})
            title = title_tag.text
            link = title_tag.find("a")["href"]
            self.page_links[link] = title
        
        self.page += 1

    def get_download_links(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        for url, title in self.page_links.items():
            try:
                if self.verbose:
                    console.print(f"Opening page {url}")
                response = requests.get(url, headers=headers)
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
                    if "getcomics.info/download" in href or "getcomics.org/download" in href or "getcomics.org/dlds/" in href:
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
