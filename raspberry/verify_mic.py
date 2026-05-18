#!/usr/bin/env python3
"""
Проверка микрофона после пайки.
Запускает 5-секундную запись через arecord, анализирует уровни и
выдаёт чёткий вердикт. Не зависит от Shazam / PyAudio.

Запускать ПОСЛЕ остановки flashshazam (или в любое время — захватит
устройство сам). При окончании, если сервис был запущен — оставляет
его запущенным.
"""

import os
import struct
import subprocess
import sys
import wave

DEV = "plughw:0,0"
DURATION = 5
RATE = 48000
FORMAT = "S32_LE"
CHANNELS = 2
OUT = "/tmp/verify_mic.wav"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def stop_service():
    subprocess.run(
        ["sudo", "-n", "systemctl", "stop", "flashshazam"],
        capture_output=True,
    )


def record():
    print(f"📡 Запись {DURATION}с с {DEV} ({FORMAT}, {RATE}Hz, {CHANNELS}ch)...")
    r = subprocess.run(
        [
            "arecord",
            "-D", DEV,
            "-f", FORMAT,
            "-r", str(RATE),
            "-c", str(CHANNELS),
            "-d", str(DURATION),
            OUT,
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"{RED}❌ arecord упал: {r.stderr}{RESET}")
        sys.exit(2)


def analyze():
    w = wave.open(OUT, "rb")
    raw = w.readframes(w.getnframes())
    sr = w.getframerate() * w.getnchannels()
    w.close()

    n = len(raw) // 4
    vals = struct.unpack(f"<{n}i", raw)
    abs_v = [abs(v) for v in vals]
    MAX = 2 ** 31

    print("\nПо секундам (rms / peak):")
    per_sec = []
    for i in range(0, len(vals) - sr, sr):
        c = abs_v[i:i + sr]
        rms = (sum(x * x for x in c) / len(c)) ** 0.5
        pk = max(c)
        rms_pct = rms / MAX * 100
        pk_pct = pk / MAX * 100
        per_sec.append((rms_pct, pk_pct))
        bar = "█" * min(40, int(pk_pct * 2))
        print(f"  t={i // sr}s  rms={rms_pct:6.3f}%  peak={pk_pct:5.2f}%  {bar}")

    return per_sec


def verdict(per_sec):
    if not per_sec:
        print(f"\n{RED}❌ Запись пустая.{RESET}")
        return 2

    # Игнорируем нулевую секунду (там часто всплеск инициализации).
    body = per_sec[1:] if len(per_sec) > 1 else per_sec
    max_rms = max(rms for rms, _ in body)
    max_peak = max(pk for _, pk in body)

    print()
    if max_rms == 0 and max_peak == 0:
        print(f"{RED}❌ Микрофон ничего не отдаёт — все нули после старта.{RESET}")
        print("   Проверь пайку SD/DOUT (Pin 38, GPIO20), VCC и GND.")
        return 2

    if max_rms < 0.05 and max_peak < 1.0:
        print(f"{YELLOW}⚠️  Мик отвечает, но уровень очень низкий (rms<0.05%).{RESET}")
        print("   Возможно: цепь WS/LRC или BCLK неустойчива, либо тихий источник.")
        print("   Хлопни / поговори рядом — повтори тест.")
        return 1

    print(f"{GREEN}✅ Микрофон работает.{RESET}")
    print(f"   Макс rms={max_rms:.2f}%  peak={max_peak:.2f}%")
    print("   Можно запускать flashshazam: sudo systemctl start flashshazam")
    return 0


def main():
    stop_service()
    record()
    per_sec = analyze()
    sys.exit(verdict(per_sec))


if __name__ == "__main__":
    main()
