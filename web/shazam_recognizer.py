import requests
import os
import time
from config import Config


class ShazamRecognizer:
    """Распознавание музыки через Shazam API (shazam-api.com)"""
    
    def __init__(self):
        self.api_key = Config.SHAZAM_API_KEY
        self.api_url = 'https://shazam-api.com/api/recognize'
        self.results_url = 'https://shazam-api.com/api/results'

    def recognize_file(self, audio_file_path):
        """Распознает трек из аудио файла"""
        try:
            if not os.path.exists(audio_file_path):
                return {'success': False, 'error': 'Аудио файл не найден'}

            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            # 1. Отправляем файл на распознавание
            print(f"🔍 Отправляем запрос к Shazam API...")
            print(f"📁 Файл: {audio_file_path} ({os.path.getsize(audio_file_path)} bytes)")
            
            with open(audio_file_path, 'rb') as f:
                files = {'file': (os.path.basename(audio_file_path), f, 'audio/wav')}
                response = requests.post(self.api_url, headers=headers, files=files, timeout=60)

            print(f"📡 Статус: {response.status_code}")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text[:300]}'
                }

            data = response.json()
            
            if 'error' in data:
                return {'success': False, 'error': data['error']}

            # 2. Получаем UUID и запрашиваем результаты
            uuid = data.get('uuid')
            results_path = data.get('results')
            
            if not uuid:
                return {'success': False, 'error': 'UUID не получен от API'}

            print(f"✅ UUID: {uuid}")
            print(f"🔄 Ожидаем результаты...")

            # Запрашиваем результаты (с retry)
            results_url = f"{self.results_url}/{uuid}"
            
            for attempt in range(15):  # Максимум 30 секунд
                time.sleep(2)
                
                results_response = requests.post(results_url, headers=headers, timeout=30)
                
                if results_response.status_code != 200:
                    continue
                
                results_data = results_response.json()
                
                # Проверяем статус
                if results_data.get('status') == 'processing':
                    print(f"   Обработка... (попытка {attempt + 1})")
                    continue
                
                # Получили результаты
                return self._process_results(results_data)

            return {'success': False, 'error': 'Таймаут ожидания результатов'}

        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Таймаут запроса к Shazam API'}
        except Exception as e:
            print(f"❌ Ошибка распознавания: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _process_results(self, data):
        """Обрабатывает результаты от Shazam API"""
        try:
            results = data.get('results', [])
            
            if not results:
                return {'success': False, 'error': 'Трек не найден'}

            # Берем первый результат
            result = results[0]
            track = result.get('track', {})
            
            if not track:
                return {'success': False, 'error': 'Данные трека отсутствуют'}

            # Формируем результат
            recognition_result = {
                'success': True,
                'title': track.get('title', 'Unknown'),
                'artist': track.get('subtitle', 'Unknown'),
                'shazam_key': track.get('key', ''),
                'cover_url': '',
                'spotify_url': '',
                'apple_music_url': ''
            }

            # Извлекаем обложку
            images = track.get('images', {})
            if images:
                recognition_result['cover_url'] = images.get('coverart', '') or images.get('coverarthq', '') or images.get('background', '')

            # Извлекаем ссылки на стриминговые сервисы
            hub = track.get('hub', {})
            if hub:
                # Ищем Spotify - проверяем разные форматы
                for provider in hub.get('providers', []):
                    if provider.get('type') == 'SPOTIFY':
                        for action in provider.get('actions', []):
                            uri = action.get('uri', '')
                            # Прямая ссылка на трек
                            if uri.startswith('spotify:track:'):
                                track_id = uri.split('track:')[-1]
                                recognition_result['spotify_url'] = f'https://open.spotify.com/track/{track_id}'
                                break
                            # Search deeplink - извлекаем для поиска
                            elif 'spotify:search:' in uri:
                                # Сохраняем search query для последующего поиска
                                recognition_result['spotify_search'] = uri.replace('spotify:search:', '')
                        break

                # Ищем Apple Music
                for option in hub.get('options', []):
                    for action in option.get('actions', []):
                        uri = action.get('uri', '')
                        if 'music.apple.com' in uri:
                            recognition_result['apple_music_url'] = uri
                            break
                    if recognition_result.get('apple_music_url'):
                        break

            print(f"✅ Распознано: {recognition_result['title']} - {recognition_result['artist']}")
            if recognition_result['spotify_url']:
                print(f"🎵 Spotify: {recognition_result['spotify_url']}")
            if recognition_result['cover_url']:
                print(f"🖼️ Обложка: {recognition_result['cover_url'][:50]}...")

            return recognition_result

        except Exception as e:
            print(f"❌ Ошибка обработки результатов: {e}")
            return {'success': False, 'error': f'Ошибка обработки: {str(e)}'}
