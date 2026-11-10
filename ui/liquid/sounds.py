"""Procedural water sounds (no audio files needed): bloop, drip, pop, splash, click, success, open, close, toggles, warn.

Pure Python + wave module. Deterministic for a given seed. 22.05 kHz, 16-bit mono.
"""
from __future__ import annotations

import io
import math
import random
import struct
import wave
from typing import Dict, List

RATE = 22050
KINDS = ("bloop", "drip", "pop", "splash", "click", "success", "open", "close", "toggle_on", "toggle_off", "warn", "drop_in")


def _n(sec: float) -> int:
    return int(sec * RATE)


def _glide(f0: float, f1: float, dur: float, tau_sweep: float = 0.05) -> List[float]:
    """Sine with exponentially moving frequency (the 'bloop' of a bubble)."""
    out, ph = [], 0.0
    for i in range(_n(dur)):
        t = i / RATE
        f = f1 + (f0 - f1) * math.exp(-t / tau_sweep)
        ph += 2 * math.pi * f / RATE
        out.append(math.sin(ph))
    return out


def _env(n: int, attack: float, tau: float) -> List[float]:
    a = max(1, _n(attack))
    return [min(1.0, i / a) * math.exp(-(i / RATE) / tau) for i in range(n)]


def _mul(a: List[float], b: List[float]) -> List[float]:
    return [x * y for x, y in zip(a, b)]


def _mix(parts: List[List[float]], offsets: List[float]) -> List[float]:
    n = max(_n(o) + len(p) for p, o in zip(parts, offsets))
    out = [0.0] * n
    for p, o in zip(parts, offsets):
        s = _n(o)
        for i, v in enumerate(p):
            out[s + i] += v
    return out


def _lowpass(x: List[float], k: float) -> List[float]:
    y, acc = [], 0.0
    for v in x:
        acc += k * (v - acc)
        y.append(acc)
    return y


def _noise(n: int, rnd: random.Random) -> List[float]:
    return [rnd.uniform(-1, 1) for _ in range(n)]


def _bloop(f0: float, f1: float, dur: float, tau: float, sweep: float = 0.045) -> List[float]:
    g = _glide(f0, f1, dur, sweep)
    h = _glide(f0 * 2, f1 * 2, dur, sweep)
    s = [a + 0.22 * b for a, b in zip(g, h)]
    return _mul(s, _env(len(s), 0.004, tau))


def synth(kind: str, seed: int = 1) -> List[int]:
    if kind not in KINDS:
        raise ValueError(f"unknown sound {kind!r}")
    rnd = random.Random(seed)
    if kind == "bloop":
        x = _bloop(rnd.uniform(300, 420), rnd.uniform(850, 1050), 0.2, 0.06)
    elif kind == "drip":
        ping = _mul(_glide(1500, 980, 0.18, 0.03), _env(_n(0.18), 0.001, 0.045))
        tail = _mul(_glide(720, 690, 0.35, 0.2), _env(_n(0.35), 0.01, 0.1))
        x = _mix([ping, [0.35 * v for v in tail]], [0.0, 0.015])
    elif kind == "pop":
        nz = _mul(_lowpass(_noise(_n(0.05), rnd), 0.5), _env(_n(0.05), 0.0005, 0.009))
        body = _mul(_glide(260, 120, 0.09, 0.02), _env(_n(0.09), 0.001, 0.025))
        x = _mix([[1.3 * v for v in nz], body], [0.0, 0.0])
    elif kind == "splash":
        n = _n(0.45)
        nz = _mul(_lowpass(_noise(n, rnd), 0.18), _env(n, 0.006, 0.12))
        parts = [[1.5 * v for v in nz]] + [_bloop(rnd.uniform(380, 700), rnd.uniform(900, 1500), 0.14, 0.045) for _ in range(3)]
        x = _mix(parts, [0.0, 0.03, 0.09, 0.16])
    elif kind == "click":
        x = _bloop(620, 900, 0.07, 0.022, 0.02)
    elif kind == "success":
        x = _mix([_bloop(520, 700, 0.22, 0.07), _bloop(660, 880, 0.22, 0.07), _bloop(880, 1180, 0.3, 0.09)], [0.0, 0.08, 0.17])
    elif kind == "open":
        x = _mix([_bloop(260, 760, 0.2, 0.07, 0.07), [0.12 * v for v in _mul(_lowpass(_noise(_n(0.12), rnd), 0.1), _env(_n(0.12), 0.02, 0.05))]], [0.0, 0.0])
    elif kind == "close":
        x = _bloop(900, 330, 0.17, 0.05, 0.06)
    elif kind == "toggle_on":
        x = _mix([_bloop(420, 820, 0.11, 0.03, 0.02), _bloop(640, 1100, 0.12, 0.035, 0.02)], [0.0, 0.05])
    elif kind == "toggle_off":
        x = _mix([_bloop(820, 440, 0.11, 0.03, 0.02), _bloop(620, 330, 0.12, 0.035, 0.02)], [0.0, 0.05])
    elif kind == "drop_in":
        x = _mix([_bloop(300, 620, 0.16, 0.05, 0.05), [0.9 * v for v in _mul(_lowpass(_noise(_n(0.22), rnd), 0.22), _env(_n(0.22), 0.004, 0.06))]], [0.0, 0.0])
    else:  # warn
        x = _mix([_bloop(360, 240, 0.2, 0.08, 0.08), _bloop(300, 200, 0.24, 0.09, 0.08)], [0.0, 0.14])
    peak = max(1e-9, max(abs(v) for v in x))
    g = 0.8 / peak
    fade = min(len(x) // 4, _n(0.012))                       # 12 ms fade-out so no sound ends with a click
    for i in range(fade):
        x[len(x) - 1 - i] *= i / fade
    return [int(max(-1.0, min(1.0, v * g)) * 32000) for v in x]


def to_wav_bytes(samples: List[int]) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


def build_all(seed: int = 1) -> Dict[str, bytes]:
    return {k: to_wav_bytes(synth(k, seed)) for k in KINDS}
