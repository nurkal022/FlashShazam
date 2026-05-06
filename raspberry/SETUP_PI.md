# FlashShazam - Raspberry Pi Zero 2W Setup

Автономное устройство: нажал кнопку → записал 15 сек → Shazam распознал → Apify скачал MP3.
Результат остаётся на OLED-экране до следующего нажатия.

## Оборудование

- Raspberry Pi Zero 2W
- Микрофон **INMP441** (I2S)
- Дисплей **OLED SH1106** 128×64 (I2C)
- Кнопка тактовая (один контакт)

### Распиновка

| Компонент | Сигнал | GPIO | Физический пин |
|---|---|---|---|
| **INMP441 mic** | VCC | 3.3V | 1 |
| | GND | GND | 6 |
| | SCK / BCLK | GPIO18 | 12 |
| | WS / LRC | GPIO19 | 35 |
| | SD / DOUT | GPIO20 | 38 |
| | L/R | → GND | 6 |
| **OLED SH1106** | VCC | 3.3V | 1 (общий) |
| | GND | GND | 9 |
| | SDA | GPIO2 / SDA1 | 3 |
| | SCL | GPIO3 / SCL1 | 5 |
| **Кнопка** | нога 1 | GPIO17 | 11 |
| | нога 2 | GND | 14 |

I2C-адрес OLED: **0x3C**. Pull-up для кнопки — внутренний (включён в коде).

## Конфигурация Pi

### 1. Включить интерфейсы

```bash
sudo raspi-config
# Interface Options → I2C → Enable
# Interface Options → SSH → Enable
```

### 2. `/boot/firmware/config.txt`

Должны быть строки:
```
dtparam=i2c_arm=on
dtparam=i2s=on
dtoverlay=adau7002-simple
dtparam=i2c_arm_baudrate=400000
```

⚠️ **`i2c_arm_baudrate=400000` обязателен** — на дефолтных 100kHz и тем более 10kHz OLED тормозит и анимации становятся слайдшоу.

После правки — `sudo reboot`.

### 3. Проверка железа

```bash
# Микрофон должен показать adau7002
arecord -l

# OLED должен светиться по адресу 0x3C
sudo apt install i2c-tools
i2cdetect -y 1

# Тестовая запись
arecord -D plughw:0,0 -f S32_LE -r 48000 -c 2 -d 3 /tmp/test.wav
```

## Установка софта

```bash
git clone https://github.com/nurkal022/FlashShazam.git ~/flashSHazam
cd ~/flashSHazam/raspberry

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env (НЕ коммитить!)
cat > .env << 'EOF'
SHAZAM_API_KEY=...           # https://shazam-api.com
APIFY_TOKEN=...              # https://console.apify.com/settings/integrations
EOF

mkdir -p recordings downloads
```

### Зависимости (нужно дополнительно через apt)

```bash
sudo apt install -y python3-pil python3-smbus i2c-tools
```

## Запуск

### Вручную
```bash
cd ~/flashSHazam/raspberry
source venv/bin/activate
python3 main.py
```

### Как systemd-сервис

`/etc/systemd/system/flashshazam.service`:
```ini
[Unit]
Description=FlashShazam Music Recognition
After=network.target sound.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/flashSHazam/raspberry
Environment=PATH=/home/admin/flashSHazam/raspberry/venv/bin:/usr/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/admin/flashSHazam/raspberry/venv/bin/python main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now flashshazam
sudo journalctl -u flashshazam -f       # логи
```

## Использование

1. На OLED — `FlashShazam / press button`
2. Жмёшь кнопку (Pin 11)
3. **Recording** — 15 сек запись с прогресс-баром
4. **Analyzing** — анимация точек, Shazam распознаёт (5-30 сек)
5. **Downloading** — анимация полосы, Apify скачивает (5-20 сек)
6. **Result** — название трека, артист, размер MP3 — остаётся до следующего нажатия

MP3 сохраняются в `~/flashSHazam/raspberry/downloads/`.

## Архитектура софта

| Файл | Назначение |
|---|---|
| `main.py` | главный цикл: кнопка → запись → распознавание → скачивание |
| `audio_recorder.py` | запись с I2S через PyAudio |
| `shazam_recognizer.py` | shazam-api.com — два запроса (upload + poll results) |
| `spotify_downloader.py` | Apify: `easyapi/spotify-music-mp3-downloader` для скачивания, `automation-lab/spotify-scraper` как поисковый фолбэк когда Shazam не отдал прямой Spotify URL |
| `display.py` | SH1106 OLED + фоновый аниматор для блокирующих стадий |
| `button.py` | GPIO17 с дебаунсом |
| `test_button_display.py` | live-тест: на OLED YES/NO в зависимости от состояния кнопки |

## Питание (портативная сборка)

Pi Zero 2W: **5V**, средне 250 mA, пик 600-700 mA. Вход — micro-USB.

**Простой путь:** powerbank 5V/2A, 5000-10000 mAh → 5-15 часов работы.

**DIY автономный** (~$10-12, нужна пайка):
- Банка **18650** Samsung 35E или LG MJ1 (3500 mAh)
- Готовый модуль «5V 2A USB Power Bank Charger Module» (TP4056 + MT3608 на одной плате)
- Тумблер SS12D00G3 в разрыв B+ → boost VIN
- microUSB кабель 15 см

Расчёт: 18650 3500mAh × 3.7V × 0.85 (КПД буста) ÷ 1.25W (avg) ≈ **8 часов автономки**.

⚠️ DW01 на TP4056 отрубает при 2.5V — для 18650 это маловато. Лучше отдельная защита с отсечкой 3.0V.

## Troubleshooting

### OLED не показывает ничего
- `i2cdetect -y 1` — должен быть `0x3C`
- Проверь SDA/SCL не перепутаны (Pin 3 и 5)
- Если не видит I2C: `dtparam=i2c_arm=on` в config.txt + reboot

### OLED тормозит / анимация рывками
- В config.txt: `dtparam=i2c_arm_baudrate=400000`. На 10kHz один кадр рендерится 3+ сек.

### Кнопка не реагирует
- `python3 test_button_display.py` — на экране YES/NO должно меняться
- Проверь: GPIO17 (Pin 11) ↔ GND (Pin 14)

### Микрофон тихий / низкий уровень
- Включить программный gain в `/etc/asound.conf` или через `alsamixer`

### Shazam: «Not enough balance»
- Кончился баланс на ключе. Сделать новый на shazam-api.com либо взять резервный из переменной `SHAZAM_API_KEY2` если он валиден.

### Apify: «Не нашли в Spotify»
- Search-фолбэк не нашёл — проверь логи `spotify_downloader.py`. Apify токен на `console.apify.com/settings/integrations`.

### Сервис не пишет логи в реальном времени
- В unit-файле должно быть `Environment=PYTHONUNBUFFERED=1`.

## Полезные команды на Pi

```bash
sudo systemctl restart flashshazam              # рестарт
sudo journalctl -u flashshazam -f \
  | grep -vE "ALSA lib|JackShm|jack server|snd_" # чистые логи приложения

# stop service на время отладки
sudo systemctl stop flashshazam
cd ~/flashSHazam/raspberry && source venv/bin/activate && python3 main.py
```
