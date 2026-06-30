"""The calibrated anchor ladder.

These hand-written strategies span the skill spectrum from naive to strong. Their
*order* on the league is what makes the league trustworthy: if a brand-new eval
harness can't reproduce a sensible anchor ordering, you can't trust what it says
about a novel strategy. This is the single most important lesson we carried over
from Orbit Wars — calibrate the league against known anchors *first*, then let it
judge new agents.

The agent under test must climb this ladder. `adaptive` is the top anchor (our
local stand-in for the Orbit Wars "producer" ceiling) — beating it is the goal.
"""

from __future__ import annotations

from typing import Dict, List

from .sim import Strategy

# Each anchor is a genome (see arena.sim.GENOME_KEYS) + a short rationale.
_ANCHOR_SPECS: List[Dict] = [
    {
        "name": "naive_miner",
        "note": "Hoards ore, never converts it to points. Bottom of the ladder.",
        "genome": {"mine": 5.0, "build": 0.2, "expand": 0.2, "fortify": 0.1,
                   "raid": 0.1, "raid_threshold": 20},
    },
    {
        "name": "all_in_raider",
        "note": "Builds a fleet and raids relentlessly; no economy backbone.",
        "genome": {"mine": 1.2, "build": 3.0, "expand": 0.3, "fortify": 0.2,
                   "raid": 2.5, "raid_threshold": 2},
    },
    {
        "name": "greedy_expander",
        "note": "Expands at every chance, undefended. Scores fast, dies to raids.",
        "genome": {"mine": 1.5, "build": 0.3, "expand": 3.0, "fortify": 0.3,
                   "raid": 0.2, "raid_threshold": 20, "expand_late_bonus": 0.5},
    },
    {
        "name": "turtle",
        "note": "Expands behind shields; reactive fortification vs fleets.",
        "genome": {"mine": 1.6, "build": 0.6, "expand": 2.0, "fortify": 1.8,
                   "raid": 0.3, "raid_threshold": 8, "fortify_threat_scale": 0.6},
    },
    {
        "name": "balanced",
        "note": "Mixed economy into expansion, with a credible raiding deterrent.",
        "genome": {"mine": 1.8, "build": 1.4, "expand": 2.0, "fortify": 1.0,
                   "raid": 1.2, "raid_threshold": 4, "expand_late_bonus": 0.4,
                   "fortify_threat_scale": 0.4},
    },
    {
        "name": "adaptive",
        "note": "Top anchor: economy first, expands late, fortifies under threat, "
                "raids only with a decisive fleet. The local 'ceiling' to beat.",
        "genome": {"mine": 2.2, "build": 1.5, "expand": 1.9, "fortify": 1.2,
                   "raid": 1.6, "raid_threshold": 5, "expand_late_bonus": 1.2,
                   "fortify_threat_scale": 0.8},
    },
]

ANCHORS: List[Strategy] = [
    Strategy(name=s["name"], genome=dict(s["genome"]), note=s["note"])
    for s in _ANCHOR_SPECS
]

_BY_NAME = {s.name: s for s in ANCHORS}


def get_anchor(name: str) -> Strategy:
    return _BY_NAME[name]
