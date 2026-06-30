"""Orbital Skirmish arena — a self-contained competitive 2-player simulation.

This package is the *testbed* for the Arena Strategist capstone agent. It is a
compact, fully deterministic re-creation (in spirit) of the kind of competitive
Kaggle simulation we tackled in Orbit Wars: cheap to simulate by the thousand,
with a genuine, calibrated skill ladder among scripted baseline agents.

Nothing here touches the live Orbit Wars competition or its locked submission —
this is an independent, MIT-spirit sandbox built for the course capstone.
"""

from .sim import Strategy, GameConfig, play_game, DEFAULT_GENOME, GENOME_KEYS
from .anchors import ANCHORS, get_anchor
from .league import League, LeagueResult

__all__ = [
    "Strategy",
    "GameConfig",
    "play_game",
    "DEFAULT_GENOME",
    "GENOME_KEYS",
    "ANCHORS",
    "get_anchor",
    "League",
    "LeagueResult",
]
