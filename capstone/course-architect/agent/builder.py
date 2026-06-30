"""The orchestrator: outline -> plan -> write modules -> assemble -> verify -> fix.

The agent loop:
  1. **Plan** (LLM): outline -> module plan (objectives, slide budget). [Day 1 vibe coding]
  2. **Write** (LLM, multi-turn): each module -> content slides, seeing the course
     context and modules already written. [Day 3 memory/state]
  3. **Assemble** (tool): render the deck to .pptx. [Day 2 tools/MCP]
  4. **Verify** (tool): coverage check — did every input bullet land on a slide? [Day 4 eval]
  5. **Self-correct**: regenerate the modules that dropped bullets, then re-verify.
The model produces all content; code only assembles and checks. [Day 5 production]
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from deck import Outline, parse_outline

from .memory import CourseState
from .provider import CourseProvider, get_provider
from .tools import CourseToolServer

_SKILL_PATH = os.path.join(os.path.dirname(__file__), "skills", "instructional_design.md")


def _load_skill() -> str:
    try:
        with open(_SKILL_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return "(skill file unavailable)"


def _outline_dict(o: Outline) -> Dict:
    return {"title": o.title, "audience": o.audience, "modules": o.modules}


@dataclass
class BuildReport:
    title: str
    provider: str
    theme: str
    modules: int
    content_slides: int
    total_slides: int
    coverage_score: float
    missing: List[str]
    out_path: str
    tool_calls: int
    fix_rounds: int
    log: List[str] = field(default_factory=list)

    def headline(self) -> str:
        cov = f"{self.coverage_score:.0%} coverage"
        gap = "all bullets covered" if not self.missing else f"{len(self.missing)} bullet(s) still missing"
        return (f"{self.provider} built '{self.title}': {self.total_slides} slides "
                f"({self.content_slides} content) across {self.modules} modules, "
                f"{cov} ({gap}). Saved to {self.out_path}.")


class CourseArchitect:
    def __init__(self, provider: Optional[CourseProvider] = None, theme: Optional[str] = None,
                 state_path: Optional[str] = None, out_dir: str = ".", verbose: bool = True):
        self.provider = provider or get_provider()
        self.theme_override = theme
        self.tools = CourseToolServer(out_dir=out_dir)
        self.state = CourseState(state_path)
        self.skill = _load_skill()
        self.verbose = verbose
        self.log: List[str] = []

    def _log(self, msg: str) -> None:
        self.log.append(msg)
        if self.verbose:
            print(msg)

    def build(self, outline_text: str, out_name: str = "course.pptx",
              max_fix_rounds: int = 1) -> BuildReport:
        # If the input gives no "## module" headings, treat it as a plain-English
        # topic and let the agent DESIGN the outline before writing the content.
        has_modules = any(l.strip().startswith("## ") for l in outline_text.splitlines())
        if has_modules:
            outline = parse_outline(outline_text)
        else:
            topic = self._extract_topic(outline_text)
            self._log(f"[outline] no sections supplied — {self.provider.name} is "
                      f"designing the outline for: {topic!r}")
            outline = self.provider.generate_outline(topic)
        self._log(f"[plan] '{outline.title}' for {outline.audience} — "
                  f"{len(outline.modules)} modules, {len(outline.all_bullets())} bullets")

        # 1. Plan
        plan = self.provider.plan_course(outline, self.skill)
        self.state.set_plan(plan, outline.title, outline.audience)
        if self.theme_override:
            self.state.theme = self.theme_override
        self._log(f"[plan] {self.provider.name} -> {len(plan.get('modules', []))} modules, "
                  f"theme '{self.state.theme}'")

        # 2. Write each module (multi-turn: pass titles already written)
        ctx = {"title": self.state.title, "audience": self.state.audience,
               "subtitle": self.state.subtitle}
        for m in plan.get("modules", []):
            slides = self.provider.generate_module(m, ctx, self.skill,
                                                   self.state.done_module_titles())
            self.state.set_module(m["title"], slides)
            self._log(f"[write] {m['title']} -> {len(slides)} slides")

        # 3 + 4. Assemble + verify coverage
        coverage = self._verify(outline)
        self._log(f"[eval] coverage {coverage['score']:.0%} "
                  f"({coverage['covered']}/{coverage['total_bullets']} bullets)")

        # 5. Self-correct dropped bullets
        fixes = 0
        while coverage["missing"] and fixes < max_fix_rounds:
            fixes += 1
            self._fix_missing(coverage["missing"], ctx)
            coverage = self._verify(outline)
            self._log(f"[fix {fixes}] re-coverage {coverage['score']:.0%} "
                      f"({len(coverage['missing'])} missing)")

        # Final assemble via the tool
        deck = self.state.deck_spec()
        res = self.tools.call_tool("assemble_deck",
                                   {"deck": deck.to_dict(), "out_path": out_name})
        self.state.coverage = coverage
        self.state.save()

        report = BuildReport(
            title=self.state.title, provider=self.provider.name, theme=self.state.theme,
            modules=len(deck.sections), content_slides=res["content_slides"],
            total_slides=res["slides"], coverage_score=coverage["score"],
            missing=coverage["missing"], out_path=res["path"],
            tool_calls=len(self.tools.call_log), fix_rounds=fixes, log=list(self.log))
        self._log("\n" + report.headline())
        return report

    # -- internals ---------------------------------------------------------- #
    @staticmethod
    def _extract_topic(text: str) -> str:
        """Pull a plain-English topic out of free text (ignoring template hints,
        markdown markers and an 'Audience:' line)."""
        parts: List[str] = []
        for raw in text.splitlines():
            s = raw.strip()
            if not s:
                continue
            if s.startswith("(") and s.endswith(")"):   # template hint line
                continue
            if s.lower().startswith("audience:"):
                continue
            s = s.lstrip("#-*• ").strip()                # drop md markers
            if s:
                parts.append(s)
        return " ".join(parts).strip() or "a useful introductory course"

    def _verify(self, outline: Outline) -> Dict:
        deck = self.state.deck_spec()
        return self.tools.call_tool("check_coverage",
                                    {"outline": _outline_dict(outline), "deck": deck.to_dict()})

    def _fix_missing(self, missing: List[str], ctx: Dict) -> None:
        """Regenerate, per owning module, slides for the bullets that got dropped, and
        append them — using the provider (never code) to produce the content."""
        missing_set = set(missing)
        for m in self.state.plan.get("modules", []):
            owned = [b for b in m.get("source_bullets", []) if b in missing_set]
            if not owned:
                continue
            synthetic = {"title": m["title"], "objective": m.get("objective", ""),
                         "source_bullets": owned}
            extra = self.provider.generate_module(synthetic, ctx, self.skill,
                                                  self.state.done_module_titles())
            self.state.modules[m["title"]] = self.state.modules.get(m["title"], []) + extra
        self.state.save()
