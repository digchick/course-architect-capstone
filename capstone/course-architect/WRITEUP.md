# Course Architect
### An AI agent that turns a sentence into a finished, branded training course

**Track: Agents for Business** · Google × Kaggle 5-Day AI Agents Intensive (Vibe Coding) — Capstone

---

## The problem

Every training company, HR team, and subject-matter expert faces the same bottleneck:
turning *what they want to teach* into *finished courseware*. A rough outline — or just an
idea in someone's head — has to become a structured slide deck: a title slide, logically
ordered modules, content slides with three to five clean bullet points each, speaker notes
for the trainer, and a summary. Then someone has to check that nothing was missed and apply
the brand. It is hours of skilled, repetitive knowledge work, and it is the reason good
course ideas sit unbuilt.

**Course Architect** removes that bottleneck. You give it a topic — or a short outline if you
want control — and it designs the curriculum, writes every slide and speaker note, assembles
a themed PowerPoint, and **checks its own work** before handing it back.

## What it does, and who it's for

The agent serves two kinds of user, which is the heart of its design:

- **The non-expert** ("I need a course on handling customer complaints") types a single
  sentence. The agent **designs the entire outline itself** — title, audience, modules, and
  the specific teachable points under each — then builds the deck.
- **The expert** ("here is exactly what to cover") hands it a structured outline, and the
  agent expands *only* those points — no padding, nothing dropped.

Either way, the human stays in control of *what* is taught and *how it's branded*; the AI does
the laborious *writing and assembly*. The output is a real, editable `.pptx` — not a
screenshot, not a wall of text — that a trainer can present or refine immediately.

It is distilled from a production course-generation system, so the pattern is proven; the
version here is generic and reusable.

## See it in action

From the single line *"how to make basic Excel formulas,"* the agent designed a four-module
course — *Formula Basics → Cell References → Built-in Functions → Troubleshooting* — and wrote
**25 slides at 100% coverage**, with accurate, specific content: `=5+10` vs `=A1+B2`, absolute
references like `$A$1`, the `SUM`/`AVERAGE`/`COUNT` functions, order of operations (PEMDAS),
and real error codes (`#DIV/0!`, `#VALUE!`). No human wrote those bullets or decided that the
SUM function deserved its own slide — the agent did.

Given the structured outline *"Giving Effective Feedback,"* it showed genuine instructional
judgment: it took the single bullet *"the SBI model"* and expanded it into four dedicated
slides — an overview, then one each for Situation, Behaviour, and Impact — because that is how
the concept is actually taught. Coverage: 100%.

## How it works

```
   (TOPIC ─▶ [ Outline Designer ] ─▶ OUTLINE)     ← only if you give just a topic
   OUTLINE ─▶ [ Planner ] ─▶ module plan ─▶ [ Writer, module-by-module ]
                                                      │ multi-turn: sees the course
                                                      │ context + modules already written
                                                      ▼
   .pptx ◀─ [ assemble_deck TOOL ] ◀─ DeckSpec ◀─ content slides (+ speaker notes)
                                          │
                                          ▼
                                [ check_coverage TOOL ] ─▶ missing points?
                                          │ yes → regenerate those modules (self-correct)
                                          ▼ no
                                       DONE ✓
```

The agent *reasons* with Gemini but only *acts* through schema-typed tools — the same shape as
a Model Context Protocol (MCP) server. It plans, writes each module while remembering the
course so far, assembles the deck, then runs an objective coverage check that drives a
self-correction loop.

## How it uses the five course days

| Day | Concept | In Course Architect |
|----|----|----|
| **1 — Vibe coding** | Natural-language roles drive the work | The Outline Designer, Planner, and Writer are vibe-coded as system prompts — an instructional designer and a courseware writer — not hard-coded logic. |
| **2 — Tools & interoperability** | MCP-style tool surface | `assemble_deck` and `check_coverage` are exposed through a `list_tools()` / `call_tool()` server; the agent acts only through them. |
| **3 — Context engineering** | Skills & memory | A reusable instructional-design *skill* guides every prompt; multi-turn *memory* lets each module see the course context and prior modules, so the deck reads as one course. |
| **4 — Quality & evaluation** | Eval-driven self-correction | Coverage is measured, not assumed; gaps feed a self-correction round. *Don't just generate — verify, then fix.* |
| **5 — Prototype → production** | Robust, reproducible, graceful | Model writes / code assembles; automatic model-fallback under rate limits; graceful offline degradation; a one-click launcher for non-technical users. |

## Design decisions that matter

**Eval-driven self-correction is the backbone.** The agent must cover *only* the points in the
outline. The `check_coverage` tool verifies every point landed on a slide (token-overlap
matching, so paraphrasing is fine) and feeds any gaps back for regeneration. This is the habit
that separates a real agent from a one-shot prompt: an objective self-check with a loop to fix
what failed.

**The model writes; the code only assembles.** Gemini produces every title, bullet, and
speaker note; `python-pptx` only lays them out and applies the theme. Code never invents
content, which keeps the output faithful and lets the brand be swapped in last without
touching a word.

**Production resilience, not a happy-path demo.** Free-tier LLM quotas are real. When a model
is rate-limited, the agent automatically falls back across a chain of Gemini models — *never*
silently to placeholder text — and surfaces a clear warning if it ever has to degrade. With no
key at all, a deterministic offline writer still produces a complete deck, so the notebook
always runs end-to-end.

**Built for a non-coder.** The same agent is wrapped in a one-click launcher: describe a course
in plain English, and a finished `.pptx` opens — no command line, no editing. Genuine user
value, not a developer toy.

## Why it's innovative

Most "AI slide" tools either dump unstructured text or hand you a rigid template to fill in.
Course Architect is different in three ways: it **designs the curriculum**, not just the prose;
it **verifies its own coverage and self-corrects**, so scope is guaranteed rather than hoped
for; and it treats the LLM as a *writer wired to tools and a goal* — planning, remembering,
acting, and checking — which is exactly what an agent is, as opposed to a single model call.

## Limitations & next steps

- **Layouts are template-based** (title / section / content / summary). Two-column, image, and
  diagram slides — plus an image-sourcing tool — are natural extensions.
- **Coverage is lexical.** An LLM-as-judge rubric (clarity, accuracy, tone) would deepen the
  Day-4 evaluation beyond "did the point appear."
- **A human review/approve step per module** would suit enterprise rollout and compliance.

## The story

This started as a real frustration: great course ideas dying as unbuilt outlines. The capstone
made it concrete — an agent that does the building, while the human keeps the judgment.
Watching it take *"how to make basic Excel formulas"* and independently decide that absolute
references and `#DIV/0!` errors each deserve a slide — then prove it covered everything — is
the moment it stops feeling like a text generator and starts feeling like a colleague who
knows how to build a course.

*Built for the Google × Kaggle 5-Day AI Agents Intensive (Vibe Coding) capstone. Themes and
prompts are generic; no proprietary brand assets or production prompts are included.*
