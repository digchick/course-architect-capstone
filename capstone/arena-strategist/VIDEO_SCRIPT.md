# Video script — Arena Strategist (~2.5 min)

The capstone submission asks for a short video explanation. This is a scene-by-scene
script: **[SHOW]** = what's on screen, **[SAY]** = voiceover. Aim for 2–3 minutes.
Record the notebook running on Kaggle (or `run_demo.py` locally) so the numbers are live.

---

### 0:00 — Hook (15s)
**[SHOW]** Title cell of `capstone_notebook.ipynb`.
**[SAY]** "Most LLM strategy demos never check if the strategy actually works. Arena
Strategist is built the opposite way — around an objective, calibrated reward. It's
an agent that *discovers* winning strategies for a competitive game, using the same
eval-driven method that took our team to silver in a $50k Kaggle simulation."

### 0:15 — The game (25s)
**[SHOW]** The "Orbital Skirmish" rules cell / README diagram.
**[SAY]** "The arena is a two-player game: mine ore, build ships, expand to score
points, fortify to defend, or raid to destroy the enemy's points. Economy, military,
territory and defence form a rock-paper-scissors loop — so no single simple strategy
wins. A strategy is just eight numbers, a 'genome', which makes it safe to run and
easy for an LLM to propose."

### 0:40 — Calibrate the league (25s)
**[SHOW]** Run the calibration cell; the anchor ladder table appears.
**[SAY]** "Step one is the most important: calibrate the evaluator. We run a league
of hand-built anchors from naive to sophisticated. The naive miner sits at the
bottom, the balanced 'adaptive' anchor on top. Because the league reproduces an
ordering we already trust, we can now trust it to judge brand-new strategies. This
calibration discipline is exactly what kept us from fooling ourselves in Orbit Wars."

### 1:05 — The agent loop (35s)
**[SHOW]** Run the agent cell; the per-round log streams (elo, rank, keep/mutate/discard).
**[SAY]** "Now the agent. Each round a Proposer — Gemini — reads the strategy skill
file, the anchor ladder, and its memory of past attempts, and proposes a new genome.
The orchestrator scores it through an MCP-style tool, the calibrated league. Then a
Critic decides: keep it as the new best, mutate, or discard. Dead ends are written to
a falsification log so neither the model nor we ever re-explore them — the
highest-leverage habit from our competition work."

### 1:40 — Result (25s)
**[SHOW]** The verification table (champion at rank 1) + the Elo-climb plot.
**[SAY]** "Within a couple of dozen rounds the agent finds a strategy that beats the
top anchor — here, Elo 1308 against the ceiling's 1223, winning nearly 87% of its
games. Verified in a fresh league, the champion tops the ladder."

### 2:05 — Course concepts + close (25s)
**[SHOW]** The concept-mapping table (Days 1–5).
**[SAY]** "Everything maps to the course: vibe-coded Proposer and Critic, an MCP tool
surface, skills and persistent memory, and a rigorous calibrated evaluation at its
heart — plus production touches: it's deterministic, it logs every tool call, and it
runs with or without an API key. That's Arena Strategist — thanks for watching."

---

### Recording tips
- Run once *before* recording so any package install is cached; then re-run on camera.
- If you don't have a Gemini key, the deterministic Mock gives identical, repeatable
  numbers — fine for the video. Mention that a key swaps in real Gemini reasoning.
- Keep it under 3 minutes; let the live tables/plot do the talking.
