"""Course Architect — deck domain layer.

The *content contract* between the agent and the file it produces. The agent (LLM)
generates a `DeckSpec`; the assembler turns it into a real `.pptx`. This separation
is the hard-won EQV production lesson: **the model produces all the content; code
only assembles it** — code never invents slide text.
"""

from .spec import (
    Slide, Section, DeckSpec, Outline,
    parse_outline, coverage_report,
)
from .theme import THEMES, get_theme, Theme
from .assembler import assemble_pptx

__all__ = [
    "Slide", "Section", "DeckSpec", "Outline",
    "parse_outline", "coverage_report",
    "THEMES", "get_theme", "Theme",
    "assemble_pptx",
]
