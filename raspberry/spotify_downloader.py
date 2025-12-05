import requests
import time
import os
import base64
from datetime import datetime
from apify_client import ApifyClient
from config import Config


class SpotifyDownloader:
    """Скачивание музыки через Spotify API + Apify"""
    
    def __init__(self):
        self.apify_token = Config.APIFY_TOKEN
        # Новый actor (из примера)
        self.actor_id = "D50jl7rp34h8YHRWg"
        self.base_url = "https://api.apify.com/v2"
        
        # Spotify Web API
        self.spotify_client_id = Config.SPOTIFY_CLIENT_ID
        self.spotify_client_secret = Config.SPOTIFY_CLIENT_SECRET
        self._spotify_token = None
        self._token_expires = 0
        
        # Apify client
        self.apify_client = ApifyClient(self.apify_token)
    
    def _get_spotify_token(self):
        """Получает access token для Spotify API"""
        if self._spotify_token and time.time() < self._token_expires:
            return self._spotify_token
        
        print("🔑 Получаем Spotify access token...")
        
        auth_string = f"{self.spotify_client_id}:{self.spotify_client_secret}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения токена: {response.status_code}")
            return None
        
        token_data = response.json()
        self._spotify_token = token_data["access_token"]
        self._token_expires = time.time() + token_data.get("expires_in", 3600) - 60
        
        print("✅ Spotify token получен")
        return self._spotify_token
    
    def search_spotify(self, track_name, artist_name, limit=5):
        """Ищет трек в Spotify и возвращает список URL"""
        token = self._get_spotify_token()
        if not token:
            return []
        
        query = f"track:{track_name} artist:{artist_name}"
        print(f"🔍 Поиск в Spotify: {query}")
        
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": query, "type": "track", "limit": limit, "market": "US"}
        
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка поиска: {response.status_code}")
            return []
        
        tracks = response.json().get("tracks", {}).get("items", [])
        
        if not tracks:
            print("⚠️ Треки не найдены")
            return []
        
        results = []
        for track in tracks:
            url = track.get("external_urls", {}).get("spotify")
            if url:
                results.append({
                    'url': url,
                    'name': track.get("name"),
                    'artist': track.get("artists", [{}])[0].get("name")
                })
        
        if results:
            print(f"✅ Найдено {len(results)} треков")
        
        return results

    def download_by_spotify_url(self, spotify_url, retry=0):
        """Скачивает трек по Spotify URL через Apify (apify-client)"""
        try:
            print(f"🎵 Скачиваем: {spotify_url}" + (f" (попытка {retry + 1})" if retry > 0 else ""))

            run_input = {
                "links": [spotify_url],
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            }

            run = self.apify_client.actor(self.actor_id).call(run_input=run_input)
            if run is None:
                return {'success': False, 'error': 'Apify run failed'}

            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                return {'success': False, 'error': 'Нет defaultDatasetId'}

            results = list(self.apify_client.dataset(dataset_id).iterate_items())
            if not results:
                return {'success': False, 'error': 'Нет результатов от Apify'}

            track_result = results[0].get("result", {}) if isinstance(results[0], dict) else results[0]

            if track_result.get("error"):
                error_msg = track_result.get('message', 'Not found')
                if retry < 1 and "not found" in error_msg.lower():
                    print(f"⚠️ Не найдено, пробуем ещё...")
                    time.sleep(2)
                    return self.download_by_spotify_url(spotify_url, retry + 1)
                return {'success': False, 'error': error_msg}

            title = track_result.get('title', 'Unknown')
            thumbnail = track_result.get('thumbnail', '')
            medias = track_result.get('medias', [])

            if not medias:
                return {'success': False, 'error': 'Нет MP3'}

            mp3_url = medias[0].get('url')
            if not mp3_url:
                return {'success': False, 'error': 'Пустая ссылка'}

            print(f"📥 Скачиваем: {title}")
            mp3_response = requests.get(mp3_url, stream=True, timeout=120)
            mp3_response.raise_for_status()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_title}_{timestamp}.mp3"
            filepath = os.path.join(Config.DOWNLOADS_DIR, filename)

            with open(filepath, 'wb') as f:
                for chunk in mp3_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(filepath)
            print(f"✅ Скачано: {filename} ({file_size / 1024 / 1024:.2f} MB)")

            return {
                'success': True,
                'file_path': filepath,
                'filename': filename,
                'title': title,
                'thumbnail': thumbnail,
                'file_size': file_size
            }

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {'success': False, 'error': str(e)}

    def download_track(self, track_name, artist_name, spotify_url=None):
        """Скачивает трек. Если нет URL - ищет в Spotify"""
        if spotify_url:
            result = self.download_by_spotify_url(spotify_url)
            if result.get('success'):
                return result
            print("⚠️ Прямой URL не сработал, ищем...")
        
        # Ищем в Spotify
        tracks = self.search_spotify(track_name, artist_name, limit=3)
        
        if not tracks:
            return {'success': False, 'error': 'Трек не найден в Spotify'}
        
        # Пробуем скачать
        for i, track in enumerate(tracks):
            print(f"🎵 Пробуем [{i+1}]: {track['name']} - {track['artist']}")
            result = self.download_by_spotify_url(track['url'])
            if result.get('success'):
                return result
        
        return {'success': False, 'error': 'Не удалось скачать'}

