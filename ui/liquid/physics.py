"""Pure-Python liquid physics: springs, droplets, splashes, bubbles. No Qt (unit-tested); the Qt overlay only draws the state."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

Color = Tuple[int, int, int]


@dataclass
class Spring:
    """Damped spring toward ``target``; stable at any frame time (sub-stepped)."""
    value: float = 0.0
    target: float = 0.0
    vel: float = 0.0
    stiffness: float = 220.0
    damping: float = 15.0

    def kick(self, impulse: float) -> None:
        self.vel += impulse

    def step(self, dt: float) -> float:
        dt = min(dt, 0.05)
        n = max(1, int(math.ceil(dt / (1 / 240))))
        h = dt / n
        for _ in range(n):
            acc = self.stiffness * (self.target - self.value) - self.damping * self.vel
            self.vel += acc * h
            self.value += self.vel * h
        return self.value

    @property
    def settled(self) -> bool:
        return abs(self.target - self.value) < 1e-3 and abs(self.vel) < 1e-2


@dataclass
class Drop:
    x: float
    y: float
    vx: float
    vy: float
    r: float
    life: float
    max_life: float
    color: Color = (120, 200, 255)
    kind: str = "drop"          # drop | bubble | spark
    phase: float = 0.0

    @property
    def alpha(self) -> float:
        k = max(0.0, self.life / self.max_life)
        return min(1.0, k * 1.6)

    def shape(self) -> Tuple[float, float, float]:
        """(rx, ry, angle_rad): drops stretch along their velocity like falling water."""
        if self.kind != "drop":
            return self.r, self.r, 0.0
        sp = math.hypot(self.vx, self.vy)
        s = min(1.9, 1.0 + sp / 700.0)
        return self.r / math.sqrt(s), self.r * s, math.atan2(self.vy, self.vx) - math.pi / 2


class ParticleSystem:
    """Droplets/bubbles with gravity. ``rng`` is injectable so tests are deterministic."""

    def __init__(self, gravity: float = 1500.0, max_particles: int = 260, rng: Optional[random.Random] = None) -> None:
        self.gravity, self.max_particles = gravity, max_particles
        self.rng = rng or random.Random()
        self.items: List[Drop] = []

    # ---- emitters -------------------------------------------------
    def _add(self, d: Drop) -> None:
        if len(self.items) >= self.max_particles:
            self.items.pop(0)
        self.items.append(d)

    def drip(self, x: float, y: float, color: Color = (120, 200, 255), n: int = 1, size: float = 5.0) -> None:
        for _ in range(n):
            r = size * self.rng.uniform(0.7, 1.3)
            self._add(Drop(x + self.rng.uniform(-6, 6), y, self.rng.uniform(-12, 12), self.rng.uniform(0, 40), r, 1.1, 1.1, color))

    def splash(self, x: float, y: float, strength: float = 1.0, color: Color = (120, 200, 255), n: int = 16) -> None:
        for _ in range(n):
            ang = math.radians(self.rng.uniform(-165, -15))
            sp = self.rng.uniform(220, 640) * strength
            self._add(Drop(x, y, math.cos(ang) * sp, math.sin(ang) * sp, self.rng.uniform(2.5, 6.5) * (0.6 + strength / 2), 0.9, 0.9, color))

    def trail(self, x: float, y: float, vx: float, vy: float, color: Color = (120, 200, 255), chance: float = 0.55) -> None:
        if self.rng.random() < chance:
            self._add(Drop(x + self.rng.uniform(-8, 8), y + self.rng.uniform(-4, 8), -vx * 0.05 + self.rng.uniform(-30, 30),
                           -vy * 0.05 + self.rng.uniform(0, 60), self.rng.uniform(2.0, 4.8), 0.75, 0.75, color))

    def bubbles(self, x: float, y: float, n: int = 8, color: Color = (190, 235, 255), spread: float = 26.0) -> None:
        for _ in range(n):
            self._add(Drop(x + self.rng.uniform(-spread, spread), y + self.rng.uniform(-8, 8), self.rng.uniform(-30, 30),
                           self.rng.uniform(-170, -60), self.rng.uniform(3, 9), 1.4, 1.4, color, "bubble", self.rng.uniform(0, 6.28)))

    # ---- simulation -----------------------------------------------
    def step(self, dt: float, floor: Optional[float] = None) -> None:
        dt = min(dt, 0.05)
        alive: List[Drop] = []
        for d in self.items:
            d.life -= dt
            if d.life <= 0:
                continue
            if d.kind == "drop":
                d.vy += self.gravity * dt
                d.vx *= 1 - min(1.0, 0.8 * dt)
                if floor is not None and d.y > floor and d.vy > 0:     # lands: tiny hop + shrink, then fades
                    d.vy *= -0.18
                    d.vx *= 0.5
                    d.r *= 0.8
                    d.y = floor
            else:                                                       # bubble: buoyancy + wobble
                d.phase += dt * 7.0
                d.vx += math.sin(d.phase) * 120 * dt
                d.vy -= 160 * dt
                d.vx *= 1 - min(1.0, 1.4 * dt)
                d.vy *= 1 - min(1.0, 0.9 * dt)
            d.x += d.vx * dt
            d.y += d.vy * dt
            if d.r > 0.4:
                alive.append(d)
        self.items = alive

    @property
    def active(self) -> bool:
        return bool(self.items)


@dataclass
class Bubble:
    x: float          # 0..1 of width
    y: float          # 0..1 of height (1 = bottom)
    r: float          # px
    speed: float      # fraction of height per second
    phase: float
    sway: float


class BubbleField:
    """Ambient bubbles that float up behind everything (cheap background life)."""

    def __init__(self, count: int = 14, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random(7)
        self.items = [self._new(rand_y=True) for _ in range(count)]

    def _new(self, rand_y: bool = False) -> Bubble:
        r = self.rng
        return Bubble(r.uniform(0.03, 0.97), r.uniform(0, 1) if rand_y else 1.08, r.uniform(5, 26), r.uniform(0.018, 0.06), r.uniform(0, 6.28), r.uniform(0.004, 0.018))

    def step(self, dt: float) -> None:
        for i, b in enumerate(self.items):
            b.y -= b.speed * dt
            b.phase += dt * 1.3
            if b.y < -0.1:
                self.items[i] = self._new()

    def position(self, b: Bubble, w: float, h: float) -> Tuple[float, float]:
        return (b.x + math.sin(b.phase) * b.sway) * w, b.y * h


def blend(a: Color, b: Color, t: float) -> Color:
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def hex_to_rgb(h: str) -> Color:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
