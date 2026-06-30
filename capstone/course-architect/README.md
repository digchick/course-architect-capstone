# Course Architect

**An AI agent that turns a short outline into a finished, branded PowerPoint course.**
Capstone for the Google × Kaggle 5-Day AI Agents Intensive (Vibe Coding). **Track: Agents for Business.**

You give it a **plain-English topic** — or a short outline if you want control — and it
designs any missing structure, plans the course, writes every slide and speaker note,
assembles a themed `.pptx`, and **checks its own work** — confirming every point actually
made it onto a slide, and self-correcting if anything was dropped.

It runs on **Gemini**, and degrades gracefully to a deterministic offline writer when no
API key is present — so the notebook always produces a real deck.

---

## The problem it solves
Turning rough outlines into structured, on-brand courseware is real, repetitive knowledge
work — hours of building title slides, content slides, speaker notes, and a summary, then
checking nothing was missed. Course Architect automates that end-to-end while keeping a
human in control of the *content* (the outline) and the *brand* (the theme). It's distilled
from a production course-generation system; the pattern generalises to any structured
document (reports, proposals, onboarding packs, lesson plans).

## What it produces
From the 9-bullet sample outline (`examples/sample_outline.md`) it builds a **14-slide deck**
(title → 3 module sections → 9 content slides with speaker notes → summary) at **100%
outline coverage**, in well under a second on the offline writer, and a few seconds on Gemini.

## Architecture
```
   OUTLINE ─▶ [ Planner (Gemini) ] ─▶ module plan ─▶ [ Writer (Gemini), per module ]
                                                            │ multi-turn: sees course
                                                            │ context + modules done
                                                            ▼
   .pptx ◀─ [ assemble_deck TOOL ] ◀─ DeckSpec ◀─ content slides (+ speaker notes)
                                          │
                                          ▼
                                [ check_coverage TOOL ] ─▶ missing bullets?
                                          │ yes → regenerate those modules (self-correct)
                                          ▼ no
                                       DONE ✓
```

## How it maps to the five course days
| Day | Concept | Where |
|----|----|----|
| 1 | Vibe coding — natural-language roles drive the build | Planner & Writer system prompts (`agent/provider.py`) |
| 2 | Tools & interoperability (MCP) | `agent/tools.py` — `list_tools()` / `call_tool()` for `assemble_deck`, `check_coverage` |
| 3 | Context engineering: skills & memory | `agent/skills/instructional_design.md`; multi-turn course state (`agent/memory.py`) |
| 4 | Agent quality & evaluation | coverage self-check drives self-correction (`agent/builder.py`) |
| 5 | Prototype → production | model writes / code only assembles; reproducible; observable tool log; graceful degradation |

## Key design decisions
- **The model writes; code only assembles.** The LLM produces every title, bullet and
  speaker note; `python-pptx` only lays them out and applies the theme. Code never invents
  content — output stays faithful and themes stay swappable (brand applied *last*).
- **Scope fidelity, enforced by evaluation.** The agent expands *only* the bullets you gave
  — no padding, nothing dropped. `check_coverage` verifies every input bullet landed on a
  slide (token-overlap match so paraphrasing is fine) and feeds gaps into a self-correction
  round. *Don't just generate — verify, then fix.*
- **Memory across a multi-turn build.** Slides are written module-by-module; each call sees
  the course context and the modules already written, so the deck reads as one course.
- **Graceful degradation.** No key → deterministic offline writer. Unparseable model output
  → coerced/fallback content. The build never stalls; a real `.pptx` always comes out.

## Results (offline writer, deterministic)
```
Plan:   3 modules, 9 bullets
Write:  9 content slides + speaker notes
Eval:   coverage 100% (9/9 bullets)
Build:  14 slides -> course.pptx
```
Self-correction is verified independently: a writer that deliberately drops a bullet is
caught by the coverage check and recovers to 100% in one fix round.

## Run it
```bash
pip install python-pptx            # core; matplotlib only for the notebook slide preview
python run_demo.py --topic "how to write basic Excel formulas for office staff"
python run_demo.py                 # uses the sample outline; Gemini if a key is set, else offline
python run_demo.py --mock          # force the deterministic offline writer
python run_demo.py --theme slate --out my_course.pptx
python run_demo.py --outline path/to/your_outline.md
```
**No command line?** Double-click **`Describe a Course.bat`** (type a topic) or edit
`MY_COURSE.md` and double-click **`Make My Course.bat`**. See `HOW TO USE.txt`.

**Enable Gemini:** set `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) and `pip install google-genai`.
Default model `gemini-3.1-flash-lite` (generous free-tier quota); override with `GEMINI_MODEL`.
If a model is rate-limited, the agent auto-falls-back across Gemini models before going offline.

**Kaggle:** `capstone_notebook.ipynb` is self-contained — it installs deps, writes every
module via `%%writefile`, builds the deck, previews slides, and prints the coverage
scorecard. Add a Kaggle Secret `GOOGLE_API_KEY` to switch the offline writer for Gemini.
Regenerate the notebook from source with `python build_notebook.py`.

## Files
```
deck/    spec.py (contract + coverage eval) · theme.py (themes) · assembler.py (python-pptx)
agent/   provider.py (Gemini + offline) · tools.py (MCP) · memory.py · builder.py
         skills/instructional_design.md
run_demo.py · build_notebook.py · capstone_notebook.ipynb · examples/sample_outline.md
```

## Limitations & next steps
- Layouts are template-based (title / section / content / summary); two-column, image, and
  diagram slides plus an image-sourcing tool are natural extensions.
- Coverage is lexical; an LLM-as-judge rubric (clarity, accuracy, tone) would deepen the eval.
- A human review/approve step per module would suit enterprise rollout.

*Themes and prompts here are generic; no proprietary brand assets or production prompts are included.*
