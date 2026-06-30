"""Orbital Skirmish — a compact, fully deterministic 2-player strategy game.

Why this exists
---------------
The capstone agent needs a *competitive environment with a real skill ladder* so
that an LLM-proposed strategy can be scored objectively. We deliberately keep the
game:

* **deterministic** — given two strategies and a map, the outcome is fixed, so the
  league is reproducible (no Monte-Carlo noise to fight, the lesson we learned the
  hard way calibrating the Orbit Wars league);
* **cheap** — a full game is a few dozen integer turns, so we can run a 7-agent
  round-robin over a map pool in well under a second;
* **strategic** — economy / military / territory / defense form a
  rock-paper-scissors-ish loop, so no single pure strategy dominates and a genuine
  ladder emerges (miner < raider < expander < turtle < balanced < adaptive).

A *strategy* is an 8-number "genome" that parameterises a fixed, legible policy.
Representing strategies as a small vector (rather than arbitrary code) makes them
trivial to serialise, store in memory, mutate, and — crucially — to ask an LLM to
propose, while staying safe and sandbox-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# --------------------------------------------------------------------------- #
# Strategy genome
# --------------------------------------------------------------------------- #

# The eight tunable knobs of the policy. Order matters: it defines the vector
# layout used by the league, the memory store, and the LLM proposal schema.
GENOME_KEYS: Tuple[str, ...] = (
    "mine",                 # base priority for MINE (+3 ore)
    "build",                # base priority for BUILD (-3 ore, +1 ship)
    "expand",               # base priority for EXPAND (-5 ore, +1 base = points)
    "fortify",              # base priority for FORTIFY (-2 ore, +1 shield)
    "raid",                 # per-ship priority for RAID (attack)
    "raid_threshold",       # min ships before RAID is considered
    "expand_late_bonus",    # EXPAND priority *= (1 + bonus * turn_fraction)
    "fortify_threat_scale", # FORTIFY priority *= (1 + scale * opponent_ships)
)

# A sensible, deliberately mediocre starting point the agent improves on.
DEFAULT_GENOME: Dict[str, float] = {
    "mine": 1.0,
    "build": 1.0,
    "expand": 1.0,
    "fortify": 1.0,
    "raid": 1.0,
    "raid_threshold": 3,
    "expand_late_bonus": 0.0,
    "fortify_threat_scale": 0.0,
}


@dataclass
class Strategy:
    """A named policy. `genome` holds the eight knobs in GENOME_KEYS."""

    name: str
    genome: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_GENOME))
    note: str = ""  # free-text rationale (the LLM fills this in)

    def normalised(self) -> Dict[str, float]:
        """Return a genome with every key present and clamped to safe ranges."""
        g = dict(DEFAULT_GENOME)
        for k, v in (self.genome or {}).items():
            if k in DEFAULT_GENOME:
                g[k] = v
        # Clamp to keep the policy well-defined and the search bounded.
        for k in ("mine", "build", "expand", "fortify", "raid"):
            g[k] = float(max(0.0, min(10.0, g[k])))
        g["raid_threshold"] = int(max(1, min(20, round(g["raid_threshold"]))))
        g["expand_late_bonus"] = float(max(0.0, min(5.0, g["expand_late_bonus"])))
        g["fortify_threat_scale"] = float(max(0.0, min(2.0, g["fortify_threat_scale"])))
        return g

    def vector(self) -> List[float]:
        g = self.normalised()
        return [float(g[k]) for k in GENOME_KEYS]


# --------------------------------------------------------------------------- #
# Game configuration ("map")
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class GameConfig:
    """A single 'map'. Varying these gives us a map pool, like Orbit Wars."""

    turns: int = 50
    start_ore: int = 10
    mine_yield: int = 3
    build_cost: int = 3
    expand_cost: int = 5
    fortify_cost: int = 2


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #

# Action codes
MINE, BUILD, EXPAND, FORTIFY, RAID = 0, 1, 2, 3, 4
ACTION_NAMES = {MINE: "MINE", BUILD: "BUILD", EXPAND: "EXPAND",
                FORTIFY: "FORTIFY", RAID: "RAID"}


class _Side:
    __slots__ = ("ore", "ships", "bases", "shield")

    def __init__(self, start_ore: int):
        self.ore = start_ore
        self.ships = 0
        self.bases = 0
        self.shield = 0


def _choose_action(me: _Side, opp: _Side, g: Dict[str, float],
                   turn: int, cfg: GameConfig) -> int:
    """Score every legal action by the genome and return the best one.

    MINE is always legal (costs nothing), so the policy is always defined.
    Ties break by a fixed action order, keeping the game deterministic.
    """
    turn_frac = turn / max(1, cfg.turns)
    scores: List[Tuple[float, int]] = []

    # MINE — always available.
    scores.append((g["mine"], MINE))

    # BUILD — needs ore.
    if me.ore >= cfg.build_cost:
        scores.append((g["build"], BUILD))

    # EXPAND — needs ore; weighted up in the late game if the genome says so.
    if me.ore >= cfg.expand_cost:
        s = g["expand"] * (1.0 + g["expand_late_bonus"] * turn_frac)
        scores.append((s, EXPAND))

    # FORTIFY — needs ore; weighted up when the opponent has a fleet.
    if me.ore >= cfg.fortify_cost:
        s = g["fortify"] * (1.0 + g["fortify_threat_scale"] * opp.ships)
        scores.append((s, FORTIFY))

    # RAID — needs a fleet at or above the threshold.
    if me.ships >= g["raid_threshold"] and me.ships >= 1:
        s = g["raid"] * me.ships
        scores.append((s, RAID))

    # argmax with stable tiebreak (lowest action code wins ties).
    best_score, best_action = scores[0]
    for s, a in scores[1:]:
        if s > best_score + 1e-12 or (abs(s - best_score) <= 1e-12 and a < best_action):
            best_score, best_action = s, a
    return best_action


def _apply_economy(side: _Side, action: int, cfg: GameConfig) -> None:
    if action == MINE:
        side.ore += cfg.mine_yield
    elif action == BUILD:
        side.ore -= cfg.build_cost
        side.ships += 1
    elif action == EXPAND:
        side.ore -= cfg.expand_cost
        side.bases += 1
    elif action == FORTIFY:
        side.ore -= cfg.fortify_cost
        side.shield += 1
    # RAID is resolved in the combat phase.


def _resolve_raid(attacker: _Side, defender: _Side) -> None:
    """Apply one raid. Uses post-economy snapshots taken by the caller.

    Net attacking ships (fleet minus the defender's standing shields) destroy one
    base each. Fleets and shields are persistent — the cost of raiding is the turn
    you didn't spend on economy, which keeps a credible offence in tension with
    a credible defence.
    """
    damage = max(0, attacker.ships - defender.shield)
    defender.bases = max(0, defender.bases - damage)


def play_game(a: Strategy, b: Strategy, cfg: GameConfig) -> Tuple[int, dict]:
    """Play one game. Returns (result, detail).

    result is +1 if `a` wins, -1 if `b` wins, 0 for a draw (from a's POV).
    """
    ga, gb = a.normalised(), b.normalised()
    A, B = _Side(cfg.start_ore), _Side(cfg.start_ore)

    for turn in range(cfg.turns):
        # Simultaneous decisions from the same snapshot.
        act_a = _choose_action(A, B, ga, turn, cfg)
        act_b = _choose_action(B, A, gb, turn, cfg)

        # Economy resolves first (so a same-turn FORTIFY can defend this turn).
        _apply_economy(A, act_a, cfg)
        _apply_economy(B, act_b, cfg)

        # Combat resolves from a frozen post-economy snapshot so both raids use
        # the same fleet/shield sizes (truly simultaneous). Net attacking ships
        # (fleet minus standing shields) destroy one base each; fleets and shields
        # persist — the cost of a raid is the economy turn you forfeited.
        a_ships, b_ships = A.ships, B.ships
        a_shield, b_shield = A.shield, B.shield
        if act_a == RAID:
            B.bases = max(0, B.bases - max(0, a_ships - b_shield))
        if act_b == RAID:
            A.bases = max(0, A.bases - max(0, b_ships - a_shield))

    # Scoring: territory first, salvage value as tiebreak.
    detail = {
        "a": {"ore": A.ore, "ships": A.ships, "bases": A.bases, "shield": A.shield},
        "b": {"ore": B.ore, "ships": B.ships, "bases": B.bases, "shield": B.shield},
    }
    if A.bases != B.bases:
        return (1 if A.bases > B.bases else -1), detail
    salv_a = A.ore + A.ships * 3 + A.shield
    salv_b = B.ore + B.ships * 3 + B.shield
    if salv_a != salv_b:
        return (1 if salv_a > salv_b else -1), detail
    return 0, detail


def play_match(a: Strategy, b: Strategy, pool: List[GameConfig]) -> Tuple[int, int, int]:
    """Play `a` vs `b` across a map pool, both sides of each map (to cancel any
    first-mover asymmetry). Returns (wins_a, draws, wins_b)."""
    wa = d = wb = 0
    for cfg in pool:
        for x, y, flip in ((a, b, 1), (b, a, -1)):
            r, _ = play_game(x, y, cfg)
            r *= flip  # re-orient to a's POV
            if r > 0:
                wa += 1
            elif r < 0:
                wb += 1
            else:
                d += 1
    return wa, d, wb
