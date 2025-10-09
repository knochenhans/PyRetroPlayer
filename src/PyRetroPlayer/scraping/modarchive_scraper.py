from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger

from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.scraping.scraper import Scraper


class ModArchiveScraper(Scraper):
    def scrape(self, song: Song) -> None:
        # Scrape page via bs4
        url = self.get_url(song)

        if not url:
            logger.warning(f"No ModArchive URL found for song: {song.file_path}")
            return

        response = self.session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            mod_page_ratings = soup.find("div", class_="mod-page-ratings")

            if mod_page_ratings:
                stats_li: List[Tag] = mod_page_ratings.find_all("li", class_="stats")

                if isinstance(stats_li, list) and len(stats_li) == 2:
                    ratings: Dict[str, str] = {}
                    member_rating = stats_li[0].get_text().split(":")[-1].strip()
                    reviewer_rating = stats_li[1].get_text().split(":")[-1].strip()
                    if member_rating != "(Unrated)":
                        ratings["member"] = member_rating
                    if reviewer_rating != "(Unrated)":
                        ratings["reviewer"] = reviewer_rating

                    self.scraped_data["ratings"] = ratings

            mod_page_archive_info = soup.find("div", class_="mod-page-archive-info")

            if mod_page_archive_info and isinstance(mod_page_archive_info, Tag):
                artist_tag = mod_page_archive_info.find(
                    "a", class_="standard-link", href=True
                )
                if artist_tag is not None:
                    self.scraped_data["artist"] = artist_tag.get_text(strip=True)

            mod_page_comments = soup.find("div", class_="mod-page-comments")

            if mod_page_comments:
                comments_data: List[Dict[str, str]] = []
                comments: List[Tag] = mod_page_comments.find_all(
                    "div", class_="comment-listing"
                )

                for comment in comments:
                    lines = comment.get_text().lstrip().rstrip().splitlines()
                    comment_data: Dict[str, str] = {}
                    comment_data["meta"] = lines[0].strip() if lines else ""
                    comment_data["content"] = (
                        lines[-1].strip() if len(lines) > 1 else ""
                    )
                    comments_data.append(comment_data)

                self.scraped_data["comments"] = comments_data

        self.apply_scraped_data_to_song(song)

    def get_url(self, song: Song) -> str:
        logger.info(f"Looking up ModArchive URL for song: {song.file_path}")

        def search_modarchive(query: str, search_type: str) -> Optional[str]:
            url = f"https://modarchive.org/index.php?request=search&query={query}&submit=Find&search_type={search_type}"
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                # Check if there are search results
                search_results_header = soup.find(
                    "h1", class_="site-wide-page-head-title", string="Search Results"
                )
                if search_results_header:
                    result = soup.find("a", class_="standard-link", href=True)
                    if result and isinstance(result, Tag):
                        href = result["href"]
                        if isinstance(href, list):
                            href = href[0]
                        return "https://modarchive.org/" + href
            return None

        filename = song.file_path.split("/")[-1]
        url = search_modarchive(filename, "filename")
        if not url:
            if song.title and song.title != "<no songtitle>":
                title_with_plus = song.title.replace(" ", "+")
                url = search_modarchive(title_with_plus, "filename_or_songtitle")
        return url if url else ""
