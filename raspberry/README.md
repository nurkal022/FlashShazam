# FlashShazam - Raspberry Pi Edition

Консольная версия FlashShazam для Raspberry Pi Zero 2W без веб-интерфейса.

## Возможности

- Запись аудио с микрофона
- Распознавание треков через Shazam API
- Скачивание треков через Spotify API
- Работает в консольном режиме

## Установка на Raspberry Pi Zero 2W

### 1. Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Установка зависимостей

```bash
# Python и pip
sudo apt install python3 python3-pip python3-dev -y

# Аудио библиотеки
sudo apt install portaudio19-dev libportaudio2 -y
sudo apt install ffmpeg -y

# Для работы с MP3
sudo apt install libmp3lame-dev -y
```

### 3. Установка Python пакетов

```bash
cd ~/flashSHazam/raspberry
pip3 install -r requirements.txt
```

### 4. Настройка API ключей

```bash
cp .env.example .env
nano .env
```

Заполни API ключи:
```
SHAZAM_API_KEY=твой_ключ
RAPIDAPI_KEY=твой_ключ
RAPIDAPI_HOST=spotify-downloader9.p.rapidapi.com
```

### 5. Настройка микрофона

Подключи USB микрофон и проверь:

```bash
arecord -l
```

Если нужно выбрать конкретное устройство, отредактируй `audio_recorder.py`:
```python
self.input_device_index = X  # номер устройства из arecord -l
```

## Запуск

```bash
python3 main.py
```

Или сделай скрипт исполняемым:
```bash
chmod +x main.py
./main.py
```

## Использование

1. Запусти `python3 main.py`
2. Нажми Enter для начала записи
3. Дождись распознавания и скачивания
4. Нажми 'q' для выхода

## Автозапуск при загрузке (опционально)

Создай systemd сервис:

```bash
sudo nano /etc/systemd/system/flashshazam.service
```

Добавь:
```ini
[Unit]
Description=FlashShazam Service
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/flashSHazam/raspberry
ExecStart=/usr/bin/python3 /home/pi/flashSHazam/raspberry/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Активируй:
```bash
sudo systemctl enable flashshazam
sudo systemctl start flashshazam
```

## Устранение неполадок

### Микрофон не работает
```bash
# Проверь устройства
arecord -l

# Проверь запись
arecord -d 5 test.wav
aplay test.wav
```

### Недостаточно памяти
Raspberry Pi Zero 2W имеет 512MB RAM. Если не хватает памяти:
```bash
# Увеличь swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Установи CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Проблемы с ffmpeg
```bash
# Переустанови ffmpeg
sudo apt remove ffmpeg
sudo apt install ffmpeg -y
```

## Структура файлов

```
raspberry/
├── main.py                 # Главный скрипт
├── config.py              # Конфигурация
├── audio_recorder.py      # Запись аудио
├── audio_converter.py     # Конвертация форматов
├── shazam_recognizer.py   # Распознавание Shazam
├── spotify_downloader.py  # Скачивание Spotify
├── requirements.txt       # Python зависимости
├── .env                   # API ключи (не коммитится)
└── README.md             # Эта инструкция
```

## Производительность

Raspberry Pi Zero 2W:
- CPU: Quad-core ARM Cortex-A53 @ 1GHz
- RAM: 512MB
- Запись: ~5-10 секунд
- Распознавание: ~2-5 секунд (зависит от API)
- Скачивание: ~10-30 секунд (зависит от скорости сети)

**Итого:** ~20-45 секунд на полный цикл

