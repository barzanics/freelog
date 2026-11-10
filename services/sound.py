"""Focus soundscapes generated procedurally (no audio files shipped): white / pink / brown noise and rain."""
from __future__ import annotations

import io
import random
import struct
import wave
from pathlib import Path
from typing import Union

KINDS = ("white", "pink", "brown", "rain")


def generate_samples(kind: str, seconds: float = 4.0, rate: int = 22050, seed: int = 1) -> list:
    """Return 16-bit samples; designed to loop (short crossfade at the seam)."""
    if kind not in KINDS:
        raise ValueError("unknown soundscape")
    rnd, n = random.Random(seed), int(seconds * rate)
    out, b, p = [], 0.0, [0.0] * 3
    for i in range(n):
        w = rnd.uniform(-1, 1)
        if kind == "white":
            v = w * 0.5
        elif kind == "brown":
            b = max(-1.0, min(1.0, b + w * 0.02)) * 0.998
            v = b * 3.0
        elif kind == "pink":      # Paul Kellet's economy filter
            p[0] = 0.99765 * p[0] + w * 0.0990460
            p[1] = 0.96300 * p[1] + w * 0.2965164
            p[2] = 0.57000 * p[2] + w * 1.0526913
            v = (p[0] + p[1] + p[2] + w * 0.1848) * 0.12
        else:                     # rain: pink-ish hiss + sparse droplets
            p[0] = 0.97 * p[0] + w * 0.15
            v = p[0] * 0.8 + (rnd.uniform(-1, 1) * 0.6 if rnd.random() < 0.0015 else 0.0)
        out.append(max(-1.0, min(1.0, v)))
    fade = min(n // 10, rate // 4)
    for i in range(fade):                       # crossfade tail into head for seamless looping
        t = i / fade
        out[i] = out[i] * t + out[n - fade + i] * (1 - t)
    return [int(s * 32000) for s in out]


def write_wav(kind: str, dest: Union[str, Path], seconds: float = 4.0, rate: int = 22050) -> Path:
    dest = Path(dest)
    with wave.open(str(dest), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(struct.pack(f"<{int(seconds * rate)}h", *generate_samples(kind, seconds, rate)))
    return dest
