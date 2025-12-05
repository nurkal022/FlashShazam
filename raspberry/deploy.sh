#!/bin/bash
#
# FlashShazam Raspberry Pi Deployment Script
#

set -e

echo "=========================================="
echo "🎵 FlashShazam - Raspberry Pi Installer"
echo "=========================================="

# Обновление системы
echo ""
echo "[1/6] Обновление системы..."
sudo apt-get update
sudo apt-get upgrade -y

# Установка системных зависимостей
echo ""
echo "[2/6] Установка системных зависимостей..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    libffi-dev \
    libssl-dev

# Создание виртуального окружения
echo ""
echo "[3/6] Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo ""
echo "[4/6] Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
echo ""
echo "[5/6] Настройка конфигурации..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Shazam API (shazam-api.com)
SHAZAM_API_KEY=your_shazam_api_key_here

# Apify для скачивания
APIFY_TOKEN=your_apify_token_here

# Spotify Web API
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
EOF
    echo "✓ .env создан (заполните своими ключами!)"
fi

# Создание директорий
echo ""
echo "[6/6] Создание директорий..."
mkdir -p recordings downloads

echo ""
echo "=========================================="
echo "✅ Установка завершена!"
echo "=========================================="
echo ""
echo "Запуск:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
