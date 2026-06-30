"""An MCP-style tool surface for the agent (course Day-2: tools & MCP).

The agent reasons (plan, write) via the LLM provider, but every *action* on the
world goes through these schema-typed tools — build the deck file, and check
coverage — with a `list_tools()` / `call_tool()` dispatcher and a logged call
history, the same shape as a real Model Context Protocol server.
"""

from __future__ import annotations

import os
from typing import Dict, List

from deck import DeckSpec, Outline, THEMES, assemble_pptx, coverage_report, get_theme


class CourseToolServer:
    def __init__(self, out_dir: str = "."):
        self.out_dir = out_dir
        self.call_log: List[Dict] = []

    def list_tools(self) -> List[Dict]:
        return [
            {"name": "assemble_deck",
             "description": "Render a DeckSpec to a .pptx file with the chosen theme. "
                            "Pure layout — adds no content of its own.",
             "inputSchema": {"type": "object",
                             "properties": {"deck": {"type": "object"},
                                            "out_path": {"type": "string"}},
                             "required": ["deck", "out_path"]}},
            {"name": "check_coverage",
             "description": "Verify every input outline bullet is represented on a slide. "
                            "Returns score, covered count, and any missing bullets.",
             "inputSchema": {"type": "object",
                             "properties": {"outline": {"type": "object"},
                                            "deck": {"type": "object"}},
                             "required": ["outline", "deck"]}},
            {"name": "list_themes",
             "description": "List available visual themes.",
             "inputSchema": {"type": "object", "properties": {}}},
        ]

    def call_tool(self, name: str, arguments: Dict) -> Dict:
        self.call_log.append({"tool": name, "arguments_keys": list(arguments.keys())})
        if name == "assemble_deck":
            return self._assemble(arguments["deck"], arguments["out_path"])
        if name == "check_coverage":
            return self._coverage(arguments["outline"], arguments["deck"])
        if name == "list_themes":
            return {"themes": list(THEMES.keys())}
        raise ValueError(f"unknown tool: {name}")

    # -- implementations ---------------------------------------------------- #
    def _assemble(self, deck_dict: Dict, out_path: str) -> Dict:
        deck = DeckSpec.from_dict(deck_dict)
        path = out_path if os.path.isabs(out_path) else os.path.join(self.out_dir, out_path)
        assemble_pptx(deck, path, get_theme(deck.theme))
        return {"path": path, "slides": deck.content_slide_count() + len(deck.sections) + 2,
                "content_slides": deck.content_slide_count(), "theme": deck.theme}

    def _coverage(self, outline_dict: Dict, deck_dict: Dict) -> Dict:
        outline = Outline(title=outline_dict.get("title", ""),
                          audience=outline_dict.get("audience", ""),
                          modules=outline_dict.get("modules", []))
        return coverage_report(outline, DeckSpec.from_dict(deck_dict))
