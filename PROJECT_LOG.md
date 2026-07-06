# Google 5-Day AI Agents Intensive — Vibe Coding Course (PROJECT LOG)

## What this is
Free Google×Kaggle course, **June 15–19, 2026**. Foundations → production for AI agents via *vibe coding* (natural language as the primary programming interface). Daily whitepaper + podcast + codelabs (self-paced, not submitted). Daily livestreams 11 AM PT (Anant Nawalgaria & Smitha Kolan) on Kaggle YouTube.
- Comp URL: kaggle.com/competitions/5-day-ai-agents-intensive-vibecoding-course-with-google
- Account: **Registered** (markjcooper / EQV UK). `userHasEntered: True` on the course comp.
- The dailies are NOT graded. **Only the capstone is graded → Kaggle badge + certificate (+ swag for top entries).**

## ⏱ CURRENT STATE — updated 2026-06-28
- **Primary = Course Architect** (Agents for Business). Build is done + re-verified fresh today (notebook executes clean end-to-end via nbconvert; 100% coverage).
- **NEW THIS SESSION (2026-06-28): live Gemini path is now real + verified.**
  - User created an AI Studio API key (stored in `.env` at project root, gitignored). **Key is exposed in chat → ROTATE after submission.**
  - **Migrated the Gemini SDK** off the now-EOL `google-generativeai` → the supported **`google-genai`** (v2.10) in `agent/provider.py`. New API: `genai.Client(api_key=…).models.generate_content(model, contents, config=GenerateContentConfig(system_instruction=…, response_mime_type='application/json', …))`. Also updated `requirements.txt` + the notebook's pip cell (`build_notebook.py`).
  - **Added retry-with-backoff** (2→16s, on 503/429/UNAVAILABLE/RESOURCE_EXHAUSTED) — free tier throws transient 503 "high demand" + 429; retries ride them out, else per-step Mock fallback.
  - **Model:** default now `gemini-2.5-flash` (via `GEMINI_MODEL` env). Available on this key incl. 2.5-flash, 3.5-flash, 3-flash-preview; 2.0-flash hit 429 quota.
  - **Live result:** Gemini wrote genuine content — e.g. "The Hidden Cost of Silence" → *Problems fester and escalate unchecked / Trust erodes between leaders and their teams*; summary uses real Bloom's objectives (articulate/differentiate/apply). It intelligently split the SBI module into 4 slides → **17 slides, 100% coverage**. Output: `course_gemini.pptx`. Huge quality leap over the offline placeholder.
  - **Verified both paths:** notebook+key→Gemini real content; notebook no-key→offline 14-slide deck; offline regression intact; nbconvert clean.
- **COVER IMAGE DONE (2026-06-28):** generated with `make_cover.py` (PIL, deck theme colours + EQV eagle brand mark, "outline → AI → deck" visual). User chose the **navy** look, eagle as corner mark. Canonical = `capstone/course-architect/cover.png` (=`cover_navy.png`); `cover_light.png` is the white alt. 1200×630.
- **ONE-CLICK LAUNCHER DONE (2026-06-28):** for non-coder use (user asked "how do I use it"). Added `MY_COURSE.md` (editable outline template), `Make My Course.bat` (reads GOOGLE_API_KEY from ../../.env → runs `run_demo.py --outline MY_COURSE.md --out "My Course.pptx"` → opens it), `HOW TO USE.txt` (3-step guide). VERIFIED via PowerShell: built "Time Management Essentials" with Gemini, 14 slides, 100% coverage, auto-opened. Workflow = edit MY_COURSE.md in Notepad → double-click the .bat → deck opens. (Git-Bash→cmd quoting mangles spaced .bat names; run via PowerShell `& "...bat"` or just double-click — NOT `cmd //c`.) Great "user value" demo moment for the video.
- **AGENT-DESIGNS-OUTLINE + RATE-LIMIT FIX (2026-06-28):** user wanted to type a plain topic (not a structured outline) and got "rubbish 3 slides". Two root causes fixed:
  1. **No outline** → added `generate_outline(topic)` to provider (Gemini `_OUTLINE_SYSTEM` + Mock fallback); `builder.build()` now detects input with no `## ` sections, treats it as a topic, and the agent DESIGNS the outline first. `run_demo.py` gained `--topic`. So a one-line topic now yields a full multi-module course.
  2. **Templated content** = free-tier **RPD cap**: Gemini 2.5 Flash is **20 requests/DAY** on free tier (dashboard showed 20/20 exhausted from testing) → silent Mock fallback. Fix: **model-fallback chain** in `GeminiProvider._json_call` (`_FALLBACK_MODELS`: 2.5-flash → 3.5-flash → 2.5-flash-lite → **3.1-flash-lite=500/day**); on 429 it switches Gemini models (not to offline), sticks with the first that works. **Default model now `gemini-3.1-flash-lite`** (500/day). Added `provider.degraded` counter + a loud `[!]` warning in run_demo when any step still used offline text. VERIFIED: "how to make basic excel formulas" → 4 modules, 25 slides, **0/25 templated**, real content (=5+10 vs =A1+B2, $A$1 mixed refs, PEMDAS, #DIV/0!). Dashboard confirms 3.1-flash-lite 7/500 used.
  - **Interfaces added:** `Describe a Course.bat` (double-click → type a topic → builds; set/p couldn't be auto-tested in harness but logic = proven Make bat), `MY_COURSE.md` now accepts a one-line topic OR a full outline, `HOW TO USE.txt` updated. `make_cover.py` cover unchanged.
- **Billing question:** free tier is enough — 3.1-flash-lite = 500 req/day ≈ 80 courses/day; judges use their own key; notebook degrades gracefully keyless. Billing only for flagship quality / heavy volume.

## ✅ EVERYTHING-BUT-VIDEO COMPLETE (2026-06-28, autonomous push while user asleep)
- **Notebook regenerated + re-verified** (`build_notebook.py` → 25 cells). Narrative updated: model default 3.1-flash-lite + fallback story; NEW section 6 "the agent designs the outline itself" (calls `provider.generate_outline`); architecture diagram now shows optional TOPIC→outline step; "designs its own curriculum" design point. **nbconvert clean OFFLINE** (course.pptx) AND **WITH KEY** (Gemini active, topic-design produced real Excel outline, 0 degraded, 100% coverage).
- **WRITEUP.md written** = paste-ready Kaggle report, **1,245 words** (limit 2500): problem, users/value, see-it-in-action (Excel + SBI examples), architecture, 5-day mapping, design decisions, innovation, limitations, story. Track = Agents for Business.
- **VIDEO_SCRIPT.md rewritten** (~4 min teleprompter) — leads with the "type a topic → agent designs the course" wow + Excel demo, coverage self-check, outline-mode, 5-day mapping, close.
- **SUBMISSION_GUIDE.txt** = full hand-holding: Part B record (Clipchamp / Xbox Game Bar), Part C YouTube upload (user's accounts: main vieve.cooper@gmail.com / brand channel **coopie007**; set Unlisted), Part D Kaggle (accept rules → upload notebook public → New Writeup → paste WRITEUP.md → cover.png → YouTube link → attach notebook → Track=Agents for Business → Submit). Reminds to ROTATE the exposed API key.
- **README.md updated** (topic mode, launchers, google-genai, 3.1-flash-lite). Offline regression PASS; all deliverables present.
- **GIT (2026-06-30):** repo initialised + first commit `d148fd1` on `master`, pushed to **PRIVATE** GitHub `digchick/course-architect-capstone` (https://github.com/digchick/course-architect-capstone). `.env`/key + `__pycache__` excluded (verified). To use as the capstone public code link: `gh repo edit digchick/course-architect-capstone --visibility public` (or the Kaggle notebook serves as the public link instead). Commit+push future changes from now on.
- **USER-SIDE REMAINING (only this):** (1) record the ≤5-min video, (2) upload to YouTube, (3) do the Kaggle clicks per SUBMISSION_GUIDE.txt. Deadline **Jul 6 23:59 PT**. Then ROTATE the API key (was exposed in chat).

## ⏱ PRIOR STATE — 2026-06-19 (Day 5 / final day)
- Today is **Day 5**, the last course day. The capstone competition **went live today**.
- **CAPSTONE AGENT BUILT + VERIFIED** (see next section). Concept chosen autonomously (user deferred): the *Arena Strategist*, which honours the Orbit Wars hint.
- Remaining work is all **interactive/user-side**: accept capstone rules, add a Gemini key, run on Kaggle, record the 2–3 min video, submit. (See "Setup checklist" + "Next steps".)

## ✅ CAPSTONE BUILD — DONE (2026-06-19): "Arena Strategist"
**Location:** `capstone/arena-strategist/`. A vibe-coded, self-improving game-strategy agent: two Gemini roles (Proposer + Critic) invent strategy "genomes" for a self-contained competitive sim and optimise them against a **calibrated Elo league** (the reward), with persistent **memory + falsification log**. It's the LLM-agent recast of the eval-driven method that won us Orbit Wars silver — *not* the Orbit Wars agent itself, and it never touches the locked OW entry.
- **Demonstrates all 5 days:** D1 vibe-coded Proposer/Critic prompts · D2 MCP-style tool server (`tools.py`, list_tools/call_tool) · D3 skills (`skills/strategy_heuristics.md`) + memory (`memory.py`) · D4 calibrated league eval (`league.py`) · D5 reproducible/observable/graceful-degradation.
- **Runs WITHOUT a key** via a deterministic `MockProvider` (guided hill-climb) — same pattern as the official starter kernel — and swaps in real Gemini when `GOOGLE_API_KEY` is set.
- **Verified:** calibrated ladder is monotonic (adaptive 1223 top → naive_miner 777 bottom); agent champion reaches **elo 1308, rank 1/7, 86.7% win-rate, BEATS the ceiling**; falsification log records + avoids dead ends.
- **`capstone_notebook.ipynb` is the submission** — self-contained (writes every module via `%%writefile`), **executed end-to-end clean in a fresh dir via nbconvert** (plot + tables render, no errors). Regenerate with `python build_notebook.py`.
- **Deliverables present:** notebook, `README.md` (writeup), `VIDEO_SCRIPT.md` (2.5-min script), `run_demo.py`, `requirements.txt`. Game = "Orbital Skirmish" (8-knob genome policy; mine/build/expand/fortify/raid).
- **STATUS: DEMOTED TO FREESTYLE BACKUP.** After reading the live rules (judges weight "real-world problem + user value", where a strategy tech-demo is weak; it only fits Freestyle), user chose to **pivot to a real-world useful agent**. Arena Strategist is kept as a valid Freestyle fallback but is NOT the primary submission.

## ✅✅ PRIMARY CAPSTONE SUBMISSION — "Course Architect" (built + verified 2026-06-19)
**Location:** `capstone/course-architect/`. **Track: Agents for Business.** User-chosen idea: an agent that turns a **short outline → finished, branded PowerPoint course** (distilled from their EQV course-generation product; generic/no proprietary assets).
- **What it does:** parse outline → **Planner (Gemini)** makes a module plan → **Writer (Gemini), multi-turn module-by-module** generates slides + speaker notes → **assemble_deck tool** (python-pptx) builds a themed `.pptx` → **check_coverage tool** verifies every input bullet landed on a slide → **self-corrects** dropped bullets. Model writes ALL content; code only assembles (the EQV production lesson).
- **Demonstrates all 5 days:** D1 vibe-coded Planner/Writer prompts · D2 MCP tool server (`agent/tools.py`) · D3 skill (`agent/skills/instructional_design.md`) + multi-turn memory (`agent/memory.py`) · D4 coverage eval → self-correction (`agent/builder.py`) · D5 reproducible/observable/graceful.
- **Runs WITHOUT a key** via a deterministic offline writer (full-coverage canned content) — Gemini when `GOOGLE_API_KEY` set. python-pptx required (notebook pip-installs it).
- **Verified:** sample outline (3 modules, 9 bullets) → **14-slide deck, 100% coverage**, valid `.pptx` (reopens, speaker notes present); self-correction proven (FlakyProvider drops a bullet → recovered to 100% in 1 fix round); `capstone_notebook.ipynb` **executed clean end-to-end in a fresh dir via nbconvert** (deck built, coverage 100%, matplotlib slide preview renders).
- **Deliverables:** `capstone_notebook.ipynb` (the submission; self-contained `%%writefile` + run + preview + writeup), `README.md` (writeup basis, <2500 words), `VIDEO_SCRIPT.md` (≤5-min YouTube script), `run_demo.py`, `build_notebook.py`, `examples/sample_outline.md`, `requirements.txt`. Sample output: `sample_course.pptx`.
- **To submit (user):** on Kaggle → create a **New Writeup** in the **Agents for Business** track → paste/adapt README (≤2500 words) → attach a **cover image** + the **code** (this notebook) → record + attach a **YouTube video ≤5 min** (use VIDEO_SCRIPT) → **Submit** (top-right). Add Gemini key as a Secret first if you want live Gemini content. Deadline Jul 6 23:59 PT.

## ✅ CAPSTONE — AUTHORITATIVE requirements (read live via browser 2026-06-19)
- **Slug:** `vibecoding-agents-capstone-project`. Community **Hackathon**. Rules ACCEPTED (file download now works; bundle = a 1-line "Hackathon with no provided dataset" note).
- **Deadline:** **Mon Jul 6 2026, 23:59 PT** (page: "17 days to go"; UTC close 2026-07-07 06:59). Completion → badge + certificate; top per-track entries get swag + social recognition.
- **Goal:** build an AI agent that solves a **meaningful REAL-WORLD problem** — help individuals stay organized, streamline business processes, support social impact, or explore a new idea. Open-ended; no fixed task; no dataset.
- **DEFINITIVELY NO "Kaggriculture" / farming simulation.** Two web searches hallucinated that; the live page contains no such words. Disregard it entirely. (Submission *format* the searches gave — writeup+video+code — was correct, though.)
- **4 tracks (pick one):** Agents for Good · Agents for Business · Concierge Agents · Freestyle ("innovative projects with a 'wow' factor").
- **Judging:** innovation, solution design, communication, effective application of course concepts & agent tech; problem definition, implementation quality, **user value**, architecture, documentation, project story.
- **A valid submission — ALL required:**
  - **Kaggle Writeup** = project report (title + subtitle + detailed analysis), **≤ 2,500 words**, must select a Track. Create via "New Writeup" → Save → "Submit" (top-right).
  - **Cover image** (required to submit).
  - **Video demo** (REQUIRED), **≤ 5 min**, published to **YouTube**, attached to the Writeup Media Gallery.
  - **Public codebase** + project link attached (a Kaggle notebook kernel is fine as the code asset; GPU T4 + internet available).
- **Reference starter (this cohort):** `hmnshudhmn24/polyglot-agent-mcp-sandbox-code-generation` (in `capstone/starter-ref/`). Prior edition `agents-intensive-capstone-project` (11,464 teams) = same Writeup format; top entries were focused, genuinely-useful real-world agents.

## Daily syllabus (corrected/confirmed) + codelab URLs
| Day | Date | Unit | Status |
|-----|------|------|--------|
| 1 | Jun 15 | Intro to Agents & Vibe Coding | content available |
| 2 | Jun 16 | Agent Tools & Interoperability (MCP / A2A / A2UI / AP2 / UCP) | content available |
| 3 | Jun 17 | Context Engineering: Sessions, Skills & Memory (long-term memory, state, token budget) | content available |
| 4 | Jun 18 | Agent Quality & Security (testing, guardrails, security eval, threat mapping) | content available |
| 5 | Jun 19 | Prototype → Production (governed, scalable, observable fleet) — capstone launches | TODAY |

**Stack:** Antigravity 2.0 / IDE / CLI · **ADK 2.0** (Agent Development Kit) · **Agents CLI** · **Gemini** (Google AI Studio key) · **MCP**; deploy to **Cloud Run**.

**Real codelab URLs (codelabs.developers.google.com):**
- Authoring Google Antigravity Skills — `/getting-started-with-antigravity-skills`
- Vibecode an ADK 2.0 Ambient Agent with Antigravity & Agents CLI — `/vibecode-ambient-expense-agent`
- Managing the Agent Lifecycle with Agents CLI & ADK 2.0 — `/agents-cli-adk-lifecycle`
- Vibecode & Secure an AI Agent Lifecycle (Antigravity + TDD) — `/secure-agentic-coding`
- Vibecode & Deploy a Frontend for an ADK agent — `/vibecode-frontend-with-antigravity`

## Setup checklist (interactive — needs the user / a browser session)
- [x] Kaggle account (registered, entered course comp)
- [ ] **Accept rules on the capstone comp** `vibecoding-agents-capstone-project` (website click; unblocks file download + submission)
- [ ] **Google AI Studio account + API key** (aistudio.google.com)
- [ ] Install **Antigravity 2.0 / IDE / CLI** + **ADK 2.0**
- [ ] Join **Kaggle Discord** (#5dgai-introductions, #5dgai-question-forum)
- [ ] (For deploy) Google Cloud / Cloud Run access

## Orbit Wars — relevance to the capstone (per user hint 2026-06-19)
Orbit Wars (`C:\Projects\orbit-wars`) is our $50k Kaggle **simulation** comp where we built a competition-grade autonomous agent — **SILVER, top 5% of 4,689 teams**. Assets: a **calibrated local league eval harness** (`_league.py`/`_one_game.py`), multiple agent strategies (producer_v2, behavior-clone, AZ-lite self-play), and a rigorous falsification methodology.
- **How it helps:** the league eval discipline is a textbook Day-4 "rigorous agent evaluation" artifact; the multi-agent self-play is a real multi-agent story. Strong *case-study / methodology* material for a capstone writeup.
- **The "or not":** Orbit Wars is a pure RL/search agent (PyTorch) — **no Gemini, no MCP, no vibe coding**. The capstone rewards an *LLM* agent built with the taught stack, so Orbit Wars is not a drop-in submission; it contributes methodology/narrative, not the agent itself.
- **🔒 HARD CONSTRAINT:** Orbit Wars' live submission is a **LOCKED silver entry** (`{producer_v2, alyce}`, finals Jun 23). Using it for the capstone must be **read-only/narrative**. Do NOT submit, rotate, or modify anything on the orbit-wars ladder.

## Next steps (all user-side / interactive)
1. Accept rules on the capstone comp `vibecoding-agents-capstone-project` (website click).
2. (Optional, for the live-LLM version) Create a Google AI Studio key; add it as a Kaggle Secret `GOOGLE_API_KEY`. The notebook runs fine without it (deterministic Mock).
3. Upload `capstone/arena-strategist/capstone_notebook.ipynb` to Kaggle, run it (Save & Run All), confirm the tables + plot render.
4. Record the 2–3 min video from `VIDEO_SCRIPT.md`.
5. Submit: notebook writeup + video + rationale (`README.md`) + code link, before **Jul 6 23:59 PT**.

## Optional polish ideas (only if desired)
- Self-play co-evolution: promote champions into the anchor set, then re-climb (AlphaZero-lite, like OW).
- Parallelise the league; export tool-call traces as metrics (Day-5 production angle).
- Have the LLM emit a small policy *function* run in a sandbox (the starter-kernel code-gen + Day-4 security pattern).

## 🎬 VIDEO PRODUCED AUTONOMOUSLY (2026-07-06, deadline day — ~21h left at build time)
- User approved AI narration ("voice is good") → **en-GB-RyanNeural** (edge-tts).
- **Content upgrade first** (user: "output a bit weak"): skill+writer now demand 4-6 substantial bullets (8-16 words), ONE concrete worked `example` per slide (new Slide.example field → themed rounded example box in assembler), 3-5 sentence notes; outline 4-5×4-5. Verified: Excel rebuild = 22 slides, example boxes render ("type 5+5 → '5+5'; =5+5 → 10", "=MIN(D2:D50)"), 100% coverage, no degradation. Committed c339951 + pushed. Notebook regenerated + nbconvert-verified.
- **Video pipeline** (scratchpad/video_build/): `make_video_deck.py` builds 10-slide 16:9 deck (cover → problem → one-sentence input → 4 real course slides → coverage log → architecture → close) + narration.json; edge-tts Ryan per-slide MP3s (160s total); PowerPoint COM embeds audio (PlayOnEntry+hidden), auto-advance = duration+1s, `CreateVideo` 1080p30.
- **RESULT: `capstone/course-architect/Course_Architect_Demo.mp4` — 2:55, 19.4 MB** (≤5min ✓). mp4/mp3 gitignored (video ships via YouTube, not repo).
- **NEXT: user watches/approves → YouTube upload (channel coopie007 or main, Unlisted) → Kaggle Writeup+submit per SUBMISSION_GUIDE.txt.**

## 📺 YOUTUBE LIVE (2026-07-06): https://youtu.be/Ac01bmWL5u4 (Unlisted, channel coopie007, title verified via oEmbed). Repo PUBLIC + root README front page added. Writeup 1,364w incl. "Try it yourself". Remaining: Kaggle notebook upload + Writeup + SUBMIT.

## 🏆 SUBMITTED TO KAGGLE (2026-07-06, ~21h before deadline) — via Puppeteer, fully automated
- Logged in (mc@digitalchicken.co.uk), pushed notebook as PUBLIC kernel `markjcooper/course-architect-capstone`.
- Created Writeup "Course Architect" / subtitle / Track=**Agents for Business** / pasted WRITEUP.md (1343w) via native-setter injection / cover+thumbnail (cover.png) / **YouTube video https://youtu.be/Ac01bmWL5u4** in gallery / gallery IMAGE (cover_light.png, needed a non-empty Image Title to tick the "Images" checklist item — the gotcha) / Project Link = github.com/digchick/course-architect-capstone.
- Checklist 8/8 → Submit → confirm CC-BY-4.0 dialog → **"Submitted!"** (green tick). Editable until Jul 7 07:59 BST.
- **ONLY REMAINING USER TASK: ROTATE the exposed Gemini API key** (aistudio.google.com → delete AQ.Ab8… → new key; update .env + any Kaggle Secret).

## 🔗 NOTEBOOK LINK ADDED (2026-07-06, post-submit) — kept status Submitted
- User asked if the notebook was sent or only the writeup. It WAS pushed as PUBLIC kernel `markjcooper/course-architect-capstone` (status COMPLETE) but the writeup only linked GitHub. Added the runnable Kaggle notebook as a 2nd Project Link via Insert Resource → Kaggle Code → Owner "Created by you" → Insert → Update Submission → refresh. Writeup now shows BOTH links (GitHub + Kaggle Notebook·Public), still "Submitted!". Participation counters are comp-wide aggregates (3,731→3,771), not per-user proof — the "Submitted!" badge is.
