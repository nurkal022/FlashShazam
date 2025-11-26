#!/usr/bin/env python3
"""
Утилита для тестирования микрофона на Raspberry Pi
"""

from audio_recorder import AudioRecorder
import sys

def main():
    recorder = AudioRecorder()
    
    print("=" * 60)
    print("Тестирование микрофона")
    print("=" * 60)
    
    # Показываем доступные устройства
    devices = recorder.list_input_devices()
    
    if not devices:
        print("\n❌ Не найдено устройств ввода!")
        print("\nПроверьте:")
        print("  1. Подключен ли микрофон")
        print("  2. Правильно ли настроен ALSA/PulseAudio")
        print("  3. Запустите: arecord -l  для проверки")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Тестовая запись (5 секунд)...")
    print("Воспроизведите звук или говорите в микрофон")
    print("=" * 60)
    print("\n⚠️  ВАЖНО для macOS:")
    print("   Если уровень звука 0% - проверьте права доступа:")
    print("   Системные настройки -> Безопасность -> Микрофон -> Terminal/Python")
    print("=" * 60)
    
    try:
        # Записываем 5 секунд
        filename = recorder.record(duration=5)
        print(f"\n✅ Запись успешна: {filename}")
        print(f"\nПроверьте файл: {filename}")
        print(f"Для прослушивания: aplay {filename}")
        
    except Exception as e:
        print(f"\n❌ Ошибка записи: {e}")
        print("\nВозможные решения:")
        if sys.platform == 'darwin':  # macOS
            print("  macOS:")
            print("  1. Системные настройки -> Безопасность -> Микрофон")
            print("  2. Разрешите доступ для Terminal/Python")
            print("  3. Перезапустите терминал")
            print("  4. Проверьте уровень громкости в Системных настройках -> Звук")
        else:  # Linux/Raspberry Pi
            print("  Linux/Raspberry Pi:")
            print("  1. Проверьте уровень громкости: alsamixer")
            print("  2. Проверьте устройство: arecord -l")
            print("  3. Убедитесь что микрофон не занят другим процессом")
            print("  4. Проверьте права: groups (должна быть группа 'audio')")
        sys.exit(1)

if __name__ == '__main__':
    main()

