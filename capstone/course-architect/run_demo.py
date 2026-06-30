"""End-to-end demo: a short outline becomes a finished .pptx course.

  python run_demo.py                       # auto: Gemini if a key is set, else Mock
  python run_demo.py --mock                # force the deterministic Mock
  python run_demo.py --theme slate --out my_course.pptx
  python run_demo.py --outline path/to/outline.md
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from agent import CourseArchitect, get_provider

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="force the deterministic Mock provider")
    ap.add_argument("--theme", default=None, help="corporate | slate | fresh")
    ap.add_argument("--outline", default=os.path.join(HERE, "examples", "sample_outline.md"))
    ap.add_argument("--topic", default=None,
                    help="plain-English topic; the agent designs the outline itself")
    ap.add_argument("--out", default="course.pptx")
    ap.add_argument("--state", default="course_state.json")
    args = ap.parse_args()

    if args.topic:
        outline_text = args.topic
    else:
        with open(args.outline, "r", encoding="utf-8") as f:
            outline_text = f.read()

    print("=" * 70)
    print("COURSE ARCHITECT - outline -> branded PowerPoint course")
    print("=" * 70)
    print(outline_text.strip())
    print("=" * 70)

    provider = get_provider(force_mock=args.mock)
    architect = CourseArchitect(provider=provider, theme=args.theme,
                                state_path=args.state, out_dir=HERE)
    report = architect.build(outline_text, out_name=args.out)

    print("\n--- Deck outline ---")
    deck = architect.state.deck_spec()
    for i, sec in enumerate(deck.sections, 1):
        print(f"  Module {i}: {sec.module_title}")
        for sl in sec.slides:
            print(f"    - {sl.title}  ({len(sl.bullets)} bullets)")
    print(f"\n{report.headline()}")
    if report.missing:
        print("Still missing:", report.missing)

    degraded = getattr(provider, "degraded", 0)
    if degraded:
        print(f"\n[!] Heads-up: {degraded} step(s) used OFFLINE placeholder text because "
              f"Gemini was rate-limited (free-tier daily cap).\n"
              f"    Re-run later, set GEMINI_MODEL=gemini-3.1-flash-lite (500/day), or set "
              f"up billing for full AI-written content.")


if __name__ == "__main__":
    main()
