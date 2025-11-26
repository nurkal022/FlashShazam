import requests
import os
import re
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from config import Config

class SpotifyDownloader:
    def __init__(self):
        self.api_key = Config.RAPIDAPI_KEY
        self.api_host = Config.RAPIDAPI_HOST

    def search_spotify_track(self, track_name, artist_name):
        """Ищет трек через Spotify API"""
        try:
            query = f"{track_name} {artist_name}"
            
            url = f"https://{self.api_host}/search"
            querystring = {
                "q": query,
                "type": "multi",
                "limit": "5",
                "offset": "0",
                "noOfTopResults": "5"
            }
            
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host
            }
            
            print(f"Поиск трека: {query}")
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            print(f"Статус поиска: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Ответ API поиска (кратко): success={result.get('success')}, data keys={list(result.get('data', {}).keys())}")
                
                # Ищем в результатах треки (сначала topResults, потом tracks)
                data = result.get('data', {})
                tracks = data.get('topResults', {}).get('items', [])
                
                # Фильтруем только треки (type='track')
                tracks = [t for t in tracks if t.get('type') == 'track']
                
                if not tracks:
                    # Если в topResults нет, ищем в tracks
                    tracks = data.get('tracks', {}).get('items', [])
                
                if tracks:
                    # Берем первый трек
                    track = tracks[0]
                    # URI формат: spotify:track:ID -> преобразуем в URL
                    uri = track.get('uri', '')
                    if uri.startswith('spotify:track:'):
                        track_id = uri.replace('spotify:track:', '')
                        spotify_url = f'https://open.spotify.com/track/{track_id}'
                    else:
                        spotify_url = track.get('external_urls', {}).get('spotify', '')
                    
                    if spotify_url:
                        print(f"Найден трек: {track.get('name')} от {track.get('artists', {}).get('items', [{}])[0].get('profile', {}).get('name', 'unknown')}")
                        print(f"Spotify URL: {spotify_url}")
                        return {'success': True, 'spotify_url': spotify_url, 'track_data': track}
                
                return {'success': False, 'error': 'Треки не найдены в результатах поиска'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:200]}'}
                
        except Exception as e:
            print(f"Ошибка поиска трека: {e}")
            return {'success': False, 'error': str(e)}

    def download_from_spotify(self, spotify_url):
        """Скачивает трек через Spotify Downloader API"""
        try:
            url = f"https://{self.api_host}/downloadSong"
            querystring = {"songId": spotify_url}
            
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host
            }
            
            print(f"Запрос к API: {url} с songId: {spotify_url}")
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            print(f"Статус ответа: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Ответ API: {result}")

                # Проверяем формат ответа
                download_link = result.get('data', {}).get('downloadLink') or result.get('downloadLink') or result.get('url')
                
                if download_link:
                    print(f"Найдена ссылка на скачивание: {download_link[:100]}...")
                    
                    # Скачиваем файл
                    file_response = requests.get(download_link, stream=True, timeout=60)
                    file_response.raise_for_status()
                    
                    # Определяем имя файла
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Получаем метаданные
                    data = result.get('data', result)
                    title = data.get('title') or data.get('name') or 'unknown'
                    artist = data.get('artist') or (data.get('artists', [{}])[0].get('name') if data.get('artists') else 'unknown') or 'unknown'
                    
                    safe_filename = f"{title} - {artist}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                    filename = f"{safe_filename}_{timestamp}.mp3"
                    filepath = os.path.join(Config.DOWNLOADS_DIR, filename)
                    
                    # Сохраняем файл
                    print(f"Скачивание файла в: {filepath}")
                    with open(filepath, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    print(f"Файл скачан: {filepath}")
                    
                    # Добавляем метаданные
                    cover_url = data.get('cover') or data.get('cover_url') or data.get('image')
                    try:
                        self._add_metadata(filepath, title, artist, cover_url)
                    except Exception as e:
                        print(f"Не удалось добавить метаданные: {e}")
                    
                    return {
                        'success': True,
                        'file_path': filepath,
                        'filename': filename,
                        'name': title,
                        'artists': [artist] if isinstance(artist, str) else artist,
                        'cover': cover_url,
                        'album': data.get('album'),
                        'release_date': data.get('releaseDate') or data.get('release_date')
                    }
                else:
                    return {'success': False, 'error': f'Ссылка на скачивание не найдена в ответе API. Ответ: {str(result)[:300]}'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:200]}'}

        except Exception as e:
            print(f"Ошибка скачивания с Spotify: {e}")
            return {'success': False, 'error': str(e)}
    
    def _add_metadata(self, mp3_path, title, artist, cover_url=None):
        """Добавляет метаданные в MP3 файл"""
        try:
            audio = MP3(mp3_path, ID3=ID3)
            
            # Добавляем теги
            audio.tags.add(TIT2(encoding=3, text=title))
            audio.tags.add(TPE1(encoding=3, text=artist))
            
            # Скачиваем и добавляем обложку
            if cover_url:
                try:
                    response = requests.get(cover_url, timeout=5)
                    if response.status_code == 200:
                        audio.tags.add(APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=response.content
                        ))
                except:
                    pass  # Игнорируем ошибки обложки
            
            audio.save()
        except Exception as e:
            print(f"Ошибка добавления метаданных: {e}")
    
    def download_track(self, track_name, artist_name):
        """Скачивает трек через Spotify API"""
        print(f"Скачивание через Spotify API: {track_name} - {artist_name}")

        # Ищем через API
        print("Ищем трек через API...")
        search_result = self.search_spotify_track(track_name, artist_name)
        if search_result.get('success'):
            spotify_url = search_result['spotify_url']
        else:
            return {
                'success': False,
                'error': f'Не удалось найти трек через API: {search_result.get("error")}',
                'name': track_name,
                'artists': [artist_name]
            }

        print(f"Используем Spotify URL: {spotify_url}")

        # Скачиваем через Spotify API
        return self.download_from_spotify(spotify_url)
