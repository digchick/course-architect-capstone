"""LLM provider: a Gemini course-designer with a deterministic Mock fallback.

Two reasoning steps, both vibe-coded as natural-language roles:
  * `plan_course`    — an instructional designer turns the outline into a module plan.
  * `generate_module`— a slide writer turns one module into content slides (multi-turn:
                       it sees the course context and the modules already written).

With a Gemini key these are real LLM calls; without one, `MockProvider` produces a
coherent, full-coverage deck deterministically, so the notebook always runs and
always emits a real `.pptx`. (Same fallback pattern as the course starter kernel.)
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

from deck import Outline


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _short_title(text: str, max_words: int = 8) -> str:
    words = re.sub(r"\s+", " ", text.strip().rstrip(".")).split()
    t = " ".join(words[:max_words])
    return t[:1].upper() + t[1:] if t else "Overview"


def _find_api_key() -> Optional[str]:
    for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        from kaggle_secrets import UserSecretsClient  # type: ignore
        client = UserSecretsClient()
        for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            try:
                v = client.get_secret(var)
                if v:
                    return v
            except Exception:
                pass
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #
# base
# --------------------------------------------------------------------------- #

class CourseProvider:
    name = "base"

    def generate_outline(self, topic: str) -> Outline:
        """Design a full course outline from a one-line topic."""
        raise NotImplementedError

    def plan_course(self, outline: Outline, skill: str) -> Dict:
        raise NotImplementedError

    def generate_module(self, module_plan: Dict, course_ctx: Dict,
                        skill: str, prior_titles: List[str]) -> List[Dict]:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Mock — deterministic, full coverage, no key needed
# --------------------------------------------------------------------------- #

class MockProvider(CourseProvider):
    name = "mock"

    def generate_outline(self, topic: str) -> Outline:
        t = (topic or "").strip().rstrip(".").strip() or "a practical skill"
        title = t[:1].upper() + t[1:]
        return Outline(
            title=title,
            audience="Beginners",
            modules=[
                {"title": f"Getting started with {t}",
                 "bullets": [f"What {t} is and why it matters",
                             "The key terms and ideas to know",
                             "A simple first example"]},
                {"title": "Core techniques",
                 "bullets": ["The most common patterns step by step",
                             "A worked example to follow along",
                             "Common mistakes and how to avoid them"]},
                {"title": "Putting it into practice",
                 "bullets": ["A realistic end-to-end example",
                             "Tips to work faster and more accurately",
                             "Where to go next to keep improving"]},
            ])

    def plan_course(self, outline: Outline, skill: str) -> Dict:
        modules = []
        for m in outline.modules:
            bullets = m.get("bullets", [])
            modules.append({
                "title": m["title"],
                "objective": f"By the end, learners can apply {m['title'].lower()}.",
                "source_bullets": list(bullets),
                "slide_count": max(1, len(bullets)),
            })
        return {
            "subtitle": f"A practical guide for {outline.audience}",
            "theme": "corporate",
            "modules": modules,
        }

    def generate_module(self, module_plan: Dict, course_ctx: Dict,
                        skill: str, prior_titles: List[str]) -> List[Dict]:
        audience = course_ctx.get("audience", "your team")
        bullets = module_plan.get("source_bullets", [])
        slides: List[Dict] = []
        if not bullets:
            slides.append({
                "title": _short_title(module_plan["title"]),
                "bullets": ["What this module covers", "Why it matters", "How to apply it"],
                "notes": f"Introduce {module_plan['title']} for {audience}; set expectations.",
                "covers": [],
            })
            return slides
        for b in bullets:
            slides.append({
                "title": _short_title(b),
                "bullets": [
                    f"Key idea: {b}",
                    f"Why it matters for {audience}",
                    "A common pitfall to avoid",
                    "One step to apply it this week",
                ],
                "example": f"Walk through one real case of '{b}' step by step with the group.",
                "notes": (f"Explain '{b}' with a concrete example relevant to {audience}. "
                          f"Give one do and one don't, then check understanding."),
                "covers": [b],
            })
        return slides


# --------------------------------------------------------------------------- #
# Gemini
# --------------------------------------------------------------------------- #

_PLANNER_SYSTEM = """You are an expert instructional designer. You turn a short course \
outline into a structured module plan for a slide deck. Follow the provided skill \
rules, especially: build only from the given bullets, never invent new topics, and \
make sure every input bullet is assigned to a module.
OUTPUT STRICT JSON only:
{"subtitle": "...", "theme": "corporate|slate|fresh",
 "modules": [{"title": "...", "objective": "By the end, learners can ...",
 "source_bullets": ["...exact input bullets for this module..."], "slide_count": <int>}]}"""

_WRITER_SYSTEM = """You are an expert courseware writer. You turn ONE module into rich, \
teachable content slides. Follow the skill rules strictly: one idea per slide; 4-6 \
SUBSTANTIAL parallel bullets (each a complete, specific statement of ~8-16 words that \
carries real information — a rule, step, criterion or consequence — never vague labels); \
ONE concrete worked "example" per slide (a real mini-scenario, numbers, or do/don't a \
learner could try — one or two sentences); substantial speaker "notes" (3-5 sentences in \
the trainer's voice: what to say, a second example or analogy, a common mistake, a check \
question). Expand ONLY the given source bullets (do not invent new topics). In each \
slide's "covers", copy the exact source bullet text(s) that slide addresses, so coverage \
can be verified.
OUTPUT STRICT JSON only:
{"slides": [{"title": "...", "bullets": ["...", "..."], "example": "...", "notes": "...",
 "covers": ["...exact source bullet..."]}]}"""

_OUTLINE_SYSTEM = """You are an expert instructional designer. Given a short topic, \
design a practical course OUTLINE for it. Choose a clear, specific course title and a \
sensible target audience, then 4-5 modules that cover the topic end to end in a logical \
order. Each module has 4-5 concrete, teachable bullet points — real sub-topics a learner \
actually needs (e.g. for "basic Excel formulas": cell references, the SUM function, \
order of operations) — never vague filler like "introduction" or "why it matters".
OUTPUT STRICT JSON only:
{"title": "...", "audience": "...",
 "modules": [{"title": "...", "bullets": ["...specific point...", "..."]}]}"""

# Lighter models carry more generous free-tier quota. They are used as automatic
# fallbacks when the primary model is rate-limited, so a busy flagship downgrades
# to a slightly smaller *Gemini* model rather than to offline templated content.
_FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3.5-flash",
                    "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]


class GeminiProvider(CourseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: Optional[str] = None):
        from google import genai
        from google.genai import types
        self._genai = genai
        self._types = types
        self._client = genai.Client(api_key=api_key)
        # Default to a high free-tier-quota model (500 req/day) so casual use does
        # not hit the flagship's 20/day cap. Override with GEMINI_MODEL if desired.
        primary = model or os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self.models = [primary] + [m for m in _FALLBACK_MODELS if m != primary]
        self._mi = 0
        self.model_name = primary
        self.degraded = 0           # steps that still fell back to offline content
        self._mock = MockProvider()

    def generate_outline(self, topic: str) -> Outline:
        prompt = (f"TOPIC: {topic}\n\nDesign the course outline as JSON. "
                  f"Make the bullets specific to this exact topic.")
        data = self._json_call(_OUTLINE_SYSTEM, prompt, max_tokens=1200)
        if not data or not data.get("modules"):
            self.degraded += 1
            return self._mock.generate_outline(topic)
        mods = []
        for m in data["modules"]:
            bl = [str(b).strip() for b in m.get("bullets", []) if str(b).strip()]
            if bl:
                mods.append({"title": str(m.get("title", "Module")).strip()[:120],
                             "bullets": bl[:6]})
        if not mods:
            self.degraded += 1
            return self._mock.generate_outline(topic)
        return Outline(title=str(data.get("title") or topic).strip()[:120],
                       audience=str(data.get("audience") or "General audience").strip()[:120],
                       modules=mods)

    def _json_call(self, system: str, prompt: str, max_tokens: int = 2048,
                   tries_per_model: int = 2) -> Optional[Dict]:
        """One JSON-returning Gemini call. Walks the model chain on rate limits, so a
        quota-capped flagship downgrades to a lighter *Gemini* model rather than to
        offline content. Returns None only if every model is unavailable (the caller
        then uses the Mock for that one step). System prompt is per-call (new SDK)."""
        import time
        config = self._types.GenerateContentConfig(
            system_instruction=system, response_mime_type="application/json",
            temperature=0.7, max_output_tokens=max_tokens)
        last = None
        mi = self._mi
        while mi < len(self.models):
            model = self.models[mi]
            delay = 2.0
            for attempt in range(tries_per_model):
                try:
                    resp = self._client.models.generate_content(
                        model=model, contents=prompt, config=config)
                    self._mi, self.model_name = mi, model     # stick with what works
                    return json.loads(resp.text)
                except Exception as exc:
                    last, msg = exc, str(exc)
                    quota = "429" in msg or "RESOURCE_EXHAUSTED" in msg
                    busy = "503" in msg or "UNAVAILABLE" in msg
                    if quota:
                        break                                 # exhausted -> switch model
                    if busy and attempt < tries_per_model - 1:
                        print(f"    [gemini] {model} busy; retry in {delay:.0f}s")
                        time.sleep(delay); delay *= 2; continue
                    if not (quota or busy):
                        print(f"    [gemini] {model}: {type(exc).__name__}; "
                              f"offline for this step")
                        return None
            nxt = mi + 1
            if nxt < len(self.models):
                print(f"    [gemini] {model} unavailable -> trying {self.models[nxt]}")
            self._mi = mi = nxt                               # advance permanently
        print(f"    [gemini] all models rate-limited "
              f"({type(last).__name__ if last else 'n/a'}); offline for this step")
        return None

    def plan_course(self, outline: Outline, skill: str) -> Dict:
        mods = "\n".join(
            f"## {m['title']}\n" + "\n".join(f"- {b}" for b in m.get("bullets", []))
            for m in outline.modules)
        prompt = (f"SKILL:\n{skill}\n\nCOURSE TITLE: {outline.title}\n"
                  f"AUDIENCE: {outline.audience}\n\nOUTLINE:\n{mods}\n\n"
                  f"Produce the module plan as JSON.")
        data = self._json_call(_PLANNER_SYSTEM, prompt)
        if not data or "modules" not in data:
            self.degraded += 1
            return self._mock.plan_course(outline, skill)
        # Ensure every module has its source bullets (fall back to the outline's).
        for i, m in enumerate(data["modules"]):
            if not m.get("source_bullets") and i < len(outline.modules):
                m["source_bullets"] = list(outline.modules[i].get("bullets", []))
        return data

    def generate_module(self, module_plan: Dict, course_ctx: Dict,
                        skill: str, prior_titles: List[str]) -> List[Dict]:
        prior = ", ".join(prior_titles) if prior_titles else "(this is the first module)"
        src = "\n".join(f"- {b}" for b in module_plan.get("source_bullets", []))
        prompt = (f"SKILL:\n{skill}\n\nCOURSE: {course_ctx.get('title')} "
                  f"(for {course_ctx.get('audience')})\n"
                  f"MODULES ALREADY WRITTEN: {prior}\n\n"
                  f"THIS MODULE: {module_plan['title']}\n"
                  f"OBJECTIVE: {module_plan.get('objective', '')}\n"
                  f"SOURCE BULLETS:\n{src}\n\nWrite this module's slides as JSON.")
        data = self._json_call(_WRITER_SYSTEM, prompt, max_tokens=4096)
        if not data or "slides" not in data or not data["slides"]:
            self.degraded += 1
            return self._mock.generate_module(module_plan, course_ctx, skill, prior_titles)
        # Coerce shape.
        out = []
        for s in data["slides"]:
            out.append({"title": str(s.get("title", "Slide"))[:120],
                        "bullets": [str(b) for b in s.get("bullets", [])][:6],
                        "example": str(s.get("example", "")),
                        "notes": str(s.get("notes", "")),
                        "covers": [str(c) for c in s.get("covers", [])]})
        return out


# --------------------------------------------------------------------------- #
# factory
# --------------------------------------------------------------------------- #

def get_provider(force_mock: bool = False) -> CourseProvider:
    if force_mock:
        print("[provider] forced Mock course designer (deterministic, no API).")
        return MockProvider()
    key = _find_api_key()
    if not key:
        print("[provider] no GOOGLE_API_KEY/GEMINI_API_KEY → Mock course designer "
              "(deterministic). Add a key to enable Gemini-written content.")
        return MockProvider()
    try:
        import google.genai  # noqa: F401
    except Exception:
        print("[provider] google-genai not installed → Mock. "
              "`pip install google-genai` to enable Gemini.")
        return MockProvider()
    prov = GeminiProvider(api_key=key)
    print(f"[provider] Gemini course designer active (model: {prov.model_name}).")
    return prov
