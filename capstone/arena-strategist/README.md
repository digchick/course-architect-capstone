# Arena Strategist

**A vibe-coded, self-improving game-strategy agent — capstone for the Google × Kaggle 5-Day AI Agents Intensive (Vibe Coding).**

An autonomous agent that **discovers winning strategies for a competitive 2-player
simulation by optimising against a calibrated league**. Two Gemini "roles" — a
**Proposer** and a **Critic** — reason in natural language about game strategy and
emit structured strategy "genomes"; the agent scores each one through an MCP-style
tool surface, remembers what worked and what didn't, and self-corrects until it
beats the strongest hand-built opponent.

It is the LLM-agent realisation of the eval-driven method that earned our team
**silver (top 5% of 4,689 teams) in the *Orbit Wars* Kaggle simulation competition**:
*a trustworthy evaluator in the inner loop, a memory of dead ends on the outside.*

---

## Why it's interesting
Most LLM "strategy" demos never check whether the strategy is actually any good.
This one is built around an **objective, calibrated reward**: a deterministic Elo
league that is first validated against anchors of known relative strength, and only
then trusted to judge novel strategies the LLM invents. That calibration step — not
the LLM — is what makes the result real.

## Course concepts demonstrated (one per day)
| Day | Concept | Where |
|----|----|----|
| 1 | Vibe coding (NL drives the build) | Proposer/Critic system prompts, `agent/provider.py` |
| 2 | Tools & interoperability (MCP) | `agent/tools.py` — `list_tools()` / `call_tool()` |
| 3 | Context engineering: skills & memory | `agent/skills/strategy_heuristics.md`, `agent/memory.py` |
| 4 | Agent quality & evaluation | `arena/league.py` — the calibrated Elo league *is* the reward |
| 5 | Prototype → production | reproducible runs, observable tool log, graceful degradation |

## Architecture
```
        +------------------ ArenaStrategist (orchestrator loop) ------------------+
        |                                                                         |
  skill + memory ---> [ Proposer ] --genome--> [ evaluate_strategy TOOL ] --eval--+
   (context)            (Gemini/Mock)              (calibrated league)             |
        ^                                                                         v
        |                                                  [ Critic ] keep / mutate / discard
        +----------------------- memory (attempts + falsifications) <-------------+
```

## The game — Orbital Skirmish
A compact, fully deterministic 2-player game. Each turn a player picks one action:
**MINE** (+3 ore), **BUILD** (−3 ore, +1 ship), **EXPAND** (−5 ore, +1 base = points),
**FORTIFY** (−2 ore, +1 standing shield), **RAID** (net ships above the enemy's
shields each destroy a base). Economy ↔ military ↔ territory ↔ defence form a
rock-paper-scissors loop, so no pure strategy dominates and a real skill ladder
emerges. A strategy is an 8-number **genome** parameterising a legible policy —
safe to execute, easy to store/mutate, and easy for an LLM to emit as JSON.

## Results (deterministic Mock run, no API key)
```
Calibrated anchors:  adaptive 1223 > greedy_expander/balanced 1098 > turtle 931
                     > all_in_raider 873 > naive_miner 777
Agent champion:      elo 1308  (rank 1/7, 86.7% win-rate) — BEATS the ceiling
```
With a Gemini key the Proposer/Critic become real LLM calls; the harness is identical.

## Run it
```bash
# Core arena + agent are pure-Python stdlib. The notebook plot needs matplotlib.
python run_demo.py            # auto: Gemini if a key is set, else deterministic Mock
python run_demo.py --mock     # force the deterministic Mock
python -m arena.league        # just print the calibrated anchor ladder
```
**Enable Gemini:** set `GOOGLE_API_KEY` (or `GEMINI_API_KEY`), `pip install google-generativeai`.
Optionally set `GEMINI_MODEL` (default `gemini-2.0-flash`).

**Kaggle:** `capstone_notebook.ipynb` is self-contained — it writes every module from
`%%writefile` cells, so it runs top-to-bottom on a stock kernel. Add a Kaggle Secret
named `GOOGLE_API_KEY` to switch the Mock for Gemini. Rebuild it from source with
`python build_notebook.py`.

## Files
```
arena/         sim.py (engine) · anchors.py (calibrated ladder) · league.py (Elo eval)
agent/         provider.py (Gemini+Mock) · tools.py (MCP) · memory.py · strategist.py
               skills/strategy_heuristics.md
run_demo.py    end-to-end demo            build_notebook.py  notebook generator
capstone_notebook.ipynb   the Kaggle submission        VIDEO_SCRIPT.md
```

## Connection to Orbit Wars — and what this is *not*
Orbit Wars is our $50k Kaggle result (silver). It is a pure RL/search agent, **no
LLM**. This capstone is *not* that agent — it is the **methodology** from it, recast
as a vibe-coded LLM agent on a self-contained arena. Orbit Wars' live submission is
locked and is never touched by this project.

## Limitations & next steps
- Argmax policy ⇒ the genome→Elo surface is piecewise-constant (many genomes tie);
  a state-conditioned or LLM-authored-code policy (in a sandbox) would deepen search.
- Single-threaded league; production would parallelise matches and export traces/metrics.
- Self-play co-evolution — promote champions into the anchor set and re-climb — is the
  natural extension (the AlphaZero-lite direction we explored in Orbit Wars).

*MIT-spirit sandbox built for the course capstone.*
