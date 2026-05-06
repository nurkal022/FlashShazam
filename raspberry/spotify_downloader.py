import requests
import os
from datetime import datetime
from apify_client import ApifyClient
from config import Config


class SpotifyDownloader:
    """Скачивание музыки через Apify (easyapi/spotify-music-mp3-downloader)"""

    ACTOR_NAME = "easyapi/spotify-music-mp3-downloader"
    SEARCH_ACTOR_NAME = "automation-lab/spotify-scraper"

    def __init__(self):
        self.apify_client = ApifyClient(Config.APIFY_TOKEN)

    def search_spotify_url(self, track_name, artist_name):
        """Ищет Spotify URL по названию + артисту через Apify."""
        query = f"{artist_name} {track_name}".strip()
        print(f"[apify-search] {query}")

        run = self.apify_client.actor(self.SEARCH_ACTOR_NAME).call(
            run_input={
                "mode": "search",
                "searchTerms": [query],
                "searchType": "tracks",
                "maxResults": 5,
            }
        )
        if not run or not run.get("defaultDatasetId"):
            return None

        items = list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            return None

        artist_lc = (artist_name or "").lower()
        title_lc = (track_name or "").lower()
        for it in items:
            if (artist_lc in (it.get("artists", "") or "").lower()
                    and title_lc in (it.get("name", "") or "").lower()):
                return it.get("url")

        return items[0].get("url")

    def download_by_spotify_url(self, spotify_url):
        """Скачивает MP3 по Spotify URL через Apify актор"""
        try:
            print(f"[apify] Запуск: {spotify_url}")

            run = self.apify_client.actor(self.ACTOR_NAME).call(
                run_input={"links": [spotify_url]}
            )

            if not run:
                return {"success": False, "error": "Apify: запуск не удался"}

            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                return {"success": False, "error": "Apify: нет dataset"}

            items = list(self.apify_client.dataset(dataset_id).iterate_items())
            if not items:
                return {"success": False, "error": "Apify: пустой результат"}

            item = items[0]
            result = item.get("result", item)

            if result.get("error"):
                msg = result.get("message", "Трек не найден")
                return {"success": False, "error": f"Apify: {msg}"}

            title = result.get("title", "Unknown")
            thumbnail = result.get("thumbnail", "")
            medias = result.get("medias", [])

            if not medias or not medias[0].get("url"):
                return {"success": False, "error": "Apify: нет ссылки на MP3"}

            mp3_url = medias[0]["url"]
            return self._download_mp3(mp3_url, title, thumbnail)

        except Exception as e:
            print(f"[apify] Ошибка: {e}")
            return {"success": False, "error": str(e)}

    def _download_mp3(self, mp3_url, title, thumbnail=""):
        """Скачивает MP3 файл по прямой ссылке"""
        print(f"[download] {title}")

        resp = requests.get(mp3_url, stream=True, timeout=120)
        resp.raise_for_status()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        filename = f"{safe_title}_{timestamp}.mp3"
        filepath = os.path.join(Config.DOWNLOADS_DIR, filename)

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(filepath)
        print(f"[download] OK: {filename} ({file_size / 1024 / 1024:.1f} MB)")

        return {
            "success": True,
            "file_path": filepath,
            "filename": filename,
            "title": title,
            "thumbnail": thumbnail,
            "file_size": file_size,
        }

    def download_track(self, track_name, artist_name, spotify_url=None):
        """
        Скачивает трек.
        Если есть spotify_url — через Apify.
        Иначе — ошибка (нужен URL от Shazam).
        """
        if spotify_url:
            return self.download_by_spotify_url(spotify_url)

        found_url = self.search_spotify_url(track_name, artist_name)
        if found_url:
            print(f"[apify-search] найдено: {found_url}")
            return self.download_by_spotify_url(found_url)

        return {
            "success": False,
            "error": f"Не нашли «{track_name} - {artist_name}» в Spotify.",
        }
