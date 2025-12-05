from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
from audio_recorder import AudioRecorder
from audio_converter import convert_to_wav
from shazam_recognizer import ShazamRecognizer
from spotify_downloader import SpotifyDownloader
from config import Config

app = Flask(__name__)
CORS(app)

recorder = AudioRecorder()
recognizer = ShazamRecognizer()
downloader = SpotifyDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices', methods=['GET'])
def list_devices():
    """Возвращает список доступных аудио устройств"""
    try:
        devices = recorder.list_input_devices()
        return jsonify({
            'success': True,
            'devices': devices
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/record', methods=['POST'])
def record_audio():
    """Записывает аудио с микрофона (для Raspberry Pi)"""
    try:
        duration = request.json.get('duration', Config.RECORDING_DURATION)
        device_index = request.json.get('device_index', None)
        
        if device_index is not None:
            recorder.input_device_index = device_index
        
        audio_file = recorder.record(duration)
        return jsonify({
            'success': True,
            'audio_file': audio_file
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recognize', methods=['POST'])
def recognize_track():
    """Распознает трек из аудио файла"""
    try:
        audio_file = request.json.get('audio_file')
        if not audio_file or not os.path.exists(audio_file):
            return jsonify({
                'success': False,
                'error': 'Аудио файл не найден'
            }), 400

        result = recognizer.recognize_file(audio_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def download_track_from_recognition(recognition):
    """Скачивает трек на основе результатов распознавания"""
    download_result = None
    spotify_url = recognition.get('spotify_url')

    if spotify_url:
        print(f"🎵 Найден Spotify URL: {spotify_url}")
        print("📥 Начинаем скачивание...")
        download_result = downloader.download_by_spotify_url(spotify_url)
    else:
        # Если нет прямого URL, ищем по названию
        print("🔍 Spotify URL не найден, ищем по названию...")
        download_result = downloader.download_track(
            recognition['title'],
            recognition['artist']
        )

    if download_result and download_result.get('success'):
        print(f"✅ Скачано: {download_result.get('filename')}")
    elif download_result:
        print(f"⚠️ Ошибка скачивания: {download_result.get('error')}")
    
    return download_result


@app.route('/api/process', methods=['POST'])
def process_full():
    """Полный цикл: запись -> распознавание -> скачивание"""
    try:
        # Поддерживаем два режима:
        # 1. Загрузка файла от браузера - через multipart/form-data
        # 2. Запись с сервера (Raspberry Pi) - через параметр duration

        if 'audio' in request.files:
            # Режим загрузки от браузера
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Файл не выбран'
                }), 400

            # Сохраняем файл
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.webm"
            filepath = os.path.join(Config.RECORDINGS_DIR, filename)
            audio_file.save(filepath)

            # Конвертируем webm в wav для распознавания
            print(f"📁 Конвертация {filepath} в WAV...")
            audio_file_path = convert_to_wav(filepath)
        else:
            # Режим записи с сервера (Raspberry Pi)
            duration = request.json.get('duration', Config.RECORDING_DURATION) if request.is_json else Config.RECORDING_DURATION
            device_index = request.json.get('device_index', None) if request.is_json else None

            if device_index is not None:
                recorder.input_device_index = device_index

            audio_file_path = recorder.record(duration)

        # 2. Распознавание через Shazam
        print(f"🔍 Распознавание трека из файла: {audio_file_path}")
        recognition = recognizer.recognize_file(audio_file_path)

        if not recognition.get('success'):
            return jsonify({
                'success': False,
                'error': 'Не удалось распознать трек',
                'recognition': recognition
            })

        print(f"✅ Распознан трек: {recognition['title']} - {recognition['artist']}")

        # 3. Скачивание через Spotify
        download_result = download_track_from_recognition(recognition)

        response_data = {
            'success': True,
            'recognition': recognition,
            'download': download_result
        }

        # Добавляем URL для воспроизведения если файл скачан
        if download_result and download_result.get('success') and download_result.get('filename'):
            response_data['audioUrl'] = f'/api/downloads/{download_result["filename"]}'

        return jsonify(response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process_last', methods=['POST'])
def process_last():
    """Обрабатывает последний записанный файл"""
    try:
        import glob

        # Ищем файлы в директории записей
        files = glob.glob(os.path.join(Config.RECORDINGS_DIR, "*"))
        if not files:
            return jsonify({
                'success': False,
                'error': 'Нет записанных файлов'
            }), 404

        # Берем самый новый файл
        last_file = max(files, key=os.path.getctime)
        print(f"📁 Обработка последнего файла: {last_file}")

        # Если это webm, конвертируем в wav
        if last_file.lower().endswith('.webm'):
            print(f"📁 Конвертация {last_file} в WAV...")
            audio_file_path = convert_to_wav(last_file)
        else:
            audio_file_path = last_file

        # 2. Распознавание через Shazam
        print(f"🔍 Распознавание трека из файла: {audio_file_path}")
        recognition = recognizer.recognize_file(audio_file_path)

        if not recognition.get('success'):
            return jsonify({
                'success': False,
                'error': 'Не удалось распознать трек',
                'recognition': recognition
            })

        print(f"✅ Распознан трек: {recognition['title']} - {recognition['artist']}")

        # 3. Скачивание через Spotify
        download_result = download_track_from_recognition(recognition)

        response_data = {
            'success': True,
            'recognition': recognition,
            'download': download_result
        }

        # Добавляем URL для воспроизведения если файл скачан
        if download_result and download_result.get('success') and download_result.get('filename'):
            response_data['audioUrl'] = f'/api/downloads/{download_result["filename"]}'

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    """Отдает аудио файлы"""
    filepath = os.path.join(Config.RECORDINGS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/downloads/<path:filename>')
def serve_download(filename):
    """Отдает скачанные MP3 файлы"""
    filepath = os.path.join(Config.DOWNLOADS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg')
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
