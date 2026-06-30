"""LLM provider abstraction: a Gemini-backed strategist with a Mock fallback.

The whole point of *vibe coding* is that natural language drives the work — here,
two LLM "roles" (a Proposer and a Critic) reason about game strategy in words and
emit structured genomes. But a capstone notebook has to *run for the grader even
without secrets*, so we ship a deterministic `MockProvider` that performs guided
hill-climbing. The official course starter kernel uses exactly this pattern (a
`MockLLMContext`) so the notebook executes top-to-bottom with or without a key.

Set a key (`GOOGLE_API_KEY` / `GEMINI_API_KEY`, or a Kaggle Secret of the same
name) and `get_provider()` returns the real `GeminiProvider`; otherwise you get
the `MockProvider` and an explanatory log line.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from arena.sim import DEFAULT_GENOME, GENOME_KEYS, Strategy


# --------------------------------------------------------------------------- #
# Shared context + result types
# --------------------------------------------------------------------------- #

@dataclass
class ProposalContext:
    """Everything a role needs to reason about the next move."""

    top_anchor: str
    top_anchor_elo: float
    anchor_summary: List[Dict]               # [{name, elo, note}]
    skill_text: str                          # the strategy-heuristics skill file
    best_genome: Optional[Dict] = None       # best genome found so far
    best_elo: Optional[float] = None
    history: List[Dict] = field(default_factory=list)   # recent {genome, elo, beats_top}
    falsifications: List[str] = field(default_factory=list)  # what didn't work
    round_index: int = 0
    budget: int = 1


@dataclass
class Proposal:
    genome: Dict[str, float]
    rationale: str
    source: str  # "gemini" | "mock"


@dataclass
class Critique:
    verdict: str            # "keep" | "mutate" | "discard"
    reasoning: str
    suggested_changes: Dict[str, float] = field(default_factory=dict)


def _coerce_genome(raw: Dict) -> Dict[str, float]:
    """Make any dict into a valid genome (fill missing keys, drop unknowns)."""
    g = dict(DEFAULT_GENOME)
    for k in GENOME_KEYS:
        if k in raw:
            try:
                g[k] = float(raw[k])
            except (TypeError, ValueError):
                pass
    g["raid_threshold"] = int(round(g["raid_threshold"]))
    # Round the continuous knobs for clean storage/display (ample resolution).
    for k in GENOME_KEYS:
        if k != "raid_threshold":
            g[k] = round(g[k], 3)
    return g


# --------------------------------------------------------------------------- #
# Base class
# --------------------------------------------------------------------------- #

class StrategyProvider:
    name = "base"

    def propose(self, ctx: ProposalContext) -> Proposal:
        raise NotImplementedError

    def critique(self, candidate: Strategy, eval_result: Dict,
                 ctx: ProposalContext) -> Critique:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Mock provider — deterministic guided hill-climber (no API key required)
# --------------------------------------------------------------------------- #

class MockProvider(StrategyProvider):
    """A real optimiser standing in for the LLM. Hill-climbs the genome around the
    best-known strategy, with periodic exploratory restarts to escape local
    optima. Deterministic given the round index, so runs are reproducible."""

    name = "mock"

    # A sensible economy-leaning seed so we start above mediocrity.
    _SEED = {"mine": 1.8, "build": 1.6, "expand": 2.2, "fortify": 1.3,
             "raid": 1.6, "raid_threshold": 3, "expand_late_bonus": 1.0,
             "fortify_threat_scale": 0.6}

    _STEP = {"mine": 0.5, "build": 0.5, "expand": 0.5, "fortify": 0.5,
             "raid": 0.5, "raid_threshold": 1, "expand_late_bonus": 0.4,
             "fortify_threat_scale": 0.3}

    def propose(self, ctx: ProposalContext) -> Proposal:
        rng = random.Random(1000 + ctx.round_index)
        base = dict(ctx.best_genome) if ctx.best_genome else dict(self._SEED)

        if ctx.best_genome is None:
            return Proposal(genome=_coerce_genome(base),
                            rationale="Seed: economy-first with late expansion and "
                                      "a reactive defence — a balanced opening to climb from.",
                            source=self.name)

        # Every 5th round, take a bigger exploratory jump (anneal the temperature).
        explore = (ctx.round_index % 5 == 0)
        temp = 1.6 if explore else 0.6 * (1.0 - 0.5 * ctx.round_index / max(1, ctx.budget))
        knobs = rng.sample(list(GENOME_KEYS), k=3 if explore else 2)

        g = dict(base)
        changed = {}
        for k in knobs:
            delta = rng.choice([-1.0, 1.0]) * self._STEP[k] * temp * rng.uniform(0.6, 1.5)
            if k == "raid_threshold":
                delta = rng.choice([-1, 1])
            g[k] = g[k] + delta
            changed[k] = round(g[k] - base[k], 2)

        verb = "Exploratory jump" if explore else "Hill-climb"
        nudges = ", ".join(f"{k} {'+' if v >= 0 else ''}{v}" for k, v in changed.items())
        rationale = (f"{verb} from best (elo {ctx.best_elo:.0f}): nudging {nudges} "
                     f"to push win-rate vs {ctx.top_anchor}.")
        return Proposal(genome=_coerce_genome(g), rationale=rationale, source=self.name)

    def critique(self, candidate: Strategy, eval_result: Dict,
                 ctx: ProposalContext) -> Critique:
        improved = (ctx.best_elo is None) or (eval_result["elo"] > ctx.best_elo)
        if eval_result["beats_top_anchor"] and improved:
            return Critique("keep",
                            f"New best: elo {eval_result['elo']} beats {ctx.top_anchor} "
                            f"(win-rate {eval_result['winrate_vs_top']:.0%}). Adopt as base.")
        if improved:
            return Critique("keep",
                            f"Improves elo to {eval_result['elo']} but doesn't yet clear "
                            f"{ctx.top_anchor}. Keep as the new climbing base.")
        # Clearly weak (low absolute win-rate, or far below our best) — discard and
        # let the orchestrator record a falsification so we never re-explore it.
        far_below = ctx.best_elo is not None and eval_result["elo"] < ctx.best_elo - 200
        if eval_result["winrate_overall"] < 0.30 or far_below:
            return Critique("discard",
                            f"elo {eval_result['elo']} ({eval_result['winrate_overall']:.0%} "
                            f"overall win-rate); well below the best line, a dead end.")
        # Otherwise mutate: diagnose a direction from the eval signal.
        changes: Dict[str, float] = {}
        if eval_result["winrate_vs_top"] < 0.5:
            changes["fortify"] = +0.5      # losing to the ceiling -> shore up defence
            changes["raid"] = +0.5         # ...and add bite
        return Critique("mutate",
                        f"elo {eval_result['elo']} below best {ctx.best_elo:.0f}; "
                        f"mutate from the current best instead.",
                        suggested_changes=changes)


# --------------------------------------------------------------------------- #
# Gemini provider — real LLM-driven Proposer / Critic
# --------------------------------------------------------------------------- #

_PROPOSER_SYSTEM = """You are the Proposer in a two-agent strategy-discovery loop \
for a competitive 2-player game called Orbital Skirmish.

Each turn a player picks ONE action by the highest weighted score:
- MINE (+3 ore), BUILD (-3 ore, +1 ship), EXPAND (-5 ore, +1 base = victory points),
  FORTIFY (-2 ore, +1 standing shield), RAID (net ships above the enemy's shield
  each destroy one of their bases). Fleets and shields persist.

A STRATEGY is an 8-number genome controlling that policy:
  mine, build, expand, fortify, raid (priorities >=0),
  raid_threshold (min ships before raiding, integer 1-20),
  expand_late_bonus (expand priority grows toward the endgame, 0-5),
  fortify_threat_scale (fortify priority grows with enemy fleet size, 0-2).

Your job: propose the next genome to TEST so it climbs an Elo league of anchor
strategies and beats the top anchor. Reason briefly, then OUTPUT STRICT JSON:
{"genome": {"mine":..,"build":..,"expand":..,"fortify":..,"raid":..,
"raid_threshold":..,"expand_late_bonus":..,"fortify_threat_scale":..},
"rationale":"one sentence"}"""

_CRITIC_SYSTEM = """You are the Critic in a two-agent strategy-discovery loop. \
Given a candidate genome and its league evaluation, decide whether to keep it as \
the new climbing base, mutate from the current best, or discard it. Consider its \
Elo, whether it beats the top anchor, and its win-rate versus the top anchor.
OUTPUT STRICT JSON: {"verdict":"keep|mutate|discard","reasoning":"one sentence",
"suggested_changes":{"<knob>": <signed delta>, ...}}"""


class GeminiProvider(StrategyProvider):
    """Calls Gemini for the Proposer and Critic roles. Falls back to a coerced
    genome if the model returns unparseable output, so the loop never stalls."""

    name = "gemini"

    def __init__(self, api_key: str, model: Optional[str] = None):
        import google.generativeai as genai  # lazy: only needed on this path
        self._genai = genai
        genai.configure(api_key=api_key)
        self.model_name = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self._proposer = genai.GenerativeModel(self.model_name,
                                               system_instruction=_PROPOSER_SYSTEM)
        self._critic = genai.GenerativeModel(self.model_name,
                                             system_instruction=_CRITIC_SYSTEM)
        self._mock = MockProvider()  # safety net for parse failures

    def _json_call(self, model, prompt: str) -> Optional[Dict]:
        try:
            resp = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json",
                                   "temperature": 0.9, "max_output_tokens": 512},
            )
            return json.loads(resp.text)
        except Exception as exc:  # parse error, rate limit, etc. — degrade gracefully
            print(f"    [gemini] call failed ({type(exc).__name__}); using fallback")
            return None

    def _render_context(self, ctx: ProposalContext) -> str:
        anchors = "\n".join(f"  - {a['name']}: elo {a['elo']:.0f} — {a['note']}"
                            for a in ctx.anchor_summary)
        hist = "\n".join(
            f"  - elo {h['elo']:.0f} {'(beat ceiling)' if h['beats_top'] else ''}: "
            f"{json.dumps({k: round(v, 2) for k, v in h['genome'].items()})}"
            for h in ctx.history[-6:]) or "  (none yet)"
        false = "\n".join(f"  - {f}" for f in ctx.falsifications[-6:]) or "  (none yet)"
        best = (json.dumps({k: round(v, 2) for k, v in ctx.best_genome.items()})
                if ctx.best_genome else "none")
        return (f"SKILL — strategy heuristics:\n{ctx.skill_text}\n\n"
                f"ANCHOR LADDER (beat the top one, '{ctx.top_anchor}' at "
                f"elo {ctx.top_anchor_elo:.0f}):\n{anchors}\n\n"
                f"BEST SO FAR: elo {ctx.best_elo} genome {best}\n\n"
                f"RECENT ATTEMPTS:\n{hist}\n\n"
                f"FALSIFIED (don't repeat):\n{false}\n\n"
                f"Round {ctx.round_index + 1} of {ctx.budget}.")

    def propose(self, ctx: ProposalContext) -> Proposal:
        prompt = self._render_context(ctx) + "\n\nPropose the next genome to test."
        data = self._json_call(self._proposer, prompt)
        if not data or "genome" not in data:
            return self._mock.propose(ctx)
        return Proposal(genome=_coerce_genome(data["genome"]),
                        rationale=str(data.get("rationale", ""))[:240],
                        source=self.name)

    def critique(self, candidate: Strategy, eval_result: Dict,
                 ctx: ProposalContext) -> Critique:
        prompt = (self._render_context(ctx) +
                  f"\n\nCANDIDATE genome: "
                  f"{json.dumps({k: round(v, 2) for k, v in candidate.normalised().items()})}"
                  f"\nEVALUATION: {json.dumps(eval_result)}\n\nCritique it.")
        data = self._json_call(self._critic, prompt)
        if not data or "verdict" not in data:
            return self._mock.critique(candidate, eval_result, ctx)
        verdict = str(data.get("verdict", "mutate")).lower()
        if verdict not in ("keep", "mutate", "discard"):
            verdict = "mutate"
        changes = {}
        for k, v in (data.get("suggested_changes") or {}).items():
            if k in GENOME_KEYS:
                try:
                    changes[k] = float(v)
                except (TypeError, ValueError):
                    pass
        return Critique(verdict, str(data.get("reasoning", ""))[:240], changes)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

def _find_api_key() -> Optional[str]:
    for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(var):
            return os.environ[var]
    # Kaggle Secrets, if running in a Kaggle notebook.
    try:
        from kaggle_secrets import UserSecretsClient  # type: ignore
        client = UserSecretsClient()
        for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            try:
                val = client.get_secret(var)
                if val:
                    return val
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_provider(force_mock: bool = False) -> StrategyProvider:
    """Return a GeminiProvider if a key + SDK are available, else a MockProvider."""
    if force_mock:
        print("[provider] forced Mock strategist (deterministic, no API).")
        return MockProvider()
    key = _find_api_key()
    if not key:
        print("[provider] no GOOGLE_API_KEY/GEMINI_API_KEY found → Mock strategist "
              "(deterministic hill-climber). Add a key to enable Gemini.")
        return MockProvider()
    try:
        import google.generativeai  # noqa: F401
    except Exception:
        print("[provider] google-generativeai not installed → Mock strategist. "
              "`pip install google-generativeai` to enable Gemini.")
        return MockProvider()
    prov = GeminiProvider(api_key=key)
    print(f"[provider] Gemini strategist active (model: {prov.model_name}).")
    return prov
