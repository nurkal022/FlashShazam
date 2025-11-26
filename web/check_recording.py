#!/usr/bin/env python3
"""
Проверка записанного файла на наличие звука
"""

import wave
import struct
import sys
import os

def analyze_wav(filename):
    """Анализирует WAV файл на наличие звука"""
    if not os.path.exists(filename):
        print(f"❌ Файл не найден: {filename}")
        return
    
    try:
        wf = wave.open(filename, 'rb')
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        duration = n_frames / framerate
        
        print(f"\n📊 Анализ файла: {filename}")
        print(f"   Каналы: {channels}")
        print(f"   Частота дискретизации: {framerate} Hz")
        print(f"   Размер сэмпла: {sample_width} байт")
        print(f"   Количество фреймов: {n_frames}")
        print(f"   Длительность: {duration:.2f} секунд")
        
        # Читаем все данные
        frames = wf.readframes(n_frames)
        wf.close()
        
        if len(frames) == 0:
            print("\n❌ Файл пустой!")
            return
        
        # Анализируем уровень звука
        if sample_width == 2:  # 16-bit
            samples = struct.unpack(f'{len(frames)//2}h', frames)
        elif sample_width == 1:  # 8-bit
            samples = struct.unpack(f'{len(frames)}B', frames)
            samples = [s - 128 for s in samples]  # Convert to signed
        else:
            print(f"❌ Неподдерживаемый размер сэмпла: {sample_width}")
            return
        
        # Находим максимальный уровень
        max_amplitude = max(abs(s) for s in samples)
        min_amplitude = min(abs(s) for s in samples)
        avg_amplitude = sum(abs(s) for s in samples) / len(samples)
        
        # Для 16-bit максимальное значение 32768
        max_possible = 32768 if sample_width == 2 else 128
        max_percent = (max_amplitude / max_possible) * 100
        avg_percent = (avg_amplitude / max_possible) * 100
        
        print(f"\n🔊 Уровни звука:")
        print(f"   Максимальная амплитуда: {max_amplitude} ({max_percent:.2f}%)")
        print(f"   Средняя амплитуда: {avg_amplitude:.1f} ({avg_percent:.2f}%)")
        print(f"   Минимальная амплитуда: {min_amplitude}")
        
        # Проверяем на тишину
        if max_percent < 0.1:
            print("\n⚠️  ФАЙЛ СОДЕРЖИТ ТОЛЬКО ТИШИНУ!")
            print("   Микрофон не записал звук.")
            print("\n   Решения для macOS:")
            print("   1. Системные настройки -> Безопасность и конфиденциальность -> Микрофон")
            print("   2. Разрешите доступ для Terminal или Python")
            print("   3. Перезапустите терминал")
            print("   4. Проверьте уровень громкости: Системные настройки -> Звук")
        elif max_percent < 1.0:
            print("\n⚠️  Очень низкий уровень звука")
            print("   Может быть недостаточно для распознавания")
        else:
            print("\n✅ Звук обнаружен!")
            print(f"   Уровень достаточен для распознавания")
        
        # Проверяем на монотонность (все одинаковые значения = тишина)
        unique_values = len(set(samples[:1000]))  # Проверяем первые 1000 сэмплов
        if unique_values < 10:
            print("\n⚠️  Подозрение на тишину: очень мало уникальных значений")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Ищем последний записанный файл
        import glob
        files = glob.glob('recordings/recording_*.wav')
        if files:
            filename = max(files, key=os.path.getctime)
            print(f"Используется последний файл: {filename}")
        else:
            print("❌ Не найдено записанных файлов")
            print("Использование: python check_recording.py <путь_к_файлу.wav>")
            sys.exit(1)
    
    analyze_wav(filename)

