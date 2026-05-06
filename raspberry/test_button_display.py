#!/usr/bin/env python3
"""
Простой тест: на OLED показывает большое ДА если кнопка нажата, иначе НЕТ.
Останови flashshazam перед запуском: sudo systemctl stop flashshazam
"""

import sys
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from display import Display
from button import BUTTON_PIN


def render(display, pressed):
    img = Image.new("1", (display.width, display.height), 0)
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40
        )
    except Exception:
        font_big = ImageFont.load_default()

    text = "YES" if pressed else "NO"
    bbox = draw.textbbox((0, 0), text, font=font_big)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (display.width - w) // 2
    y = (display.height - h) // 2 - 4
    draw.text((x, y), text, fill=1, font=font_big)

    display.display_image(img)


def main(duration=120):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    display = Display()
    if not display._enabled:
        print("OLED недоступен")
        return 1

    last_state = None
    start = time.time()
    print(f"Жми кнопку GPIO{BUTTON_PIN}. {duration}s, Ctrl+C для выхода.")

    try:
        while time.time() - start < duration:
            pressed = GPIO.input(BUTTON_PIN) == 0
            if pressed != last_state:
                render(display, pressed)
                print("PRESSED" if pressed else "released")
                last_state = pressed
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nstop")
    finally:
        GPIO.cleanup()
    return 0


if __name__ == "__main__":
    dur = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    sys.exit(main(dur))
