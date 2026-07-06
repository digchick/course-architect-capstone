"""Demonstrate the self-correction loop with REAL data.

A writer that deliberately drops one point on its first pass. The coverage tool
catches the gap; the agent regenerates just that module and re-checks — recovering
to 100%. Prints the real before/after numbers (used to build the showcase graphic).
"""
from __future__ import annotations
import json

from agent import CourseArchitect
from agent.provider import MockProvider

OUTLINE = """# Giving Effective Feedback
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

DROP = "The difference between feedback and criticism"   # the point we'll drop on pass 1


class FlakyWriter(MockProvider):
    """Writes the deck, but silently omits one point the first time it sees it."""
    name = "flaky-demo"

    def __init__(self, drop: str):
        super().__init__()
        self.drop = drop
        self.dropped = False

    def generate_module(self, module_plan, course_ctx, skill, prior_titles):
        slides = super().generate_module(module_plan, course_ctx, skill, prior_titles)
        if not self.dropped:
            keep = [s for s in slides if self.drop not in s.get("covers", [])]
            if len(keep) != len(slides):
                self.dropped = True          # drop it exactly once (first pass)
                return keep
        return slides


arch = CourseArchitect(provider=FlakyWriter(DROP), state_path=None, out_dir=".", verbose=True)

# Peek at coverage BEFORE any fix round: run with 0 fix rounds first (clone the flow).
print("=" * 68)
print("SELF-CORRECTION DEMO — the agent catches and fixes its own dropped point")
print("=" * 68)
report = arch.build(OUTLINE, out_name="selfcorrect_demo.pptx", max_fix_rounds=1)

# The build log above shows: draft coverage (a point missing) -> fix -> re-coverage.
result = {
    "dropped_point": DROP,
    "final_score": report.coverage_score,
    "final_missing": report.missing,
    "fix_rounds": report.fix_rounds,
    "total_bullets": report.coverage_score and round(1 / (1)),  # placeholder
}
print("\nRESULT:", json.dumps({
    "dropped_point": DROP,
    "fix_rounds": report.fix_rounds,
    "final_coverage_pct": round(report.coverage_score * 100),
    "final_missing": report.missing,
}, indent=1))
