import requests
import time
import os
import base64
from datetime import datetime
from apify_client import ApifyClient
from config import Config


class SpotifyDownloader:
    """Скачивание музыки через Apify Spotify Music MP3 Downloader"""
    
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
        """Получает access token для Spotify API (Client Credentials Flow)"""
        if self._spotify_token and time.time() < self._token_expires:
            return self._spotify_token
        
        print("🔑 Получаем Spotify access token...")
        
        auth_string = f"{self.spotify_client_id}:{self.spotify_client_secret}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data=data,
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
        params = {
            "q": query,
            "type": "track",
            "limit": limit,
            "market": "US"
        }
        
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка поиска: {response.status_code}")
            return []
        
        data = response.json()
        tracks = data.get("tracks", {}).get("items", [])
        
        if not tracks:
            print("⚠️ Треки не найдены")
            return []
        
        # Возвращаем список URL
        results = []
        for track in tracks:
            url = track.get("external_urls", {}).get("spotify")
            name = track.get("name")
            artist = track.get("artists", [{}])[0].get("name")
            if url:
                results.append({
                    'url': url,
                    'name': name,
                    'artist': artist
                })
        
        if results:
            print(f"✅ Найдено {len(results)} треков")
            print(f"🔗 Первый: {results[0]['name']} - {results[0]['artist']}")
        
        return results

    def download_by_spotify_url(self, spotify_url, retry=0):
        """Скачивает трек по Spotify URL через Apify (через apify-client)"""
        try:
            print(f"🎵 Запускаем скачивание: {spotify_url}" + (f" (попытка {retry + 1})" if retry > 0 else ""))

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
                error_msg = track_result.get('message', 'Трек не найден')
                if retry < 1 and "not found" in error_msg.lower():
                    print(f"⚠️ Не найдено, пробуем ещё раз...")
                    time.sleep(2)
                    return self.download_by_spotify_url(spotify_url, retry + 1)
                return {'success': False, 'error': error_msg}

            title = track_result.get('title', 'Unknown')
            thumbnail = track_result.get('thumbnail', '')
            medias = track_result.get('medias', [])

            if not medias:
                return {'success': False, 'error': 'Нет ссылки на MP3'}

            mp3_url = medias[0].get('url')
            if not mp3_url:
                return {'success': False, 'error': 'Пустая ссылка на MP3'}

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
            print(f"❌ Ошибка скачивания: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def search_and_download(self, track_name, artist_name):
        """
        Ищет трек в Spotify API по названию и скачивает через Apify.
        Пробует несколько вариантов если первый не сработал.
        """
        try:
            print(f"🔍 Ищем в Spotify: {track_name} - {artist_name}")
            
            # Ищем треки через Spotify Web API
            tracks = self.search_spotify(track_name, artist_name, limit=5)
            
            if not tracks:
                # Если не нашли - возвращаем поисковую ссылку
                import urllib.parse
                search_query = f"{track_name} {artist_name}"
                encoded_query = urllib.parse.quote(search_query)
                spotify_search_url = f"https://open.spotify.com/search/{encoded_query}"
                
                return {
                    'success': False,
                    'error': 'Трек не найден в Spotify',
                    'spotify_search_url': spotify_search_url,
                    'title': track_name,
                    'artist': artist_name
                }
            
            # Пробуем скачать каждый вариант пока не получится
            last_error = None
            for i, track in enumerate(tracks[:3]):  # Максимум 3 попытки
                print(f"🎵 Пробуем [{i+1}]: {track['name']} - {track['artist']}")
                result = self.download_by_spotify_url(track['url'])
                
                if result.get('success'):
                    return result
                else:
                    last_error = result.get('error')
                    print(f"   ⚠️ Не удалось: {last_error}")
            
            # Если ничего не сработало
            import urllib.parse
            search_query = f"{track_name} {artist_name}"
            encoded_query = urllib.parse.quote(search_query)
            spotify_search_url = f"https://open.spotify.com/search/{encoded_query}"
            
            return {
                'success': False,
                'error': last_error or 'Не удалось скачать трек',
                'spotify_search_url': spotify_search_url,
                'title': track_name,
                'artist': artist_name
            }
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _try_common_track_ids(self, track_name, artist_name):
        """Пробует скачать по известным ID для популярных треков"""
        # Известные Spotify track IDs для популярных треков
        known_tracks = {
            'the show must go on': '4K1hoMqLgxLVBphQhxQfcM',  # Queen - The Show Must Go On
            'we will rock you': '54flyrjcdnQdco7300avMJ',    # Queen - We Will Rock You
            'bohemian rhapsody': '7tFiyTwD0nx5a1eklYtX2J',   # Queen - Bohemian Rhapsody
            'dont stop me now': '5T8EDUDqKcs6OSOwEsfqG7',    # Queen - Don't Stop Me Now
            'somebody to love': '0fDF2c8skOsczCJQSWXQtD',    # Queen - Somebody To Love
            'i want to break free': '4VMYDCV2IEDYJArNxUaFjT', # Queen - I Want To Break Free
        }
        
        track_lower = track_name.lower()
        for known_name, track_id in known_tracks.items():
            if known_name in track_lower:
                spotify_url = f'https://open.spotify.com/track/{track_id}'
                print(f"🎯 Используем известный ID: {spotify_url}")
                return self.download_by_spotify_url(spotify_url)
        
        return {'success': False, 'error': f'Трек "{track_name}" не найден. Нужен Spotify URL.'}

    def download_track(self, track_name, artist_name, spotify_url=None):
        """
        Скачивает трек. Если есть spotify_url - использует его напрямую.
        Иначе ищет по названию.
        """
        if spotify_url:
            result = self.download_by_spotify_url(spotify_url)
            if result.get('success'):
                return result
            # Если прямой URL не сработал, пробуем поиск
            print(f"⚠️ Прямой URL не сработал, пробуем поиск...")
        
        # Ищем и скачиваем по названию
        return self.search_and_download(track_name, artist_name)

