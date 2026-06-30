"""Persistent strategy memory + falsification log (course Day 3: memory & state).

Two things the agent remembers across turns (and across runs, via JSON on disk):

1. **Attempts** — every genome tried, its league evaluation, who proposed it and
   the critic's verdict. This is the agent's episodic memory; the Proposer reads
   the recent slice to avoid re-treading ground and to hill-climb from the best.

2. **Falsifications** — short, human-readable lessons ("raid-only with no economy
   tops out ~elo 880"). This is the durable, distilled memory. It's the single
   highest-leverage idea we took from Orbit Wars: *write down what DOESN'T work*
   so neither a human nor an LLM wastes budget re-exploring dead ends.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from arena.sim import Strategy


@dataclass
class Attempt:
    round_index: int
    name: str
    genome: Dict[str, float]
    elo: float
    rank: int
    beats_top_anchor: bool
    winrate_vs_top: float
    rationale: str
    source: str          # "gemini" | "mock"
    verdict: str         # critic verdict


class StrategyMemory:
    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.attempts: List[Attempt] = []
        self.falsifications: List[str] = []
        self.best: Optional[Attempt] = None
        if path and os.path.exists(path):
            self.load()

    # -- recording ---------------------------------------------------------- #
    def record(self, attempt: Attempt) -> None:
        self.attempts.append(attempt)
        if (self.best is None) or (attempt.elo > self.best.elo):
            self.best = attempt
        self.save()

    def add_falsification(self, lesson: str) -> None:
        if lesson and lesson not in self.falsifications:
            self.falsifications.append(lesson)
            self.save()

    # -- recall (used to build the Proposer/Critic context) ----------------- #
    def recent(self, n: int = 6) -> List[Dict]:
        return [{"genome": a.genome, "elo": a.elo, "beats_top": a.beats_top_anchor}
                for a in self.attempts[-n:]]

    def best_genome(self) -> Optional[Dict]:
        return dict(self.best.genome) if self.best else None

    def best_elo(self) -> Optional[float]:
        return self.best.elo if self.best else None

    def already_tried(self, genome: Dict[str, float], tol: float = 1e-6) -> bool:
        for a in self.attempts:
            if all(abs(a.genome.get(k, 0) - genome.get(k, 0)) <= tol for k in genome):
                return True
        return False

    # -- persistence -------------------------------------------------------- #
    def save(self) -> None:
        if not self.path:
            return
        data = {
            "attempts": [asdict(a) for a in self.attempts],
            "falsifications": self.falsifications,
            "best": asdict(self.best) if self.best else None,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.attempts = [Attempt(**a) for a in data.get("attempts", [])]
        self.falsifications = data.get("falsifications", [])
        self.best = Attempt(**data["best"]) if data.get("best") else None

    def summary(self) -> str:
        if not self.attempts:
            return "memory: empty"
        return (f"memory: {len(self.attempts)} attempts, "
                f"best elo {self.best.elo:.0f} ({self.best.name}), "
                f"{len(self.falsifications)} falsifications recorded")
