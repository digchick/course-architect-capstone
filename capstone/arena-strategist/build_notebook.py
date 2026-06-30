"""Generate capstone_notebook.ipynb from the *tested* source files.

Rather than hand-maintain a notebook (which drifts from the code), we assemble it
from the real modules: each module becomes a readable `%%writefile` cell, so the
submitted notebook is self-contained AND identical to what we verified locally.
Run:  python build_notebook.py
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def read(path: str) -> str:
    with open(os.path.join(HERE, path), "r", encoding="utf-8") as f:
        return f.read()


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _lines(text)}


def writefile(path: str) -> dict:
    return code(f"%%writefile {path}\n" + read(path))


def _lines(text: str):
    # nbformat wants a list of strings, each (except the last) ending in \n.
    parts = text.splitlines(keepends=True)
    return parts if parts else [""]


INTRO = """# Arena Strategist — a vibe-coded, self-improving game-strategy agent

**5-Day AI Agents Intensive (Vibe Coding) — Capstone**

This notebook builds an **autonomous agent that discovers winning strategies for a
competitive 2-player simulation by optimising against a *calibrated league***. It is
the LLM-agent realisation of the eval-driven method that earned our team **silver
(top 5% of 4,689 teams)** in the *Orbit Wars* Kaggle simulation competition: a
*trustworthy evaluator in the inner loop, a memory of dead ends on the outside*.

Two LLM roles — a **Proposer** and a **Critic** (Gemini) — reason in natural language
about game strategy and emit structured "genomes". The agent scores each genome
through an **MCP-style tool surface**, remembers what worked and what didn't, and
self-corrects until it beats the strongest hand-built anchor.

### What it demonstrates (one per course day)
| Day | Concept | Where in this notebook |
|----|----|----|
| 1 | Vibe coding — natural language drives the build | Proposer/Critic system prompts in `agent/provider.py` |
| 2 | Tools & interoperability (MCP) | `agent/tools.py` — `list_tools()` / `call_tool()` |
| 3 | Context engineering: skills & memory | `agent/skills/*.md`, `agent/memory.py` (attempts + falsifications) |
| 4 | Agent quality & evaluation | `arena/league.py` — the calibrated Elo league IS the reward |
| 5 | Prototype → production | reproducible run, observable tool log, graceful degradation |

> **Runs with or without a key.** With a Gemini key (add a Kaggle Secret named
> `GOOGLE_API_KEY`) the Proposer/Critic are real LLM calls. Without one, a
> deterministic `Mock` strategist (guided hill-climb) runs instead, so this notebook
> executes top-to-bottom for the grader either way — the same fallback pattern the
> official course starter kernel uses.
"""

SETUP_MD = """## 1. Write out the project
Each module is written to disk from its own cell, so the code below is exactly what
runs — and exactly what was verified locally. (Pure Python; no heavy dependencies.)"""

ENABLE_GEMINI = """## 2. (Optional) Enable the real Gemini strategist
Skip this to run on the deterministic Mock. To use Gemini:
1. Add your AI Studio key as a Kaggle **Secret** named `GOOGLE_API_KEY`
   (Add-ons → Secrets), then enable it for this notebook; **or**
2. set the environment variable in-notebook (less secure):

```python
import os; os.environ["GOOGLE_API_KEY"] = "..."   # and: pip install google-generativeai
```
The model defaults to `gemini-2.0-flash`; override with `GEMINI_MODEL`."""

RUN1_MD = """## 3. Calibrate the league (the trustworthy evaluator)
Before judging any new strategy, confirm the league reproduces a sensible ordering
of the **anchors** — naive at the bottom, the sophisticated `adaptive` anchor on top.
This calibration step is the whole reason the eval can be trusted; it's the single
biggest lesson we carried over from Orbit Wars."""

RUN1_CODE = """from arena import League, Strategy
league = League()
print(league.run().table())
print("\\nCeiling to beat:", league.top_anchor().name)"""

RUN2_MD = """## 4. The agent climbs the ladder
Each round: **Proposer** suggests a genome → the **`evaluate_strategy` tool** scores
it on the league → the **Critic** says keep / mutate / discard → everything goes to
**memory**, and dead ends become **falsifications** the Proposer won't revisit."""

RUN2_CODE = """from agent import ArenaStrategist, get_provider

provider = get_provider()          # Gemini if a key is present, else Mock
agent = ArenaStrategist(provider=provider, league=league, memory_path="arena_memory.json")
report = agent.run(budget=24)"""

RUN3_MD = """## 5. Verify the champion & visualise the climb
Drop the discovered champion back into a fresh league to confirm it really tops the
ladder, then plot Elo per round."""

RUN3_CODE = """import matplotlib.pyplot as plt

champ = Strategy(name="champion", genome=report.best_genome, note="discovered by the agent")
print(league.run(extra=[champ]).table())
print("\\nChampion genome:", report.best_genome)
print(report.headline())

elos = [t["elo"] for t in report.trace]
rounds = [t["round"] for t in report.trace]
plt.figure(figsize=(9, 4))
plt.plot(rounds, elos, marker="o", label="proposed genome")
plt.axhline(report.top_anchor_elo, ls="--", color="crimson",
            label=f"ceiling ({report.top_anchor} {report.top_anchor_elo:.0f})")
best = report.top_anchor_elo
run_best = []
for e in elos:
    best = max(best if run_best else e, e) if not run_best else max(run_best[-1], e)
    run_best.append(best)
plt.plot(rounds, run_best, color="green", lw=2, label="best so far")
plt.xlabel("round"); plt.ylabel("Elo"); plt.title("Arena Strategist — climb vs the ceiling")
plt.legend(); plt.tight_layout(); plt.show()

print("\\n" + agent.memory.summary())
for f in agent.memory.falsifications:
    print("  falsified:", f)"""

TOOLS_MD = """## 6. The MCP tool surface (inspect)
The agent only ever touches the simulator through these schema-typed tools — the
same shape as a real Model Context Protocol server (`tools/list` + `tools/call`)."""

TOOLS_CODE = """import json
from agent import ArenaToolServer
ts = ArenaToolServer(league)
print(json.dumps(ts.list_tools(), indent=2)[:1400], "...")
print("\\nExample call -> simulate_match vs the top anchor:")
print(ts.call_tool("simulate_match", {"genome": report.best_genome, "opponent": report.top_anchor}))"""

WRITEUP = """## 7. How it works — architecture & design notes

```
        +------------------ ArenaStrategist (orchestrator loop) ------------------+
        |                                                                         |
  skill + memory ---> [ Proposer ] --genome--> [ evaluate_strategy TOOL ] --eval--+
   (context)              (Gemini)                  (calibrated league)            |
        ^                                                                         v
        |                                                       [ Critic ] keep/mutate/discard
        +----------------------- memory (attempts + falsifications) <-------------+
```

**Why a calibrated league is the heart of it.** An LLM will happily invent
plausible-sounding strategies; most are wrong. The only way to know is an evaluator
you trust. We first calibrate the league against hand-built anchors of known
relative strength — if it can't reproduce *their* ordering, it can't be trusted on
novel strategies. Only then do we let the agent optimise against it. This is exactly
how we avoided fooling ourselves in Orbit Wars, where a *miscalibrated* local eval
had previously sent the search chasing mirages.

**Why strategies are genomes, not code.** Representing a strategy as 8 numbers (not
free-form code) makes proposals safe to execute, trivial to store/diff/mutate, and
easy for an LLM to emit as strict JSON — no sandbox required. (The course starter
kernel *does* show the code-generation-plus-sandbox pattern; we note it as the
natural Day-4 security extension if strategies were arbitrary code.)

**Memory & falsification.** Every attempt is persisted; genuinely bad lines become
short "falsification" notes fed back into the Proposer's context. Writing down what
*doesn't* work is the cheapest way to stop an agent (or a human) re-exploring dead
ends — the highest-leverage habit from our competition work.

**Graceful degradation (production thinking).** Missing key → Mock. Unparseable LLM
output → coerced/fallback genome. The loop never stalls; the notebook always runs.

### Connection to Orbit Wars
Orbit Wars is our $50k Kaggle simulation result (silver, top 5% of 4,689). It is a
pure reinforcement-learning / search agent — no LLM. This capstone is **not** that
agent; it is the *methodology* from it, re-cast as a vibe-coded LLM agent on a
self-contained arena: calibrate a trustworthy league, then search against it with a
memory of dead ends. (Orbit Wars' live submission is locked and untouched here.)

### Limitations & next steps
- The arena is deliberately compact; the policy is argmax over weighted actions, so
  the genome→Elo surface is piecewise-constant (many genomes tie). A richer policy
  (state-conditioned, or LLM-authored code in a sandbox) would deepen the search.
- The league is single-threaded; Day-5 production would parallelise matches and add
  tracing/metrics export.
- Self-play co-evolution (promote champions into the anchor set, then re-climb) is
  the natural extension — exactly the AlphaZero-lite direction we explored in Orbit Wars.

*Built for the Google × Kaggle 5-Day AI Agents Intensive (Vibe Coding) capstone.*"""


def build() -> dict:
    cells = [
        md(INTRO),
        md(SETUP_MD),
        code("import os\n"
             "for d in ('arena', 'agent', 'agent/skills'):\n"
             "    os.makedirs(d, exist_ok=True)\n"
             "print('dirs ready')"),
        writefile("arena/__init__.py"),
        writefile("arena/sim.py"),
        writefile("arena/anchors.py"),
        writefile("arena/league.py"),
        writefile("agent/__init__.py"),
        writefile("agent/provider.py"),
        writefile("agent/memory.py"),
        writefile("agent/tools.py"),
        writefile("agent/skills/strategy_heuristics.md"),
        writefile("agent/strategist.py"),
        md(ENABLE_GEMINI),
        md(RUN1_MD), code(RUN1_CODE),
        md(RUN2_MD), code(RUN2_CODE),
        md(RUN3_MD), code(RUN3_CODE),
        md(TOOLS_MD), code(TOOLS_CODE),
        md(WRITEUP),
    ]
    for i, cell in enumerate(cells):
        cell["id"] = f"cell{i:02d}"  # nbformat >=4.5 requires unique cell ids
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


if __name__ == "__main__":
    nb = build()
    out = os.path.join(HERE, "capstone_notebook.ipynb")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"wrote {out} ({len(nb['cells'])} cells)")
