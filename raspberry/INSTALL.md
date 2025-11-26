# Установка на Raspberry Pi Zero 2W

## Быстрая установка

### Метод 1: Автоматический (рекомендуется)

```bash
# На Raspberry Pi
git clone <repo-url> flashSHazam
cd flashSHazam/raspberry

# Отредактируй .env файл с твоими API ключами
nano .env

# Запусти скрипт установки
./deploy.sh

# Готово! Запусти
python3 main.py
```

### Метод 2: Ручная установка

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y

# 2. Установка системных зависимостей
sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    libportaudio2 \
    ffmpeg \
    libmp3lame-dev

# 3. Установка Python пакетов
cd flashSHazam/raspberry
pip3 install -r requirements.txt

# 4. Настройка .env
cp .env.example .env
nano .env
# Добавь свои API ключи

# 5. Создание директорий
mkdir -p recordings downloads

# 6. Запуск
python3 main.py
```

## Настройка микрофона

### Проверка устройств

```bash
# Список всех аудио устройств
arecord -l

# Пример вывода:
# card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
```

### Выбор устройства

Если микрофон не находится автоматически, отредактируй `audio_recorder.py`:

```python
class AudioRecorder:
    def __init__(self):
        # Укажи номер устройства из arecord -l
        self.input_device_index = 1  # Например, card 1
```

### Тест микрофона

```bash
# Запись 5 секунд
arecord -d 5 -f cd test.wav

# Проигрывание
aplay test.wav
```

## Настройка автозапуска

### Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/flashshazam.service
```

Содержимое:
```ini
[Unit]
Description=FlashShazam Service
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/flashSHazam/raspberry
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/pi/flashSHazam/raspberry/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl daemon-reload
sudo systemctl enable flashshazam
sudo systemctl start flashshazam

# Проверка статуса
sudo systemctl status flashshazam

# Логи
sudo journalctl -u flashshazam -f
```

## Оптимизация для Pi Zero 2W

### Увеличение swap (если мало памяти)

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Измени: CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Отключение ненужных сервисов

```bash
# Bluetooth (если не используется)
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# GUI (если запущена)
sudo systemctl set-default multi-user.target
```

### Overclock (опционально, осторожно!)

```bash
sudo nano /boot/config.txt
```

Добавь:
```ini
# Overclock Pi Zero 2W
over_voltage=2
arm_freq=1200
```

Перезагрузка:
```bash
sudo reboot
```

## Удаленный доступ

### SSH

```bash
# Включить SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Подключение с другого компьютера
ssh pi@raspberrypi.local
```

### Копирование файлов

```bash
# С компьютера на Pi
scp file.mp3 pi@raspberrypi.local:~/flashSHazam/raspberry/downloads/

# С Pi на компьютер
scp pi@raspberrypi.local:~/flashSHazam/raspberry/downloads/song.mp3 ./
```

## Мониторинг

### Температура

```bash
vcgencmd measure_temp
```

### Использование памяти

```bash
free -h
```

### Использование CPU

```bash
top
# или
htop  # (нужна установка: sudo apt install htop)
```

### Дисковое пространство

```bash
df -h
```

## Устранение проблем

### Ошибка: "No module named 'pyaudio'"

```bash
sudo apt install portaudio19-dev libportaudio2
pip3 install --upgrade pyaudio
```

### Ошибка: "ffmpeg not found"

```bash
sudo apt install ffmpeg
ffmpeg -version
```

### Ошибка: "Permission denied" для микрофона

```bash
# Добавь пользователя в группу audio
sudo usermod -a -G audio $USER

# Перезайди или перезагрузи
sudo reboot
```

### Ошибка: "API key invalid"

Проверь .env файл:
```bash
cat .env
```

Убедись что ключи правильные и без пробелов.

### Медленная работа

1. Проверь температуру: `vcgencmd measure_temp`
2. Увеличь swap (см. выше)
3. Отключи ненужные сервисы
4. Используй более быструю SD карту (Class 10 или UHS)

## Обновление

```bash
cd ~/flashSHazam
git pull
cd raspberry
pip3 install -r requirements.txt --upgrade
```

## Бэкап

```bash
# Сохранить скачанные треки
tar -czf backup_$(date +%Y%m%d).tar.gz downloads/

# Копировать на другой компьютер
scp backup_*.tar.gz user@computer:~/
```

## Дополнительно

### Подключение кнопки для запуска

Можно подключить физическую кнопку к GPIO для запуска записи.

Пример (требует доработки `main.py`):
```python
import RPi.GPIO as GPIO

BUTTON_PIN = 17  # GPIO 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button_callback(channel):
    # Запуск записи
    pass

GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, 
                     callback=button_callback, bouncetime=300)
```

### LED индикатор

Подключи LED к GPIO для индикации статуса:
- Мигает = запись
- Горит = обработка
- Выключен = готов

