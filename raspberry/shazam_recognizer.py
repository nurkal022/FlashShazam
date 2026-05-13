import requests
import time
import os
from config import Config


class ShazamRecognizer:
    """Распознавание музыки через Shazam API (shazam-api.com)"""
    
    def __init__(self):
        self.api_key = Config.SHAZAM_API_KEY
        self.api_url = "https://shazam-api.com/api/recognize"
        self.results_url = "https://shazam-api.com/api/results/"

    def recognize_file(self, audio_file_path):
        """Распознает трек из аудио файла через Shazam API"""
        if not os.path.exists(audio_file_path):
            return {'success': False, 'error': 'Аудио файл не найден'}

        headers = {'Authorization': f'Bearer {self.api_key}'}

        try:
            print(f"🔍 Отправляем запрос к Shazam API...")
            print(f"📁 Файл: {audio_file_path} ({os.path.getsize(audio_file_path)} bytes)")
            
            with open(audio_file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(self.api_url, headers=headers, files=files, timeout=30)

            print(f"📡 Статус: {response.status_code}")
            
            if response.status_code == 403:
                error_data = response.json()
                return {'success': False, 'error': error_data.get('message', 'Доступ запрещен (403)')}
            
            response.raise_for_status()
            initial_response = response.json()

            if initial_response.get('status') == 'processing' and initial_response.get('uuid'):
                uuid = initial_response['uuid']
                print(f"✅ UUID: {uuid}")
                print("🔄 Ожидаем результаты...")

                # Ожидаем результаты
                for attempt in range(15):
                    time.sleep(2)
                    results_response = requests.post(f"{self.results_url}{uuid}", headers=headers, timeout=10)
                    results_response.raise_for_status()
                    results_data = results_response.json()

                    if results_data.get('status') == 'finished':
                        if results_data.get('results'):
                            track_info = results_data['results'][0].get('track', {})
                            if track_info:
                                return self._parse_track_info(track_info)
                        return {'success': False, 'error': 'Трек не распознан'}
                    
                    elif results_data.get('status') == 'error':
                        return {'success': False, 'error': results_data.get('error', 'Ошибка API')}
                    
                    print(f"   Обработка... (попытка {attempt + 1})")

                return {'success': False, 'error': 'Таймаут ожидания результатов'}
            else:
                return {'success': False, 'error': initial_response.get('error', 'Неизвестная ошибка')}

        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Ошибка запроса: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'Ошибка: {e}'}

    def _parse_track_info(self, track_info):
        """Парсит информацию о треке из ответа Shazam"""
        title = track_info.get('title', 'Unknown')
        artist = track_info.get('subtitle', 'Unknown')
        
        # Обложка
        cover_url = track_info.get('images', {}).get('coverarthq') or \
                    track_info.get('images', {}).get('coverart', '')
        
        # Spotify URL
        spotify_url = ''
        if 'hub' in track_info and 'providers' in track_info['hub']:
            for provider in track_info['hub']['providers']:
                if provider.get('type') == 'SPOTIFY' and 'actions' in provider:
                    for action in provider['actions']:
                        if action.get('type') == 'uri' and action.get('uri', '').startswith('spotify:track:'):
                            spotify_url = action['uri'].replace('spotify:track:', 'https://open.spotify.com/track/')
                            break
                if spotify_url:
                    break
        
        # Apple Music URL
        apple_music_url = ''
        if 'hub' in track_info and 'options' in track_info['hub']:
            for option in track_info['hub']['options']:
                if option.get('providername') == 'applemusic' and 'actions' in option:
                    for action in option['actions']:
                        if action.get('type') == 'applemusicopen':
                            apple_music_url = action.get('uri', '')
                            break
                if apple_music_url:
                    break

        print(f"✅ Распознано: {title} - {artist}")
        if cover_url:
            print(f"🖼️ Обложка: {cover_url[:50]}...")

        return {
            'success': True,
            'title': title,
            'artist': artist,
            'cover_url': cover_url,
            'spotify_url': spotify_url,
            'apple_music_url': apple_music_url,
            'shazam_key': track_info.get('key', '')
        }

