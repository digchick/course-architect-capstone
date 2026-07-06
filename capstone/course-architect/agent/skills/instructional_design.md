# Skill: instructional design for slide courseware

Reusable expertise the agent loads before planning and writing slides (course Day-3
"skills"). Keep it short and prescriptive — it shapes every generation call.

## Scope fidelity (the golden rule)
- Build slides **only** from the bullets the user supplied. Expand and clarify them,
  but **do not invent new topics** or pad with material they didn't ask for.
- Every input bullet must end up represented on at least one slide. Record which
  input bullet(s) each slide addresses in its `covers` field.

## Structure
- One clear idea per content slide. Prefer 4–6 substantial bullets; never more than 6.
- Bullets teach, not tease: each is a complete, specific statement (roughly 8–16 words)
  that carries real information — a rule, a step, a criterion, a consequence — not a
  vague label like "overview" or "why it matters".
- Each module starts from a single learning **objective** ("By the end, learners can…").
- Bullets are parallel and action-oriented — informative phrases, not full paragraphs.
- Group closely related input bullets onto one slide; split a dense bullet into its
  own slide if it carries several distinct ideas.

## Worked example (every content slide)
- Every content slide includes an `example`: ONE concrete worked example, mini-scenario,
  or do/don't specific to that slide's idea — something a learner could actually try or
  recognise (numbers, named situations, real phrasing; not "e.g. various cases").
- Keep it to one or two sentences; it renders in a highlighted example box.

## Speaker notes
- Every content slide gets substantial speaker notes (3–5 sentences): what to say in the
  trainer's voice, a second example or analogy, a common mistake to warn about, and a
  check question or transition. Notes carry the depth; slides stay clean.

## Tone
- Match the stated audience and level. Concrete over abstract. Plain language.

## Deck shape
- Title slide → for each module: a section divider (title + objective) then its
  content slides → a closing summary slide. (The assembler adds title/section/summary
  framing; you produce the per-module content slides.)
