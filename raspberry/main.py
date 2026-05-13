#!/usr/bin/env python3
"""
FlashShazam для Raspberry Pi с OLED и кнопкой
"""

import time
import os
from audio_recorder import AudioRecorder
from shazam_recognizer import ShazamRecognizer
from spotify_downloader import SpotifyDownloader
from display import Display
from button import Button
from config import Config


def main():
    print("=" * 60)
    print("🎵 FlashShazam - Raspberry Pi Edition")
    print("=" * 60)
    
    # Инициализация
    recorder = AudioRecorder(input_device_index=0)  # INMP441
    recognizer = ShazamRecognizer()
    downloader = SpotifyDownloader()
    display = Display()
    button = Button()
    
    print(f"\n✓ Длительность записи: {Config.RECORDING_DURATION} сек")
    print(f"✓ Записи: {Config.RECORDINGS_DIR}/")
    print(f"✓ Скачанные: {Config.DOWNLOADS_DIR}/")
    
    def process_track():
        """Полный цикл распознавания"""
        try:
            # 1. Запись (с возможностью отмены долгим нажатием во время записи)
            display.show_recording(Config.RECORDING_DURATION)
            print(f"\n🎤 Запись ({Config.RECORDING_DURATION} сек). Удерживай кнопку 1.5с для отмены...")

            def keep_going():
                # отмена если кнопка зажата дольше 1.5 сек
                return button.held_for() < 1.5

            audio_file = recorder.record(Config.RECORDING_DURATION, should_continue=keep_going)

            if audio_file is None:
                display.show_cancelled()
                time.sleep(1)
                display.show_ready()
                print("⏹  Запись отменена")
                return

            print(f"✓ Записано: {audio_file}")

            # 2. Распознавание
            display.show_analyzing()
            print("\n🔍 Распознавание...")
            recognition = recognizer.recognize_file(audio_file)

            if not recognition.get('success'):
                error_msg = recognition.get('error', 'Unknown error')
                display.show_error(error_msg[:60])
                print(f"❌ Не распознано: {error_msg}")
                return

            title = recognition['title']
            artist = recognition['artist']
            spotify_url = recognition.get('spotify_url', '')

            print(f"\n🎵 {title} - {artist}")

            # 3. Подтверждение: короткое нажатие = скачать, долгое = пропустить
            display.show_confirm(title, artist)
            print("Нажми коротко = скачать, удерживай = пропустить")
            action = button.wait_for_press_classified(long_threshold=1.0)

            if action == 'long':
                display.show_result(title, artist)
                print("⏭  Скачивание пропущено")
                print("\n" + "=" * 60)
                return

            # 4. Скачивание
            display.show_downloading(title)
            print("\n📥 Скачивание...")
            download = downloader.download_track(title, artist, spotify_url)

            if download.get('success'):
                size_mb = download.get('file_size', 0) / 1024 / 1024
                display.show_result(title, artist, size_mb=size_mb)
                print(f"\n✅ Готово: {download['filename']}")
            else:
                display.show_result(title, artist)
                print(f"⚠️ Не удалось скачать: {download.get('error')}")

            print("\n" + "=" * 60)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            display.show_error(str(e)[:60])
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

    # Главный цикл: первый раз показываем ready, дальше результат остаётся до нажатия
    display.show_ready()
    try:
        while True:
            print("\n" + "-" * 60)
            print("Нажмите кнопку...")
            if button.wait_for_press():
                print("\n🔘 Кнопка нажата!")
                process_track()
                
    except KeyboardInterrupt:
        print("\n\n👋 Прервано")
    finally:
        button.cleanup()
        display.clear()


if __name__ == '__main__':
    main()
