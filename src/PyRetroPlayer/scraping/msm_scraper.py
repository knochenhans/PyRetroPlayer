from bs4 import BeautifulSoup, Tag

from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.scraping.scraper import Scraper


class MSMScraper(Scraper):
    def scrape(self, song: Song) -> None:
        # Scrape page via bs4
        url = self.get_url(song)
        response = self.session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            page_div = soup.find("div", class_="details-wrap")

            current_section = ""

            # loop through all direct children of page_div
            if page_div:
                for child in page_div.find_all(recursive=False):
                    if isinstance(child, Tag):
                        match child.name:
                            case "div":
                                match child.get("class", [])[0]:
                                    case "details":
                                        match current_section:
                                            case "Instances":
                                                self.scraped_data["instances"] = (
                                                    self.scrape_table(child)
                                                )
                                            case "Links":
                                                self.scraped_data["links"] = (
                                                    self.scrape_links(child)
                                                )
                                            case "Samples":
                                                self.scraped_data["samples"] = (
                                                    self.scrape_table(child)
                                                )
                                            case "Similar sample set":
                                                pass
                                            case _:
                                                pass
                                        pass
                                    case _:
                                        pass
                            case "h1":
                                current_section = child.get_text(strip=True) or ""
                            case _:
                                pass

    def get_url(self, song: Song) -> str:
        return f"https://modsamplemaster.thegang.nu/module.php?sha1={song.sha1}"
