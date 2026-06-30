"""Generate capstone_notebook.ipynb for Course Architect from the tested source.

Each module becomes a readable `%%writefile` cell, so the submitted notebook is
self-contained and identical to what was verified locally.  Run: python build_notebook.py
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def read(path: str) -> str:
    with open(os.path.join(HERE, path), "r", encoding="utf-8") as f:
        return f.read()


def _lines(text: str):
    parts = text.splitlines(keepends=True)
    return parts if parts else [""]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _lines(text)}


def writefile(path: str) -> dict:
    return code(f"%%writefile {path}\n" + read(path))


INTRO = """# Course Architect — an agent that turns an outline into a finished PowerPoint course

**5-Day AI Agents Intensive (Vibe Coding) — Capstone · Track: Agents for Business**

Building courseware is slow: someone turns a rough outline into dozens of well-structured,
on-brand slides with speaker notes. **Course Architect** is an AI agent that does it — you
give it a short outline (a title, an audience, a few modules with bullet points) — or even
just a topic, and it designs the outline itself — then it plans the course, writes every
slide and speaker note, assembles a branded `.pptx`, and **checks its own work**: did every
point actually make it onto a slide?

This is a real-world business agent, distilled from a production course-generation system.
It runs on **Gemini**, and degrades gracefully to a deterministic offline mode if no key
is present — so this notebook always produces a real deck.

### What it demonstrates (one per course day)
| Day | Concept | Where |
|----|----|----|
| 1 | Vibe coding — NL roles drive the work | Planner & Writer prompts in `agent/provider.py` |
| 2 | Tools & interoperability (MCP) | `agent/tools.py` — `assemble_deck`, `check_coverage` |
| 3 | Context engineering: skills & memory | `agent/skills/*.md`, multi-turn `agent/memory.py` |
| 4 | Agent quality & evaluation | coverage self-check drives self-correction (`builder.py`) |
| 5 | Prototype → production | model writes content / code only assembles; reproducible; graceful |

> **Runs with or without a key.** Add a Kaggle Secret `GOOGLE_API_KEY` (AI Studio) to have
> **Gemini** write the content. Without one, a deterministic offline writer fills the deck so
> the notebook still runs end-to-end and emits a real `.pptx`.
"""

SETUP_MD = """## 1. Install deps & write out the project
`python-pptx` builds the slides; `google-genai` powers the (optional) Gemini path.
Each module is then written from its own cell, so the code below is exactly what runs."""

INSTALL = """import importlib, subprocess, sys
def ensure(pkg, mod):
    try:
        importlib.import_module(mod); return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg]); return True
        except Exception as e:
            print("could not install", pkg, "-", e); return False
ensure("python-pptx", "pptx")
ensure("google-genai", "google.genai")  # only needed for the Gemini path

import os
for d in ("deck", "agent", "agent/skills"):
    os.makedirs(d, exist_ok=True)
print("ready")"""

ENABLE_GEMINI = """## 2. (Optional) Enable Gemini-written content
Skip to run the deterministic offline writer. To use Gemini:
1. Add your AI Studio key as a Kaggle **Secret** named `GOOGLE_API_KEY` (Add-ons → Secrets), or
2. set it in-notebook: `import os; os.environ["GOOGLE_API_KEY"] = "..."`

Model defaults to `gemini-3.1-flash-lite` (generous free-tier quota); override with
`GEMINI_MODEL`. If a model is rate-limited, the agent automatically falls back across a
chain of Gemini models — never to offline text — before degrading. A small production touch."""

OUTLINE_MD = """## 3. Your course outline
The agent's input: a title, an audience, and a few modules with bullet points. Edit freely."""

OUTLINE_CODE = '''OUTLINE = """# Giving Effective Feedback
Audience: Newly promoted team leaders (beginner)

## Why feedback matters
- The hidden cost of staying silent about problems
- Feedback as a tool for building trust, not just correcting
- The difference between feedback and criticism

## A simple model for feedback
- The Situation-Behaviour-Impact (SBI) model
- Keeping feedback specific and observable
- Focusing on behaviour, not personality

## Handling difficult reactions
- Staying calm when feedback is met with defensiveness
- Listening before responding
- Agreeing on a concrete next step together
"""
print(OUTLINE)'''

RUN_MD = """## 4. Build the course
Plan → write each module (multi-turn) → assemble the `.pptx` → check coverage → self-correct
any dropped points. Watch the log."""

RUN_CODE = """from agent import CourseArchitect, get_provider

provider = get_provider()          # Gemini if a key is present, else offline writer
architect = CourseArchitect(provider=provider, theme="corporate",
                            state_path="course_state.json", out_dir=".")
report = architect.build(OUTLINE, out_name="course.pptx")
print()
print(report.headline())"""

PREVIEW_MD = """## 5. Preview the slides
Kaggle can't render `.pptx` inline, so we draw a few slides from the deck spec with the
theme's colours. The real, editable file is `course.pptx` in the notebook output."""

PREVIEW_CODE = """import matplotlib.pyplot as plt
from deck import get_theme

def _hex(h): return "#" + h
def render_slides(deck, n=3):
    th = get_theme(deck.theme)
    panels = [("title", deck.title, [deck.subtitle or ("For: " + deck.audience)], th.band, "FFFFFF")]
    for sec in deck.sections:
        for sl in sec.slides:
            panels.append(("content", sl.title, sl.bullets, th.bg, th.title))
    panels = panels[:n+1]
    fig, axes = plt.subplots(1, len(panels), figsize=(5.2*len(panels), 3.4))
    if len(panels) == 1: axes = [axes]
    for ax, (kind, title, bullets, bg, tcol) in zip(axes, panels):
        ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis("off")
        ax.add_patch(plt.Rectangle((0,0),10,6, color=_hex(bg)))
        ax.add_patch(plt.Rectangle((0,5.7),10,0.3, color=_hex(th.accent)))
        ax.text(0.4, 5.0, title, fontsize=13, fontweight="bold", color=_hex(tcol), wrap=True)
        for i,b in enumerate(bullets[:5]):
            ax.text(0.6, 4.2-0.6*i, "• "+b, fontsize=9, color=_hex(th.body if kind=="content" else "FFFFFF"), wrap=True)
    plt.tight_layout(); plt.show()

render_slides(architect.state.deck_spec(), n=3)"""

OUTLINE_DESIGN_MD = """## 6. The agent can design the outline itself
No outline? Give it a one-line **topic** and the agent designs the whole curriculum — title,
audience, modules and teachable bullet points — which flows straight into the same build
pipeline. (This is exactly what the one-click 'Describe a Course' launcher uses.)"""

OUTLINE_DESIGN_CODE = '''# One plain-English topic in; a full structured outline out (a single Gemini call).
topic = "How to write basic Excel formulas for office staff"
designed = provider.generate_outline(topic)

print(f"TOPIC: {topic}\\n")
print(f"-> '{designed.title}'  (audience: {designed.audience})")
for i, m in enumerate(designed.modules, 1):
    print(f"\\n  Module {i}: {m['title']}")
    for b in m["bullets"]:
        print(f"    - {b}")
print("\\nGive that topic to architect.build(topic) and it designs the outline, then writes the deck.")'''

TOOLS_MD = """## 7. The MCP tool surface & the coverage check
The agent reasons with the LLM but only *acts* through these schema-typed tools — the same
shape as a Model Context Protocol server."""

TOOLS_CODE = """import json
from agent import CourseToolServer
ts = CourseToolServer(out_dir=".")
print(json.dumps(ts.list_tools(), indent=2)[:1100], "...")
print("\\nFinal coverage scorecard:")
print(json.dumps(architect.state.coverage, indent=2)[:900])"""

WRITEUP = """## 8. How it works — architecture & design

```
   (TOPIC ──▶ [ Outline Designer (Gemini) ] ──▶ OUTLINE)   ← optional: if you give only a topic
   OUTLINE ──▶ [ Planner (Gemini) ] ──▶ module plan ──▶ [ Writer (Gemini), per module ]
                                                                  │ multi-turn: sees course
                                                                  │ context + modules done
                                                                  ▼
   .pptx ◀── [ assemble_deck TOOL ] ◀── DeckSpec ◀── content slides (+ speaker notes)
                                            │
                                            ▼
                                  [ check_coverage TOOL ] ──▶ missing bullets?
                                            │ yes → regenerate those modules (self-correct)
                                            ▼ no
                                        DONE ✓
```

**Designs its own curriculum.** Given only a topic, the agent first designs a full outline
(modules + teachable points) before building — so a non-expert gets a structured course from
a single sentence, while an expert can still hand it a precise outline to follow exactly.

**Model writes, code assembles.** The LLM produces every title, bullet and speaker note;
`python-pptx` only lays them out and applies the theme. Code never invents content — a
production discipline that keeps output faithful and themes swappable (brand applied last).

**Scope fidelity, enforced by evaluation.** The agent must cover *only* the bullets you gave —
no padding, nothing dropped. The `check_coverage` tool verifies every input bullet landed on
a slide and feeds any gaps back into a **self-correction** round. That objective self-check is
the project's backbone, and the habit that matters most in real agent systems: *don't just
generate — verify, then fix.*

**Memory across a multi-turn build.** Slides are written module-by-module; each call sees the
course context and the modules already written, so the deck stays coherent rather than a bag
of disconnected slides.

**Graceful degradation (production thinking).** No key → deterministic offline writer.
Unparseable model output → coerced/fallback content. The build never stalls; the notebook
always emits a real `.pptx`.

### Why this matters (Agents for Business)
Turning rough outlines into structured, on-brand courseware is real, repetitive knowledge
work. The same pattern — *plan → generate section-by-section → assemble a real document →
verify coverage → self-correct* — generalises to any structured-document generation: reports,
proposals, onboarding packs, lesson plans.

### Limitations & next steps
- Layout is template-based (title / section / content / summary); richer layouts (two-column,
  image slides, diagrams) and an image-sourcing tool are natural extensions.
- Coverage is lexical (token overlap); an LLM-as-judge rubric (clarity, accuracy, tone) would
  deepen the Day-4 evaluation.
- A human-in-the-loop review/approve step per module would suit enterprise use.

*Built for the Google × Kaggle 5-Day AI Agents Intensive (Vibe Coding) capstone. Themes and
prompts here are generic; no proprietary brand assets are included.*"""


def build() -> dict:
    cells = [
        md(INTRO),
        md(SETUP_MD), code(INSTALL),
        writefile("deck/__init__.py"),
        writefile("deck/spec.py"),
        writefile("deck/theme.py"),
        writefile("deck/assembler.py"),
        writefile("agent/__init__.py"),
        writefile("agent/provider.py"),
        writefile("agent/memory.py"),
        writefile("agent/tools.py"),
        writefile("agent/skills/instructional_design.md"),
        writefile("agent/builder.py"),
        md(ENABLE_GEMINI),
        md(OUTLINE_MD), code(OUTLINE_CODE),
        md(RUN_MD), code(RUN_CODE),
        md(PREVIEW_MD), code(PREVIEW_CODE),
        md(OUTLINE_DESIGN_MD), code(OUTLINE_DESIGN_CODE),
        md(TOOLS_MD), code(TOOLS_CODE),
        md(WRITEUP),
    ]
    for i, cell in enumerate(cells):
        cell["id"] = f"cell{i:02d}"
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                        "name": "python3"},
                         "language_info": {"name": "python", "version": "3.11"}},
            "nbformat": 4, "nbformat_minor": 5}


if __name__ == "__main__":
    nb = build()
    out = os.path.join(HERE, "capstone_notebook.ipynb")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"wrote {out} ({len(nb['cells'])} cells)")
