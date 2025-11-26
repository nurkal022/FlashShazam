# Настройка для Raspberry Pi 🍓

## Установка зависимостей

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка системных зависимостей
sudo apt install -y python3-pip python3-venv portaudio19-dev python3-pyaudio ffmpeg

# Установка ALSA утилит (для работы с микрофоном)
sudo apt install -y alsa-utils
```

## Настройка микрофона

### 1. Проверка подключенных устройств:
```bash
arecord -l
```

Вы увидите список устройств, например:
```
card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

### 2. Настройка уровня громкости:
```bash
alsamixer
```
- Выберите нужное устройство (F6)
- Настройте уровень записи (стрелки вверх/вниз)
- Нажмите `Esc` для выхода

### 3. Тестовая запись:
```bash
# Запись 5 секунд
arecord -d 5 -f cd test.wav

# Воспроизведение
aplay test.wav
```

### 4. Тест через Python:
```bash
python test_microphone.py
```

## Настройка I2S микрофона (INMP441)

Если используете I2S микрофон INMP441:

### 1. Включите I2S в config:
```bash
sudo raspi-config
# Interface Options -> I2S -> Enable
```

### 2. Добавьте в `/boot/config.txt`:
```
dtoverlay=i2s-mmap
```

### 3. Перезагрузите:
```bash
sudo reboot
```

### 4. Проверьте устройство:
```bash
arecord -l
# Должно появиться устройство типа "bcm2835-i2s"
```

## Запуск приложения

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск сервера
python app.py
```

Сервер будет доступен по адресу: `http://raspberry-pi-ip:5001`

## Автозапуск при загрузке

Создайте systemd сервис:

```bash
sudo nano /etc/systemd/system/flashshazam.service
```

Содержимое:
```ini
[Unit]
Description=FlashShazam Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/flashSHazam
Environment="PATH=/home/pi/flashSHazam/venv/bin"
ExecStart=/home/pi/flashSHazam/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl enable flashshazam.service
sudo systemctl start flashshazam.service
```

## Проверка статуса:
```bash
sudo systemctl status flashshazam.service
```

## Устранение проблем

### Микрофон не определяется:
1. Проверьте подключение: `arecord -l`
2. Проверьте права: `groups` (должна быть группа `audio`)
3. Добавьте пользователя в группу: `sudo usermod -a -G audio $USER`

### Пустые записи:
1. Проверьте уровень звука: `alsamixer`
2. Увеличьте уровень записи
3. Запустите тест: `python test_microphone.py`

### Ошибки распознавания:
1. Убедитесь что музыка играет достаточно громко
2. Проверьте качество записи: `aplay recordings/recording_*.wav`
3. Увеличьте длительность записи в `config.py`

