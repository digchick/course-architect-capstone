# Video script — Course Architect (~4 min; hard limit 5 min)

Read the **[SAY]** lines out loud while you do the **[SHOW]** actions on screen. Aim for a
calm, normal speaking pace. You don't have to be word-perfect — say it in your own words.
Total target: about 4 minutes. (Full recording + upload steps are in `SUBMISSION_GUIDE.txt`.)

---

### 0:00 — Hook (20s)
**[SHOW]** The cover image (`cover.png`), or the title slide of a finished deck.
**[SAY]** "Turning a rough idea into a finished, on-brand training course is hours of work —
writing every slide, every speaker note, checking nothing's missed. Course Architect is an AI
agent that does all of it. Watch."

### 0:20 — The "wow": just describe it (50s)
**[SHOW]** Double-click **`Describe a Course.bat`**, and type:
`How to write basic Excel formulas for office staff`. Press Enter.
**[SAY]** "I haven't written an outline. I've just told it what I want — a course on basic Excel
formulas for office staff. From that one sentence, the agent is now designing the whole
curriculum itself: the title, the audience, the modules, and the specific points to teach under
each one — then it writes every slide."

### 1:10 — The result (45s)
**[SHOW]** `My Course.pptx` opens. Scroll through: title, a module divider, a couple of content
slides (show the real bullets — cell references, the SUM function, `#DIV/0!` errors), the
summary. Click a slide and show the **Notes** pane.
**[SAY]** "Seconds later, here's a real, editable PowerPoint — around 25 slides. Title slide, a
section per module, content slides with clean bullet points, and — importantly — a speaker note
on every slide telling the trainer what to say. The content is genuinely accurate: cell
references, the SUM function, even common error codes. The agent decided all of this."

### 1:55 — It checks its own work (45s)
**[SHOW]** The notebook (or terminal) log: `plan → write → eval → coverage 100%`. Point at the
coverage line.
**[SAY]** "But the part I'm proudest of is this: it doesn't just generate and hope. After
writing, it runs a coverage check — did every point it planned actually land on a slide? If
something was dropped, it rewrites that module and checks again, until it's complete. That
verify-then-fix loop is what makes it an agent you can trust, not just a text generator."

### 2:40 — You can also give it an outline (30s)
**[SHOW]** Open `MY_COURSE.md`, show a structured outline (title, audience, `##` modules, bullets).
**[SAY]** "If you're the expert and want full control, you can hand it a precise outline instead,
and it expands exactly those points — no padding, nothing dropped. So it works for a complete
beginner and for a professional course designer."

### 3:10 — How it works / the course (40s)
**[SHOW]** The architecture diagram and the Day 1–5 mapping table in the notebook/writeup.
**[SAY]** "Under the hood it's the agent toolkit from the course: vibe-coded roles for the
designer, planner and writer; an MCP-style tool layer that actually builds the file and checks
coverage; memory so the course stays coherent across modules; and a real evaluation at its
heart. It even falls back across Gemini models if one is busy, and runs offline if there's no
key — so it never just stops."

### 3:50 — Close (15s)
**[SHOW]** The cover image again, or the finished deck.
**[SAY]** "That's Course Architect — describe a course, and get a finished, branded deck you can
present today. The same pattern works for any structured document: reports, proposals,
onboarding. Thanks for watching."

---

### Tips
- **Do one practice run first** (so the model's warm and you know the timing), then record.
- The payoff is the **real `.pptx` opening** — make sure you show that, not just the log.
- If a live build feels risky, you can pre-build the deck and just narrate over the finished
  file plus the notebook — that's completely fine.
- Keep it **under 5 minutes** (hard limit). ~4 is ideal. Shorter is better than rushed.
