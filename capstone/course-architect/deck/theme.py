"""Visual themes (branding applied *last*, to a finished content table).

Generic, clean corporate looks — deliberately NOT any real client's brand assets.
Swapping the active theme restyles the whole deck without touching content, which
is the "template + content table, brand last not first" approach from EQV.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str             # slide background (hex, no #)
    band: str           # accent band / section background
    title: str          # title text colour
    body: str           # body text colour
    muted: str          # subtitle / footer colour
    accent: str         # bullet marker / rule colour
    font_title: str = "Calibri"
    font_body: str = "Calibri"


THEMES = {
    "corporate": Theme(
        name="corporate", bg="FFFFFF", band="1F3A5F", title="1F3A5F",
        body="222831", muted="6B7280", accent="2E86C1",
        font_title="Calibri", font_body="Calibri"),
    "slate": Theme(
        name="slate", bg="0F172A", band="1E293B", title="F8FAFC",
        body="E2E8F0", muted="94A3B8", accent="38BDF8",
        font_title="Calibri", font_body="Calibri"),
    "fresh": Theme(
        name="fresh", bg="FFFFFF", band="0E7C66", title="0E7C66",
        body="1F2937", muted="6B7280", accent="F59E0B",
        font_title="Calibri", font_body="Calibri"),
}


def get_theme(name: str) -> Theme:
    return THEMES.get((name or "").lower(), THEMES["corporate"])
