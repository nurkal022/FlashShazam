#!/usr/bin/env python3
"""
FlashShazam для Raspberry Pi Zero 2W
Консольная версия без веб-интерфейса
"""

import time
import os
from audio_recorder import AudioRecorder
from audio_converter import convert_to_wav
from shazam_recognizer import ShazamRecognizer
from spotify_downloader import SpotifyDownloader
from config import Config

def main():
    print("=" * 60)
    print("FlashShazam - Raspberry Pi Edition")
    print("=" * 60)
    
    # Инициализация компонентов
    recorder = AudioRecorder()
    recognizer = ShazamRecognizer()
    downloader = SpotifyDownloader()
    
    print("\nКомпоненты инициализированы")
    print(f"Длительность записи: {Config.RECORDING_DURATION} секунд")
    print(f"Директория записей: {Config.RECORDINGS_DIR}")
    print(f"Директория загрузок: {Config.DOWNLOADS_DIR}")
    
    while True:
        print("\n" + "-" * 60)
        print("Нажмите Enter для начала записи или 'q' для выхода...")
        user_input = input().strip().lower()
        
        if user_input == 'q':
            print("Выход...")
            break
        
        try:
            # 1. Запись аудио
            print(f"\n[1/3] Запись аудио ({Config.RECORDING_DURATION} сек)...")
            audio_file = recorder.record(Config.RECORDING_DURATION)
            print(f"✓ Записано: {audio_file}")
            
            # 2. Распознавание
            print("\n[2/3] Распознавание трека...")
            recognition = recognizer.recognize_sync(audio_file)
            
            if not recognition.get('success'):
                print(f"✗ Не удалось распознать: {recognition.get('error', 'Неизвестная ошибка')}")
                continue
            
            title = recognition['title']
            artist = recognition['artist']
            print(f"✓ Распознано: {title} - {artist}")
            
            if recognition.get('cover_url'):
                print(f"  Обложка: {recognition['cover_url']}")
            
            # 3. Скачивание
            print("\n[3/3] Скачивание трека...")
            download_result = downloader.download_track(title, artist)
            
            if download_result.get('success') and download_result.get('file_path'):
                print(f"✓ Скачано: {download_result['filename']}")
                print(f"  Путь: {download_result['file_path']}")
            elif download_result.get('success'):
                print(f"✓ Метаданные получены, но файл не скачан")
                print(f"  {download_result.get('error', '')}")
            else:
                print(f"✗ Ошибка скачивания: {download_result.get('error', 'Неизвестная ошибка')}")
            
            print("\n" + "=" * 60)
            print("Готово!")
            
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем")
            break
        except Exception as e:
            print(f"\n✗ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()

