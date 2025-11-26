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
        
        # Используем указанное устройство или по умолчанию
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
        
        result = recognizer.recognize_sync(audio_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download', methods=['POST'])
def download_track():
    """Скачивает трек по названию и артисту"""
    try:
        track_name = request.json.get('track_name')
        artist_name = request.json.get('artist_name')
        
        if not track_name or not artist_name:
            return jsonify({
                'success': False,
                'error': 'Не указаны название трека или артист'
            }), 400
        
        result = downloader.download_track(track_name, artist_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process', methods=['POST'])
def process_full():
    """Полный цикл: запись -> распознавание -> скачивание"""
    try:
        # Поддерживаем два режима:
        # 1. Запись с сервера (Raspberry Pi) - через параметр duration
        # 2. Загрузка файла от браузера - через multipart/form-data
        
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
            print(f"Конвертация {filepath} в WAV...")
            audio_file_path = convert_to_wav(filepath)
        else:
            # Режим записи с сервера (Raspberry Pi)
            duration = request.json.get('duration', Config.RECORDING_DURATION) if request.is_json else Config.RECORDING_DURATION
            device_index = request.json.get('device_index', None) if request.is_json else None
            
            if device_index is not None:
                recorder.input_device_index = device_index
            
            audio_file_path = recorder.record(duration)
        
        # 2. Распознавание
        print(f"Распознавание трека из файла: {audio_file_path}")
        recognition = recognizer.recognize_sync(audio_file_path)
        
        if not recognition.get('success'):
            return jsonify({
                'success': False,
                'error': 'Не удалось распознать трек',
                'recognition': recognition
            })
        
        print(f"Распознан трек: {recognition['title']} - {recognition['artist']}")
        
        # 3. Скачивание
        print("Начало скачивания трека...")
        download_result = downloader.download_track(
            recognition['title'],
            recognition['artist']
        )
        
        print(f"Результат скачивания: success={download_result.get('success')}, error={download_result.get('error')}")
        
        response_data = {
            'success': True,
            'recognition': recognition,
            'download': download_result
        }
        
        # Добавляем URL для проигрывания если файл скачан
        if download_result.get('success') and download_result.get('filename'):
            response_data['audioUrl'] = f'/api/downloads/{download_result["filename"]}'
        
        return jsonify(response_data)
    except Exception as e:
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
        print(f"Обработка последнего файла: {last_file}")
        
        # Если это webm, конвертируем в wav
        if last_file.lower().endswith('.webm'):
            print(f"Конвертация {last_file} в WAV...")
            audio_file_path = convert_to_wav(last_file)
        else:
            audio_file_path = last_file
            
        # 2. Распознавание
        print(f"Распознавание трека из файла: {audio_file_path}")
        recognition = recognizer.recognize_sync(audio_file_path)
        
        if not recognition.get('success'):
            return jsonify({
                'success': False,
                'error': 'Не удалось распознать трек',
                'recognition': recognition
            })
        
        print(f"Распознан трек: {recognition['title']} - {recognition['artist']}")
        
        # 3. Скачивание
        print("Начало скачивания трека...")
        download_result = downloader.download_track(
            recognition['title'],
            recognition['artist']
        )
        
        print(f"Результат скачивания: success={download_result.get('success')}, error={download_result.get('error')}")
        
        response_data = {
            'success': True,
            'recognition': recognition,
            'download': download_result
        }
        
        # Добавляем URL для проигрывания если файл скачан
        if download_result.get('success') and download_result.get('filename'):
            response_data['audioUrl'] = f'/api/downloads/{download_result["filename"]}'
        
        return jsonify(response_data)
            
    except Exception as e:
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
        return send_file(filepath)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

