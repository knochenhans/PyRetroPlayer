from typing import Any, Dict, List

import requests
from bs4 import Tag
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from PyRetroPlayer.playlist.song import Song


class Scraper:
    def __init__(self) -> None:
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)

        self.scraped_data: Dict[str, Any] = {}

    def scrape(self, song: Song) -> None:
        raise NotImplementedError("Subclasses must implement this method")

    def scrape_links(self, child: Tag) -> List[Dict[str, str]]:
        links: List[Dict[str, str]] = []
        for li in child.find_all("li"):
            a_tag = li.find("a", href=True)
            if a_tag:
                links.append(
                    {
                        "text": a_tag.get_text(strip=True),
                        "url": a_tag["href"],
                    }
                )
        return links

    def scrape_table(self, table: Tag) -> List[Dict[str, str]]:
        # Extract headers if present
        headers: List[str] = []
        header_row = table.find("tr")
        if header_row:
            ths = header_row.find_all("th")
            if ths:
                headers = [th.get_text(strip=True) for th in ths]

        rows_data: List[Dict[str, str]] = []
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if headers and len(cols) == len(headers):
                # Use headers as keys
                row_data = {
                    headers[i]: cols[i].get_text(strip=True)
                    for i in range(len(headers))
                }
                rows_data.append(row_data)
            elif len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                rows_data.append({key: value})
        return rows_data
    
    def apply_scraped_data_to_song(self, song: Song) -> None:
        song.custom_metadata = {}
        for key, value in self.scraped_data.items():
            if key == "artist" and isinstance(value, str):
                song.artist = value
            else:
                song.custom_metadata[key] = value
    
    def reset(self) -> None:
        self.scraped_data = {}
