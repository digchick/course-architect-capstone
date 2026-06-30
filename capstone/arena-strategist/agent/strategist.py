"""The orchestrator: a self-correcting Proposer → Eval → Critic loop.

This is the agent proper. Each round:

  1. **Proposer** (LLM or Mock) reads the skill, the anchor ladder, the best genome
     so far, recent attempts and the falsification log, and proposes a new genome.
  2. The orchestrator calls the **`evaluate_strategy` tool** (the MCP surface) to
     score it on the calibrated league — the objective reward signal.
  3. **Critic** (LLM or Mock) reads the evaluation and returns keep / mutate /
     discard, optionally suggesting knob changes — the self-correction step.
  4. Everything is written to **memory**; new dead ends become **falsifications**.

It is deliberately the same control loop as the Orbit Wars search that earned us
silver: a trustworthy eval in the inner loop, memory of what failed on the outside.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from arena.league import League
from arena.sim import Strategy

from .memory import Attempt, StrategyMemory
from .provider import ProposalContext, StrategyProvider, get_provider
from .tools import ArenaToolServer

_SKILL_PATH = os.path.join(os.path.dirname(__file__), "skills", "strategy_heuristics.md")


def _load_skill() -> str:
    try:
        with open(_SKILL_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return "(skill file unavailable)"


@dataclass
class RunReport:
    rounds: int
    best_name: str
    best_genome: Dict[str, float]
    best_elo: float
    top_anchor: str
    top_anchor_elo: float
    beat_ceiling: bool
    tool_calls: int
    provider: str
    trace: List[Dict] = field(default_factory=list)

    def headline(self) -> str:
        verb = "BEAT" if self.beat_ceiling else "did not beat"
        return (f"{self.provider} strategist {verb} the ceiling: best elo "
                f"{self.best_elo:.0f} vs {self.top_anchor} {self.top_anchor_elo:.0f} "
                f"after {self.rounds} rounds ({self.tool_calls} tool calls).")


class ArenaStrategist:
    def __init__(self, provider: Optional[StrategyProvider] = None,
                 league: Optional[League] = None,
                 memory_path: Optional[str] = None,
                 verbose: bool = True):
        self.league = league or League()
        self.tools = ArenaToolServer(self.league)
        self.provider = provider or get_provider()
        self.memory = StrategyMemory(memory_path)
        self.skill = _load_skill()
        self.verbose = verbose
        # Pin the ceiling once (anchors-only league) so the target is fixed.
        anchors = self.tools.anchor_summary()
        self.top = anchors[0]
        self.anchor_summary = anchors

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def _context(self, round_index: int, budget: int) -> ProposalContext:
        return ProposalContext(
            top_anchor=self.top["name"],
            top_anchor_elo=self.top["elo"],
            anchor_summary=self.anchor_summary,
            skill_text=self.skill,
            best_genome=self.memory.best_genome(),
            best_elo=self.memory.best_elo(),
            history=self.memory.recent(6),
            falsifications=list(self.memory.falsifications),
            round_index=round_index,
            budget=budget,
        )

    def run(self, budget: int = 20) -> RunReport:
        self._log(f"Arena Strategist - provider={self.provider.name}, "
                  f"ceiling={self.top['name']} (elo {self.top['elo']:.0f}), budget={budget}\n")
        trace: List[Dict] = []

        for r in range(budget):
            ctx = self._context(r, budget)

            # 1. Proposer
            proposal = self.provider.propose(ctx)
            cand = Strategy(name=f"gen{r:02d}", genome=proposal.genome, note=proposal.rationale)

            # Skip exact repeats — don't spend eval budget twice on a known point.
            if self.memory.already_tried(cand.normalised()):
                self._log(f"[r{r:02d}] repeat genome skipped")
                continue

            # 2. Evaluate via the MCP tool surface (the reward signal)
            ev = self.tools.call_tool("evaluate_strategy",
                                      {"genome": cand.normalised(), "name": cand.name})

            # 3. Critic (self-correction)
            crit = self.provider.critique(cand, ev, ctx)

            # 4. Memory
            self.memory.record(Attempt(
                round_index=r, name=cand.name, genome=cand.normalised(),
                elo=ev["elo"], rank=ev["rank"], beats_top_anchor=ev["beats_top_anchor"],
                winrate_vs_top=ev["winrate_vs_top"], rationale=proposal.rationale,
                source=proposal.source, verdict=crit.verdict))
            if crit.verdict == "discard":
                self.memory.add_falsification(
                    f"{proposal.rationale[:70]} -> elo {ev['elo']:.0f} (weak); abandoned.")

            flag = "* NEW BEST" if self.memory.best.round_index == r else ""
            beat = "BEATS ceiling" if ev["beats_top_anchor"] else ""
            self._log(f"[r{r:02d}] {proposal.source:<6} elo {ev['elo']:>6.0f} "
                      f"rank {ev['rank']}/{ev['field_size']} "
                      f"wr_vs_{self.top['name']} {ev['winrate_vs_top']:>4.0%} "
                      f"-> {crit.verdict:<7} {beat} {flag}")
            trace.append({"round": r, "source": proposal.source, "elo": ev["elo"],
                          "rank": ev["rank"], "beats_top": ev["beats_top_anchor"],
                          "verdict": crit.verdict, "rationale": proposal.rationale})

        best = self.memory.best
        report = RunReport(
            rounds=len(trace),
            best_name=best.name, best_genome=best.genome, best_elo=best.elo,
            top_anchor=self.top["name"], top_anchor_elo=self.top["elo"],
            beat_ceiling=best.elo > self.top["elo"],
            tool_calls=len(self.tools.call_log), provider=self.provider.name, trace=trace)
        self._log("\n" + report.headline())
        return report
