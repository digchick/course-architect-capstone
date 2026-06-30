"""The calibrated league — the agent's reward signal.

Given a set of strategies and a map pool, we run a full round-robin (each pair on
every map, both sides) and convert the win matrix into Elo-style ratings with a
deterministic Bradley-Terry fit. No randomness, so the ratings are perfectly
reproducible — exactly what you want when an LLM is going to optimise against them.

`evaluate_candidate` is the function the agent's tools call: drop a new strategy in
with the anchors, return its rating and its win-rate versus the top anchor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .anchors import ANCHORS
from .sim import GameConfig, Strategy, play_match

# A small, fixed map pool. Varying turns / starting ore / mine yield stresses
# different economic tempos so a strategy can't overfit a single map.
DEFAULT_POOL: List[GameConfig] = [
    GameConfig(turns=40, start_ore=8, mine_yield=3),
    GameConfig(turns=50, start_ore=10, mine_yield=3),
    GameConfig(turns=60, start_ore=10, mine_yield=2),
    GameConfig(turns=50, start_ore=14, mine_yield=3),
    GameConfig(turns=70, start_ore=6, mine_yield=4),
]


@dataclass
class LeagueResult:
    names: List[str]
    elo: Dict[str, float]
    wins: Dict[str, int]
    games: Dict[str, int]
    winrate_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def table(self) -> str:
        rows = sorted(self.names, key=lambda n: -self.elo[n])
        out = ["  rank  strategy            elo     W     played  winrate",
               "  ----  ------------------  ------  ----  ------  -------"]
        for i, n in enumerate(rows, 1):
            wr = self.wins[n] / self.games[n] if self.games[n] else 0.0
            out.append(f"  {i:>4}  {n:<18}  {self.elo[n]:>6.0f}  "
                       f"{self.wins[n]:>4}  {self.games[n]:>6}  {wr:>6.1%}")
        return "\n".join(out)


def _bradley_terry_elo(names: List[str],
                       score: Dict[str, Dict[str, float]],
                       played: Dict[str, Dict[str, int]],
                       iters: int = 500) -> Dict[str, float]:
    """Fit Bradley-Terry strengths from a win matrix, return Elo-scaled ratings.

    `score[i][j]` = points i took off j (win=1, draw=0.5). Deterministic MM update.
    """
    strength = {n: 1.0 for n in names}
    for _ in range(iters):
        new = {}
        for i in names:
            wins_i = sum(score[i][j] for j in names if j != i)
            denom = 0.0
            for j in names:
                if j == i:
                    continue
                games_ij = played[i][j]
                if games_ij:
                    denom += games_ij / (strength[i] + strength[j])
            new[i] = wins_i / denom if denom > 0 else strength[i]
        # Normalise geometric mean to 1 to keep the fit from drifting.
        gm = math.exp(sum(math.log(max(v, 1e-9)) for v in new.values()) / len(new))
        strength = {n: new[n] / gm for n in names}
    # Map log-strength to Elo (400/ln10 per natural log unit), centred at 1000.
    scale = 400.0 / math.log(10.0)
    return {n: 1000.0 + scale * math.log(max(strength[n], 1e-9)) for n in names}


class League:
    """Run round-robins and evaluate candidates against the anchor ladder."""

    def __init__(self, anchors: List[Strategy] | None = None,
                 pool: List[GameConfig] | None = None):
        self.anchors = anchors if anchors is not None else list(ANCHORS)
        self.pool = pool if pool is not None else list(DEFAULT_POOL)

    def run(self, extra: List[Strategy] | None = None) -> LeagueResult:
        strategies = list(self.anchors) + list(extra or [])
        names = [s.name for s in strategies]
        score = {i: {j: 0.0 for j in names} for i in names}
        played = {i: {j: 0 for j in names} for i in names}
        wins = {n: 0 for n in names}
        games = {n: 0 for n in names}
        wr = {i: {} for i in names}

        for a in range(len(strategies)):
            for b in range(a + 1, len(strategies)):
                sa, sb = strategies[a], strategies[b]
                wa, dr, wb = play_match(sa, sb, self.pool)
                n_games = wa + dr + wb
                # accumulate symmetric stats
                score[sa.name][sb.name] += wa + 0.5 * dr
                score[sb.name][sa.name] += wb + 0.5 * dr
                played[sa.name][sb.name] += n_games
                played[sb.name][sa.name] += n_games
                wins[sa.name] += wa
                wins[sb.name] += wb
                games[sa.name] += n_games
                games[sb.name] += n_games
                wr[sa.name][sb.name] = wa / n_games if n_games else 0.0
                wr[sb.name][sa.name] = wb / n_games if n_games else 0.0

        elo = _bradley_terry_elo(names, score, played)
        return LeagueResult(names=names, elo=elo, wins=wins, games=games,
                            winrate_matrix=wr)

    def top_anchor(self) -> Strategy:
        """Highest-rated anchor in an anchors-only league (the ceiling to beat)."""
        res = self.run()
        best = max(self.anchors, key=lambda s: res.elo[s.name])
        return best

    def evaluate_candidate(self, candidate: Strategy) -> Dict:
        """Score one candidate against the anchor ladder. This is the core signal
        the agent optimises. Returns elo, rank, and win-rate vs the top anchor."""
        res = self.run(extra=[candidate])
        ranked = sorted(res.names, key=lambda n: -res.elo[n])
        rank = ranked.index(candidate.name) + 1
        top = max(self.anchors, key=lambda s: res.elo[s.name]).name
        return {
            "name": candidate.name,
            "elo": round(res.elo[candidate.name], 1),
            "rank": rank,
            "field_size": len(res.names),
            "top_anchor": top,
            "top_anchor_elo": round(res.elo[top], 1),
            "winrate_vs_top": round(res.winrate_matrix[candidate.name].get(top, 0.0), 3),
            "beats_top_anchor": res.elo[candidate.name] > res.elo[top],
            "winrate_overall": round(res.wins[candidate.name] / res.games[candidate.name], 3)
            if res.games[candidate.name] else 0.0,
        }


if __name__ == "__main__":
    # Calibration check: anchors-only league should produce a sensible ladder.
    league = League()
    result = league.run()
    print("Anchor-only calibrated league:\n")
    print(result.table())
    print(f"\nTop anchor (ceiling to beat): {league.top_anchor().name}")
