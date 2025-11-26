# FlashShazam

Распознавание и скачивание музыки через Shazam и Spotify API.

## Версии

Проект имеет две версии:

### 🌐 Web версия (`/web`)
- Flask веб-сервер
- Веб-интерфейс для записи через браузер
- API endpoints
- Запись с микрофона через браузер

**Использование:**
```bash
cd web
pip install -r requirements.txt
python app.py
# Открой http://localhost:5001
```

### 🍓 Raspberry Pi версия (`/raspberry`)
- Консольная версия без веб-интерфейса
- Оптимизирована для Raspberry Pi Zero 2W
- Запись с USB микрофона
- Простой CLI интерфейс

**Использование:**
```bash
cd raspberry
# Следуй инструкциям в raspberry/README.md
./deploy.sh  # На Raspberry Pi
python3 main.py
```

## Возможности

- 🎵 Распознавание треков через Shazam API
- 📥 Скачивание через Spotify API (spotify-downloader9.p.rapidapi.com)
- 🎤 Запись с микрофона
- 🎨 Добавление метаданных и обложек в MP3
- 🔄 Автоматическая конвертация форматов

## Требования

### Общие
- Python 3.8+
- API ключи:
  - Shazam RapidAPI key
  - Spotify downloader RapidAPI key

### Web версия
- Flask
- Современный браузер с поддержкой MediaRecorder API

### Raspberry Pi версия
- Raspberry Pi Zero 2W (или старше)
- USB микрофон
- Debian/Raspbian OS

## Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone <repo-url>
cd flashSHazam
```

### 2. Создать .env файл
```bash
# Для web версии
cd web
cp .env.example .env
nano .env

# Для Raspberry Pi версии
cd raspberry
cp .env.example .env
nano .env
```

### 3. Запустить нужную версию

**Web:**
```bash
cd web
pip install -r requirements.txt
python app.py
```

**Raspberry Pi:**
```bash
cd raspberry
./deploy.sh  # Установка всех зависимостей
python3 main.py
```

## API Ключи

Получи API ключи на [RapidAPI](https://rapidapi.com):

1. [Shazam API](https://rapidapi.com/apidojo/api/shazam)
2. [Spotify Downloader API](https://rapidapi.com/spotify-downloader9.p.rapidapi.com)

## Документация

- [Web версия](web/README.md)
- [Raspberry Pi версия](raspberry/README.md)
- [Настройка macOS](MACOS_MICROPHONE_FIX.md)
- [Настройка Raspberry Pi](RASPBERRY_PI_SETUP.md)

## Структура проекта

```
flashSHazam/
├── web/                    # Web версия с Flask
│   ├── app.py             # Flask сервер
│   ├── templates/         # HTML шаблоны
│   ├── audio_recorder.py
│   ├── shazam_recognizer.py
│   ├── spotify_downloader.py
│   └── requirements.txt
│
├── raspberry/             # Raspberry Pi версия
│   ├── main.py           # Консольный скрипт
│   ├── deploy.sh         # Скрипт установки
│   ├── audio_recorder.py
│   ├── shazam_recognizer.py
│   ├── spotify_downloader.py
│   └── requirements.txt
│
├── recordings/           # Записи (создается автоматически)
├── downloads/            # Скачанные треки
└── README.md            # Этот файл
```

## Лицензия

MIT
