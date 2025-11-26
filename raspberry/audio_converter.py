"""
Конвертация аудио файлов для распознавания
"""

import os
from pydub import AudioSegment
from config import Config

def convert_to_wav(input_file, output_file=None):
    """
    Конвертирует аудио файл в WAV формат для распознавания
    
    Поддерживаемые форматы: webm, mp3, m4a, ogg, flac
    """
    try:
        # Определяем формат по расширению
        ext = os.path.splitext(input_file)[1].lower().lstrip('.')
        
        if ext == 'wav':
            # Уже WAV, возвращаем как есть
            return input_file
        
        # Если выходной файл не указан, создаем рядом
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.wav'
        
        print(f"Конвертация {ext} -> wav: {input_file}")
        
        # Загружаем аудио
        if ext == 'webm':
            audio = AudioSegment.from_file(input_file, format="webm")
        elif ext == 'mp3':
            audio = AudioSegment.from_mp3(input_file)
        elif ext == 'm4a':
            audio = AudioSegment.from_file(input_file, format="m4a")
        elif ext == 'ogg':
            audio = AudioSegment.from_ogg(input_file)
        elif ext == 'flac':
            audio = AudioSegment.from_file(input_file, format="flac")
        else:
            # Пробуем автоматически определить
            audio = AudioSegment.from_file(input_file)
        
        # Конвертируем в моно, 44.1kHz для лучшей совместимости с Shazam
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(44100)
        
        # Экспортируем в WAV
        audio.export(output_file, format="wav")
        
        print(f"Конвертация завершена: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Ошибка конвертации: {e}")
        raise Exception(f"Не удалось конвертировать файл: {e}")

