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

    def wait_for_press_classified(self, timeout=None, long_threshold=1.5):
        """
        Ждёт нажатия и классифицирует:
            'short' — обычное короткое нажатие
            'long'  — удержание дольше long_threshold секунд
            None    — таймаут
        Возвращает после отпускания (или сразу как только пересечён порог long).
        """
        start = time.time()
        while self._running:
            if GPIO.input(self.pin) == GPIO.LOW:
                time.sleep(0.05)
                if GPIO.input(self.pin) == GPIO.LOW:
                    t0 = time.time()
                    while GPIO.input(self.pin) == GPIO.LOW:
                        if time.time() - t0 >= long_threshold:
                            while GPIO.input(self.pin) == GPIO.LOW:
                                time.sleep(0.02)
                            return 'long'
                        time.sleep(0.02)
                    return 'short'

            if timeout and (time.time() - start) > timeout:
                return None

            time.sleep(0.01)
        return None

    def held_for(self):
        """
        Если кнопка зажата прямо сейчас — возвращает сколько секунд она зажата.
        Иначе возвращает 0. Используется для опроса во время блокирующих операций
        (например, чтобы отменить запись по долгому удержанию).
        """
        if not hasattr(self, '_hold_start'):
            self._hold_start = None
        if GPIO.input(self.pin) == GPIO.LOW:
            if self._hold_start is None:
                self._hold_start = time.time()
            return time.time() - self._hold_start
        else:
            self._hold_start = None
            return 0.0

    def cleanup(self):
        self._running = False
