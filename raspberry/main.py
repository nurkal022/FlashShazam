#!/usr/bin/env python3
"""
FlashShazam для Raspberry Pi
Консольная версия: распознавание + скачивание
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
    print("🎵 FlashShazam - Raspberry Pi Edition")
    print("=" * 60)
    
    # Инициализация
    # INMP441 обычно card 1, device 0 → index 1
    recorder = AudioRecorder(input_device_index=1)
    recognizer = ShazamRecognizer()
    downloader = SpotifyDownloader()
    
    print(f"\n✓ Длительность записи: {Config.RECORDING_DURATION} сек")
    print(f"✓ Записи: {Config.RECORDINGS_DIR}/")
    print(f"✓ Скачанные: {Config.DOWNLOADS_DIR}/")
    
    while True:
        print("\n" + "-" * 60)
        print("Нажмите Enter для записи | 'l' - последний файл | 'q' - выход")
        user_input = input().strip().lower()
        
        if user_input == 'q':
            print("👋 Выход...")
            break
        
        try:
            # Определяем источник аудио
            if user_input == 'l':
                # Используем последний записанный файл
                import glob
                files = glob.glob(os.path.join(Config.RECORDINGS_DIR, "*.wav"))
                if not files:
                    print("❌ Нет записанных файлов")
                    continue
                audio_file = max(files, key=os.path.getctime)
                print(f"📁 Используем: {os.path.basename(audio_file)}")
            else:
                # Записываем новое аудио
                print(f"\n🎤 Запись ({Config.RECORDING_DURATION} сек)...")
                audio_file = recorder.record(Config.RECORDING_DURATION)
                print(f"✓ Записано: {audio_file}")
            
            # Распознавание
            print("\n🔍 Распознавание...")
            recognition = recognizer.recognize_file(audio_file)
            
            if not recognition.get('success'):
                print(f"❌ Не распознано: {recognition.get('error')}")
                continue
            
            title = recognition['title']
            artist = recognition['artist']
            spotify_url = recognition.get('spotify_url', '')
            
            print(f"\n🎵 {title} - {artist}")
            
            if recognition.get('apple_music_url'):
                print(f"🍎 Apple Music: {recognition['apple_music_url']}")
            
            # Скачивание
            print("\n📥 Скачивание...")
            download = downloader.download_track(title, artist, spotify_url)
            
            if download.get('success'):
                print(f"\n✅ Готово: {download['filename']}")
                print(f"📁 Путь: {download['file_path']}")
            else:
                print(f"⚠️ Не удалось скачать: {download.get('error')}")
                print("   Трек распознан, но скачивание недоступно")
            
            print("\n" + "=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Прервано")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
