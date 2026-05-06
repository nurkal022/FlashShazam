#!/usr/bin/env python3
"""
SH1106 OLED Display driver - direct I2C communication
"""

import smbus2
import threading
import time
from PIL import Image, ImageDraw, ImageFont


class Display:
    def __init__(self, bus_num=1, address=0x3C, width=128, height=64):
        self._anim_thread = None
        self._anim_stop = threading.Event()
        self._lock = threading.Lock()
        try:
            self.bus = smbus2.SMBus(bus_num)
            self.addr = address
            self.width = width
            self.height = height
            self._enabled = True
            
            # SH1106 init sequence
            self._init_display()
            self.clear()
            print(f'✓ OLED SH1106 инициализирован ({width}x{height})')
            
        except Exception as e:
            print(f'⚠️ OLED недоступен: {e}')
            self._enabled = False
            self.bus = None
    
    def _write_cmd(self, cmd):
        """Отправить команду"""
        if not self._enabled:
            return
        try:
            self.bus.write_byte_data(self.addr, 0x00, cmd)
        except:
            pass
    
    def _write_data(self, data):
        """Отправить данные"""
        if not self._enabled:
            return
        try:
            self.bus.write_byte_data(self.addr, 0x40, data)
        except:
            pass
    
    def _init_display(self):
        """Инициализация SH1106"""
        init_seq = [
            0xAE,        # Display OFF
            0xD5, 0x80,  # Clock divide
            0xA8, 0x3F,  # Multiplex ratio
            0xD3, 0x00,  # Display offset
            0x40,        # Start line
            0x8D, 0x14,  # Charge pump
            0x20, 0x00,  # Memory mode
            0xA1,        # Segment remap
            0xC8,        # COM scan direction
            0xDA, 0x12,  # COM pins
            0x81, 0xCF,  # Contrast
            0xD9, 0xF1,  # Pre-charge
            0xDB, 0x40,  # VCOM detect
            0xA4,        # Display all on resume
            0xA6,        # Normal display (not inverted)
            0xAF,        # Display ON
        ]
        
        for cmd in init_seq:
            self._write_cmd(cmd)
            time.sleep(0.001)
    
    def clear(self):
        """Очистить экран"""
        self.stop_animation()
        if not self._enabled:
            return
        
        for page in range(8):
            self._write_cmd(0xB0 + page)  # Set page
            self._write_cmd(0x02)  # Set lower column (SH1106 offset)
            self._write_cmd(0x10)  # Set higher column
            
            for _ in range(128):
                self._write_data(0x00)
    
    def display_image(self, image):
        """Отобразить PIL Image (1-bit, 128x64)"""
        if not self._enabled:
            return

        with self._lock:
            image = image.convert('1')
            pixels = list(image.getdata())
            for page in range(8):
                self._write_cmd(0xB0 + page)
                self._write_cmd(0x02)  # SH1106 offset
                self._write_cmd(0x10)
                for x in range(128):
                    byte = 0
                    for bit in range(8):
                        y = page * 8 + bit
                        if y < 64:
                            if pixels[y * 128 + x]:
                                byte |= (1 << bit)
                    self._write_data(byte)

    def stop_animation(self):
        if self._anim_thread:
            self._anim_stop.set()
            self._anim_thread.join(timeout=1)
            self._anim_thread = None

    def _animate(self, frame_fn, fps=8):
        """Запустить фоновую анимацию. frame_fn(i) -> PIL Image."""
        self.stop_animation()
        if not self._enabled:
            return
        self._anim_stop.clear()

        def loop():
            i = 0
            interval = 1.0 / fps
            while not self._anim_stop.is_set():
                try:
                    img = frame_fn(i)
                    self.display_image(img)
                except Exception:
                    pass
                i += 1
                if self._anim_stop.wait(interval):
                    break

        self._anim_thread = threading.Thread(target=loop, daemon=True)
        self._anim_thread.start()
    
    def show_text(self, lines):
        """Показать текст (список строк)"""
        if not self._enabled:
            for i, line in enumerate(lines):
                print(f'[DISPLAY] {line}')
            return
        
        image = Image.new('1', (self.width, self.height), 0)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        y = 2
        for line in lines:
            draw.text((2, y), str(line)[:21], fill=1, font=font)
            y += 16
        
        self.display_image(image)
    
    def show_status(self, line1, line2='', line3=''):
        self.show_text([line1, line2, line3])
    
    def show_recording(self, seconds_left):
        self.stop_animation()
        image = Image.new('1', (self.width, self.height), 0)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        draw.text((30, 5), 'RECORDING', fill=1, font=font)
        draw.rectangle((10, 30, 118, 45), outline=1)
        
        progress = int((15 - seconds_left) / 15 * 106)
        if progress > 0:
            draw.rectangle((12, 32, 12 + progress, 43), fill=1)
        
        draw.text((52, 50), f'{seconds_left}s', fill=1, font=font)
        self.display_image(image)
    
    def _font(self, size):
        try:
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
            )
        except Exception:
            return ImageFont.load_default()

    def _wrap(self, draw, text, font, max_w):
        words = str(text).split()
        if not words:
            return [""]
        lines, cur = [], words[0]
        for w in words[1:]:
            test = cur + " " + w
            if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines[:2]

    def show_analyzing(self):
        f = self._font(14)
        f_dot = self._font(10)

        def frame(i):
            img = Image.new("1", (self.width, self.height), 0)
            draw = ImageDraw.Draw(img)

            text = "Analyzing"
            bbox = draw.textbbox((0, 0), text, font=f)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, 14), text, fill=1, font=f)

            # 3 точки, прыгающие по очереди
            cx, cy = self.width // 2, 46
            active = i % 3
            for k, dx in enumerate((-14, 0, 14)):
                r = 4 if k == active else 2
                draw.ellipse((cx + dx - r, cy - r, cx + dx + r, cy + r), fill=1)
            return img

        self._animate(frame, fps=4)

    def show_downloading(self, title):
        f_top = self._font(13)
        f_title = self._font(11)
        title_lines = None

        def frame(i):
            nonlocal title_lines
            img = Image.new("1", (self.width, self.height), 0)
            draw = ImageDraw.Draw(img)
            if title_lines is None:
                title_lines = self._wrap(draw, title, f_title, self.width - 8)
            draw.text((4, 2), "Downloading", fill=1, font=f_top)
            for n, line in enumerate(title_lines):
                draw.text((4, 22 + n * 14), line, fill=1, font=f_title)
            # бегущая полоска внизу
            bar_w = 22
            x = (i * 6) % (self.width + bar_w) - bar_w
            draw.rectangle((4, 56, self.width - 5, 60), outline=1)
            draw.rectangle((max(5, x), 57, min(self.width - 6, x + bar_w), 59), fill=1)
            return img

        self._animate(frame, fps=8)

    def show_result(self, title, artist, size_mb=None):
        """Финальный экран: остаётся на дисплее до следующего нажатия."""
        self.stop_animation()
        img = Image.new("1", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)

        f_title = self._font(13)
        f_artist = self._font(11)
        f_meta = self._font(10)

        title_lines = self._wrap(draw, title, f_title, self.width - 6)
        for i, line in enumerate(title_lines[:2]):
            draw.text((3, 2 + i * 15), line, fill=1, font=f_title)

        artist_y = 2 + len(title_lines[:2]) * 15 + 2
        artist_line = self._wrap(draw, artist, f_artist, self.width - 6)[0]
        draw.text((3, artist_y), artist_line, fill=1, font=f_artist)

        # нижняя полоса: размер слева, подсказка справа
        draw.line((0, 52, self.width - 1, 52), fill=1)
        if size_mb is not None:
            draw.text((3, 54), f"{size_mb:.1f}MB", fill=1, font=f_meta)
        draw.text((self.width - 30, 54), "PRESS", fill=1, font=f_meta)
        self.display_image(img)

    # совместимость со старым main.py
    def show_track(self, title, artist):
        self.show_result(title, artist, size_mb=None)

    def show_success(self, title, size_mb=0, artist=""):
        self.show_result(title, artist, size_mb=size_mb)

    def show_error(self, message):
        self.stop_animation()
        img = Image.new("1", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        f_big = self._font(16)
        f_small = self._font(10)
        draw.text((38, 2), "ERROR", fill=1, font=f_big)
        for i, line in enumerate(self._wrap(draw, message, f_small, self.width - 6)):
            draw.text((3, 26 + i * 12), line, fill=1, font=f_small)
        draw.line((0, 52, self.width - 1, 52), fill=1)
        draw.text((self.width - 30, 54), "PRESS", fill=1, font=f_small)
        self.display_image(img)

    def show_ready(self):
        self.stop_animation()
        img = Image.new("1", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        f_big = self._font(15)
        f_small = self._font(10)
        draw.text((6, 16), "FlashShazam", fill=1, font=f_big)
        draw.line((0, 40, self.width - 1, 40), fill=1)
        draw.text((26, 48), "press button", fill=1, font=f_small)
        self.display_image(img)
    
    def __del__(self):
        if self.bus:
            self.bus.close()


if __name__ == '__main__':
    # Тест
    display = Display()
    
    if display._enabled:
        print('Testing OLED...')
        
        display.show_ready()
        time.sleep(2)
        
        for i in range(15, 0, -3):
            display.show_recording(i)
            time.sleep(0.5)
        
        display.show_analyzing()
        time.sleep(2)
        
        display.show_track('Bohemian Rhapsody', 'Queen')
        time.sleep(2)
        
        display.show_downloading('Bohemian Rhapsody')
        time.sleep(2)
        
        display.show_success('Bohemian Rhapsody', 8.5)
        time.sleep(2)
        
        display.clear()
        print('Test complete!')
    else:
        print('OLED not available')
