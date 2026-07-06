"""Course state — the agent's working memory across a multi-turn build.

The deck is built module-by-module, and each module's generation sees the course
context and the modules already done (course Day-3 memory/state). This object holds
that growing state and can render it to a `DeckSpec` for assembly at any point. It
also persists to JSON so a build can be inspected or resumed.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from deck import DeckSpec, Section, Slide


class CourseState:
    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.title: str = "Untitled Course"
        self.subtitle: str = ""
        self.audience: str = ""
        self.theme: str = "corporate"
        self.plan: Dict = {}                       # {modules: [{title, objective, source_bullets, slide_count}]}
        self.modules: Dict[str, List[Dict]] = {}   # module_title -> [slide dicts]
        self.coverage: Dict = {}
        self.log: List[str] = []
        if path and os.path.exists(path):
            self.load()

    # -- building blocks ---------------------------------------------------- #
    def set_plan(self, plan: Dict, title: str, audience: str) -> None:
        self.plan = plan
        self.title = title
        self.audience = audience
        self.subtitle = plan.get("subtitle", "") or f"A practical guide for {audience}"
        self.theme = plan.get("theme", self.theme)
        self.save()

    def set_module(self, module_title: str, slides: List[Dict]) -> None:
        self.modules[module_title] = slides
        self.save()

    def done_module_titles(self) -> List[str]:
        return list(self.modules.keys())

    def deck_spec(self) -> DeckSpec:
        sections: List[Section] = []
        for m in self.plan.get("modules", []):
            mt = m["title"]
            slides = [Slide(title=s.get("title", ""), bullets=list(s.get("bullets", [])),
                            notes=s.get("notes", ""), example=s.get("example", ""),
                            covers=list(s.get("covers", [])))
                      for s in self.modules.get(mt, [])]
            sections.append(Section(module_title=mt, objective=m.get("objective", ""),
                                    slides=slides))
        return DeckSpec(title=self.title, subtitle=self.subtitle, audience=self.audience,
                        theme=self.theme, sections=sections)

    # -- persistence -------------------------------------------------------- #
    def save(self) -> None:
        if not self.path:
            return
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"title": self.title, "subtitle": self.subtitle,
                       "audience": self.audience, "theme": self.theme,
                       "plan": self.plan, "modules": self.modules,
                       "coverage": self.coverage, "log": self.log}, f, indent=2)

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            d = json.load(f)
        self.__dict__.update({k: d.get(k, getattr(self, k)) for k in
                              ("title", "subtitle", "audience", "theme",
                               "plan", "modules", "coverage", "log")})
