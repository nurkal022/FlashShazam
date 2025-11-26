#!/bin/bash
# Скрипт деплоя на Raspberry Pi Zero 2W

echo "=================================="
echo "FlashShazam - Деплой на Raspberry Pi"
echo "=================================="

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция проверки команды
check_command() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

# 1. Проверка системы
echo -e "\n[1/7] Проверка системы..."
uname -a
check_command "Система проверена"

# 2. Обновление системы
echo -e "\n[2/7] Обновление системы (может занять время)..."
sudo apt update
check_command "apt update"

# 3. Установка системных зависимостей
echo -e "\n[3/7] Установка системных зависимостей..."
sudo apt install -y python3 python3-pip python3-dev portaudio19-dev libportaudio2 ffmpeg libmp3lame-dev
check_command "Системные зависимости установлены"

# 4. Установка Python пакетов
echo -e "\n[4/7] Установка Python пакетов..."
pip3 install --upgrade pip
pip3 install -r requirements.txt
check_command "Python пакеты установлены"

# 5. Проверка .env файла
echo -e "\n[5/7] Проверка .env файла..."
if [ ! -f .env ]; then
    echo -e "${RED}✗${NC} Файл .env не найден!"
    echo "Создай .env файл с API ключами:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
else
    echo -e "${GREEN}✓${NC} Файл .env найден"
fi

# 6. Проверка микрофона
echo -e "\n[6/7] Проверка аудио устройств..."
arecord -l
check_command "Аудио устройства проверены"

# 7. Создание директорий
echo -e "\n[7/7] Создание директорий..."
mkdir -p recordings downloads
check_command "Директории созданы"

# Готово
echo -e "\n=================================="
echo -e "${GREEN}Установка завершена!${NC}"
echo "=================================="
echo ""
echo "Запуск:"
echo "  python3 main.py"
echo ""
echo "Или:"
echo "  chmod +x main.py"
echo "  ./main.py"
echo ""

