"""Is the person really working, or is the screen just sitting there?

Raw OS idle time alone gets two cases wrong: (1) a *video call / slides / reading a long build log* has no input but is real work, and (2) a *mouse jiggler or a
frozen app* shows constant "activity" while nothing changes. This model fuses three cheap signals - input idle seconds, how much the screen content changed
(a tiny 16x9 thumbnail difference, 0..1) and the application category - and only ever *refines* the basic idle verdict:

* ACTIVE + screen static for ``frozen_after`` seconds  -> away ("frozen")      (jiggler / hung app / locked-but-awake)
* idle + screen alive + work-type app (call, docs, editor) -> work ("passive") for at most ``passive_limit`` seconds, then away
* everything else keeps the basic verdict

All state is a couple of timestamps, so it costs nothing at runtime.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple

WORK, NEUTRAL, AWAY = "work", "neutral", "away"


@dataclass
class EngagementConfig:
    screen_static_eps: float = 0.004      # mean |delta| below this = "nothing changed"
    screen_live: float = 0.02             # above this = something is really happening on screen
    frozen_after: int = 900               # seconds of static screen (while "active") before we call it frozen
    passive_limit: int = 1500             # max seconds of input-less presence we still count as work (a meeting, a long read)
    passive_categories: Set[str] = field(default_factory=lambda: {"communication", "documents", "development", "design"})


class EngagementModel:
    def __init__(self, cfg: Optional[EngagementConfig] = None) -> None:
        self.cfg = cfg or EngagementConfig()
        self._static_since: Optional[dt.datetime] = None
        self._passive_since: Optional[dt.datetime] = None

    def reset(self) -> None:
        self._static_since = self._passive_since = None

    def refine(self, base_state: str, idle_sec: float, screen_delta: Optional[float], category: str, now: dt.datetime, idle_limit: int = 120) -> Tuple[str, str]:
        """Return (state, reason). ``base_state`` is the plain idle/category verdict."""
        c = self.cfg
        if screen_delta is not None:
            if screen_delta < c.screen_static_eps:
                self._static_since = self._static_since or now
            else:
                self._static_since = None
        # (1) busy-looking but frozen
        if base_state == WORK and idle_sec < idle_limit and screen_delta is not None and self._static_since is not None:
            if (now - self._static_since).total_seconds() >= c.frozen_after:
                return AWAY, "frozen"
        # (2) no input but the screen is alive in a work app: a call, a presentation, reading
        if base_state == AWAY and idle_sec >= idle_limit:
            if screen_delta is not None and screen_delta >= c.screen_live and category in c.passive_categories:
                self._passive_since = self._passive_since or now
                if (now - self._passive_since).total_seconds() <= c.passive_limit:
                    return WORK, "passive"
                return AWAY, "passive_expired"
            return AWAY, "idle"
        if idle_sec < idle_limit:
            self._passive_since = None
        return base_state, "input" if base_state != AWAY else "away"
