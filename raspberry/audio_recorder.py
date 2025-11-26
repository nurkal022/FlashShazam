import pyaudio
import wave
import os
import struct
from datetime import datetime
from config import Config

class AudioRecorder:
    def __init__(self, input_device_index=None):
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.input_device_index = input_device_index
        
    def list_input_devices(self):
        """Список доступных входных устройств"""
        audio = pyaudio.PyAudio()
        devices = []
        
        print("\nДоступные аудио устройства:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'rate': info['defaultSampleRate']
                })
                print(f"  [{i}] {info['name']} - {info['maxInputChannels']} каналов")
        
        audio.terminate()
        return devices
    
    def find_default_input_device(self):
        """Находит устройство по умолчанию"""
        audio = pyaudio.PyAudio()
        try:
            default_device = audio.get_default_input_device_info()
            device_index = default_device['index']
            print(f"Используется устройство по умолчанию: [{device_index}] {default_device['name']}")
            return device_index
        except Exception as e:
            print(f"Ошибка получения устройства по умолчанию: {e}")
            # Пробуем найти любое устройство с входом
            for i in range(audio.get_device_count()):
                info = audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"Используется устройство: [{i}] {info['name']}")
                    return i
            return None
        finally:
            audio.terminate()
    
    def check_audio_level(self, audio_data_bytes):
        """Проверяет уровень звука в записанных данных"""
        try:
            chunk_size = len(audio_data_bytes) // 2  # 2 bytes per sample (16-bit)
            audio_data = struct.unpack(f'{chunk_size}h', audio_data_bytes)
            max_level = max(abs(sample) for sample in audio_data)
            # Максимальное значение для 16-bit: 32768
            level_percent = (max_level / 32768.0) * 100
            return level_percent
        except Exception as e:
            print(f"Ошибка проверки уровня: {e}")
            return 0.0
        
    def record(self, duration=Config.RECORDING_DURATION):
        """Записывает аудио с микрофона"""
        audio = pyaudio.PyAudio()
        
        # Определяем устройство
        device_index = self.input_device_index
        if device_index is None:
            device_index = self.find_default_input_device()
            if device_index is None:
                audio.terminate()
                raise Exception("Не найдено устройство ввода")
        
        print(f"Запись {duration} секунд с устройства [{device_index}]...")
        
        try:
            stream = audio.open(
                format=self.sample_format,
                channels=self.channels,
                rate=self.rate,
                frames_per_buffer=self.chunk,
                input=True,
                input_device_index=device_index
            )
            
            frames = []
            total_chunks = int(self.rate / self.chunk * duration)
            max_level_found = 0.0
            
            print("Начало записи...")
            
            for i in range(total_chunks):
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Проверяем уровень звука в записанных данных
                    level = self.check_audio_level(data)
                    if level > max_level_found:
                        max_level_found = level
                    
                    # Показываем прогресс каждые 3 секунды
                    if i % (int(self.rate / self.chunk * 3)) == 0:
                        elapsed = i * self.chunk / self.rate
                        print(f"  Запись... {elapsed:.1f}с (текущий уровень: {level:.1f}%, макс: {max_level_found:.1f}%)")
                except Exception as e:
                    print(f"Ошибка чтения данных: {e}")
                    break
            
            print(f"\nМаксимальный уровень звука за запись: {max_level_found:.1f}%")
            
            if max_level_found < 0.1:
                print("⚠️  ВНИМАНИЕ: Очень низкий уровень звука!")
                print("   Возможные причины:")
                print("   - Микрофон не подключен или выключен")
                print("   - Нет прав доступа к микрофону (macOS: Системные настройки -> Безопасность)")
                print("   - Уровень громкости слишком низкий")
                print("   - Неправильное устройство выбрано")
            elif max_level_found < 1.0:
                print("⚠️  Низкий уровень звука - может быть недостаточно для распознавания")
            
            stream.stop_stream()
            stream.close()
            
            # Проверяем что записали данные
            total_bytes = sum(len(f) for f in frames)
            if total_bytes == 0:
                raise Exception("Запись пустая - проверьте микрофон и уровень звука")
            
            print(f"Записано {total_bytes} байт данных")
            
        except Exception as e:
            audio.terminate()
            raise Exception(f"Ошибка записи: {e}")
        
        # Сохраняем файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(Config.RECORDINGS_DIR, f"recording_{timestamp}.wav")
        
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.sample_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print(f"Запись сохранена: {filename}")
            return filename
        except Exception as e:
            audio.terminate()
            raise Exception(f"Ошибка сохранения файла: {e}")
        finally:
            audio.terminate()

