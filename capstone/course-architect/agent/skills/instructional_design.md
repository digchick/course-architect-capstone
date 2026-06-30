# Skill: instructional design for slide courseware

Reusable expertise the agent loads before planning and writing slides (course Day-3
"skills"). Keep it short and prescriptive — it shapes every generation call.

## Scope fidelity (the golden rule)
- Build slides **only** from the bullets the user supplied. Expand and clarify them,
  but **do not invent new topics** or pad with material they didn't ask for.
- Every input bullet must end up represented on at least one slide. Record which
  input bullet(s) each slide addresses in its `covers` field.

## Structure
- One clear idea per content slide. Prefer 3–5 bullets; never more than 6.
- Each module starts from a single learning **objective** ("By the end, learners can…").
- Bullets are short, parallel, action-oriented phrases — not full paragraphs.
- Group closely related input bullets onto one slide; split a dense bullet into its
  own slide if it carries several distinct ideas.

## Speaker notes
- Every content slide gets concise speaker notes (2–4 sentences): what to say, an
  example or analogy, and a transition. Notes carry the depth; slides stay clean.

## Tone
- Match the stated audience and level. Concrete over abstract. Plain language.

## Deck shape
- Title slide → for each module: a section divider (title + objective) then its
  content slides → a closing summary slide. (The assembler adds title/section/summary
  framing; you produce the per-module content slides.)
