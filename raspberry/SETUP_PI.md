# FlashShazam - Raspberry Pi Zero 2W Setup

## Hardware

### INMP441 I2S Microphone Wiring

| INMP441 | Raspberry Pi Zero 2W |
|---------|---------------------|
| VCC     | 3.3V (Pin 1)        |
| GND     | GND (Pin 6)         |
| SCK/BCLK| GPIO18 (Pin 12)     |
| WS/LRC  | GPIO19 (Pin 35)     |
| SD/DOUT | GPIO20 (Pin 38)     |
| L/R     | GND (Pin 6)         |

## Software Setup

### 1. Enable I2S

```bash
sudo raspi-config
# Interface Options → I2S → Enable
```

### 2. Configure Audio Overlay

Edit `/boot/firmware/config.txt`:
```bash
sudo nano /boot/firmware/config.txt
```

Add at the end:
```
dtparam=i2s=on
dtoverlay=adau7002-simple
```

Reboot:
```bash
sudo reboot
```

### 3. Verify Microphone

```bash
arecord -l
# Should show: card 0: adau7002 [adau7002]

# Test recording
arecord -D plughw:0,0 -f S32_LE -r 48000 -c 2 -d 3 /tmp/test.wav
```

### 4. Install FlashShazam

```bash
# Clone repo
git clone https://github.com/nurkal022/FlashShazam.git ~/flashSHazam

# Setup
cd ~/flashSHazam/raspberry
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with your API keys
cat > .env << EOF
SHAZAM_API_KEY=your_key_here
APIFY_TOKEN=your_token_here
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
EOF

# Create directories
mkdir -p recordings downloads
```

### 5. Run

```bash
cd ~/flashSHazam/raspberry
source venv/bin/activate
python main.py
```

Controls:
- **Enter** - Record and recognize
- **l** - Process last recording
- **q** - Quit

### 6. Auto-start (Optional)

```bash
# Enable service
sudo systemctl enable flashshazam
sudo systemctl start flashshazam

# Check status
sudo systemctl status flashshazam

# View logs
journalctl -u flashshazam -f
```

## Troubleshooting

### No audio devices

```bash
# Check kernel modules
lsmod | grep snd

# Check cards
cat /proc/asound/cards
```

### Low audio level

The INMP441 may need gain adjustment. Try:
```bash
alsamixer
# Or edit /etc/asound.conf for software gain
```

### Python errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

