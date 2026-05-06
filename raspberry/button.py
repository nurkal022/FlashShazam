#!/usr/bin/env python3
"""
Button module - GPIO17 (Pin 11)
"""

import RPi.GPIO as GPIO
import time

BUTTON_PIN = 17  # GPIO17 = Pin 11


class Button:
    def __init__(self, pin=BUTTON_PIN):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._running = True
        print(f'✓ Кнопка на GPIO{self.pin} (Pin 11)')

    def is_pressed(self):
        return GPIO.input(self.pin) == GPIO.LOW

    def wait_for_press(self, timeout=None):
        start = time.time()
        while self._running:
            if GPIO.input(self.pin) == GPIO.LOW:
                time.sleep(0.05)
                if GPIO.input(self.pin) == GPIO.LOW:
                    while GPIO.input(self.pin) == GPIO.LOW:
                        time.sleep(0.01)
                    return True

            if timeout and (time.time() - start) > timeout:
                return False

            time.sleep(0.01)
        return False

    def cleanup(self):
        self._running = False
