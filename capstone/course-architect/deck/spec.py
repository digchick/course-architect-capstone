"""The content contract: outline in, deck spec out, plus a coverage evaluator.

* `Outline`   — the short input the user provides (title, audience, modules+bullets).
* `DeckSpec`  — the full deck the agent produces (sections of slides). Code assembles
                this verbatim; it never adds content of its own.
* `coverage_report` — the agent's objective self-check: did every input bullet make it
                onto a slide? This enforces the EQV rule "cover ONLY the bullets given"
                and is the Day-4 evaluation signal that drives self-correction.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List


# --------------------------------------------------------------------------- #
# Input outline
# --------------------------------------------------------------------------- #

@dataclass
class Outline:
    title: str
    audience: str
    modules: List[Dict]  # [{"title": str, "bullets": [str]}]

    def all_bullets(self) -> List[str]:
        out: List[str] = []
        for m in self.modules:
            out.extend(m.get("bullets", []))
        return out


def parse_outline(text: str) -> Outline:
    """Parse a tiny markdown-ish outline. Format:

        # Course Title
        Audience: Frontline managers (beginner)
        ## Module One Title
        - first point
        - second point
        ## Module Two Title
        - ...
    """
    title, audience = "Untitled Course", "General audience"
    modules: List[Dict] = []
    current: Dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("## "):
            current = {"title": line[3:].strip(), "bullets": []}
            modules.append(current)
        elif line.startswith("# "):
            title = line[2:].strip()
        elif re.match(r"(?i)^audience\s*:", line):
            audience = line.split(":", 1)[1].strip()
        elif line.lstrip().startswith(("-", "*", "•")):
            bullet = line.lstrip()[1:].strip()
            if bullet and current is not None:
                current["bullets"].append(bullet)
        # bare lines before any module are ignored (e.g. a description)
    if not modules:
        # Fall back: treat every bullet/line as a single module.
        modules = [{"title": title, "bullets":
                    [l.strip("-*• ").strip() for l in text.splitlines()
                     if l.strip() and not l.startswith("#")]}]
    return Outline(title=title, audience=audience, modules=modules)


# --------------------------------------------------------------------------- #
# Output deck
# --------------------------------------------------------------------------- #

@dataclass
class Slide:
    title: str
    bullets: List[str] = field(default_factory=list)
    notes: str = ""                       # speaker notes
    example: str = ""                     # one concrete worked example (rendered in a box)
    covers: List[str] = field(default_factory=list)  # which input bullets this slide addresses


@dataclass
class Section:
    module_title: str
    objective: str = ""
    slides: List[Slide] = field(default_factory=list)


@dataclass
class DeckSpec:
    title: str
    subtitle: str = ""
    audience: str = ""
    theme: str = "corporate"
    sections: List[Section] = field(default_factory=list)

    # -- (de)serialisation for memory + LLM JSON --------------------------- #
    def to_dict(self) -> Dict:
        return {
            "title": self.title, "subtitle": self.subtitle,
            "audience": self.audience, "theme": self.theme,
            "sections": [
                {"module_title": s.module_title, "objective": s.objective,
                 "slides": [asdict(sl) for sl in s.slides]}
                for s in self.sections],
        }

    @staticmethod
    def from_dict(d: Dict) -> "DeckSpec":
        sections = []
        for s in d.get("sections", []):
            slides = [Slide(title=sl.get("title", ""),
                            bullets=list(sl.get("bullets", [])),
                            notes=sl.get("notes", ""),
                            example=sl.get("example", ""),
                            covers=list(sl.get("covers", [])))
                      for sl in s.get("slides", [])]
            sections.append(Section(module_title=s.get("module_title", ""),
                                    objective=s.get("objective", ""), slides=slides))
        return DeckSpec(title=d.get("title", "Untitled"), subtitle=d.get("subtitle", ""),
                        audience=d.get("audience", ""), theme=d.get("theme", "corporate"),
                        sections=sections)

    def content_slide_count(self) -> int:
        return sum(len(s.slides) for s in self.sections)


# --------------------------------------------------------------------------- #
# Coverage evaluation (the self-check)
# --------------------------------------------------------------------------- #

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _tokens(s: str) -> set:
    return set(_norm(s).split())


def coverage_report(outline: Outline, deck: DeckSpec) -> Dict:
    """Was every input bullet represented on a slide?

    A bullet counts as covered if it's listed in a slide's `covers`, or if a slide's
    title/bullets overlap it strongly (token Jaccard >= 0.5) — so we don't punish the
    model for paraphrasing while still catching genuinely dropped material.
    """
    # Gather all slide text + explicit covers.
    explicit = set()
    slide_blobs: List[set] = []
    for sec in deck.sections:
        for sl in sec.slides:
            for c in sl.covers:
                explicit.add(_norm(c))
            slide_blobs.append(_tokens(sl.title + " " + " ".join(sl.bullets)))

    per_bullet: Dict[str, bool] = {}
    missing: List[str] = []
    for bullet in outline.all_bullets():
        nb = _norm(bullet)
        covered = nb in explicit
        if not covered:
            bt = _tokens(bullet)
            if bt:
                for blob in slide_blobs:
                    inter = len(bt & blob)
                    union = len(bt | blob) or 1
                    if inter / union >= 0.5 or (len(bt) >= 2 and bt <= blob):
                        covered = True
                        break
        per_bullet[bullet] = covered
        if not covered:
            missing.append(bullet)

    total = len(per_bullet)
    covered_n = total - len(missing)
    return {
        "total_bullets": total,
        "covered": covered_n,
        "missing": missing,
        "score": round(covered_n / total, 3) if total else 1.0,
        "per_bullet": per_bullet,
    }
