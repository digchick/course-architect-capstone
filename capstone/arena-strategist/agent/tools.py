"""An MCP-style tool server wrapping the arena (course Day 2: tools & MCP).

The agent never touches the simulator directly — it acts only through this tool
surface, exactly the discipline the Model Context Protocol encourages: a small set
of well-described, schema-typed tools, a `list_tools()` (MCP `tools/list`) and a
`call_tool()` (MCP `tools/call`) dispatcher, and a log of every call for
observability. Swapping this class for a real `mcp` stdio server is mechanical —
the schemas are already in MCP shape.
"""

from __future__ import annotations

from typing import Dict, List

from arena.league import League
from arena.sim import GENOME_KEYS, Strategy

_GENOME_PROPERTIES = {
    "mine": {"type": "number", "description": "priority for MINE (+3 ore)"},
    "build": {"type": "number", "description": "priority for BUILD (-3 ore, +1 ship)"},
    "expand": {"type": "number", "description": "priority for EXPAND (-5 ore, +1 base)"},
    "fortify": {"type": "number", "description": "priority for FORTIFY (-2 ore, +1 shield)"},
    "raid": {"type": "number", "description": "per-ship priority for RAID"},
    "raid_threshold": {"type": "integer", "description": "min ships before raiding (1-20)"},
    "expand_late_bonus": {"type": "number", "description": "EXPAND grows toward endgame (0-5)"},
    "fortify_threat_scale": {"type": "number", "description": "FORTIFY grows with enemy fleet (0-2)"},
}


class ArenaToolServer:
    def __init__(self, league: League | None = None):
        self.league = league or League()
        self.call_log: List[Dict] = []

    # -- MCP surface -------------------------------------------------------- #
    def list_tools(self) -> List[Dict]:
        genome_schema = {"type": "object", "properties": _GENOME_PROPERTIES}
        return [
            {
                "name": "evaluate_strategy",
                "description": "Run a strategy genome through the calibrated Elo "
                               "league against all anchors. Returns elo, rank, "
                               "win-rate vs the top anchor, and whether it beats it.",
                "inputSchema": {"type": "object",
                                "properties": {"genome": genome_schema},
                                "required": ["genome"]},
            },
            {
                "name": "simulate_match",
                "description": "Play a genome head-to-head against one named anchor "
                               "across the map pool. Returns wins/draws/losses.",
                "inputSchema": {"type": "object",
                                "properties": {"genome": genome_schema,
                                               "opponent": {"type": "string"}},
                                "required": ["genome", "opponent"]},
            },
            {
                "name": "list_anchors",
                "description": "List the calibrated anchor ladder with Elo and notes.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def call_tool(self, name: str, arguments: Dict) -> Dict:
        self.call_log.append({"tool": name, "arguments": arguments})
        if name == "evaluate_strategy":
            return self._evaluate(arguments["genome"], arguments.get("name", "candidate"))
        if name == "simulate_match":
            return self._simulate(arguments["genome"], arguments["opponent"])
        if name == "list_anchors":
            return self._list_anchors()
        raise ValueError(f"unknown tool: {name}")

    # -- implementations ---------------------------------------------------- #
    def _evaluate(self, genome: Dict, name: str = "candidate") -> Dict:
        cand = Strategy(name=name, genome={k: genome[k] for k in genome if k in GENOME_KEYS})
        return self.league.evaluate_candidate(cand)

    def _simulate(self, genome: Dict, opponent: str) -> Dict:
        from arena.sim import play_match
        cand = Strategy(name="candidate", genome=genome)
        opp = next((a for a in self.league.anchors if a.name == opponent), None)
        if opp is None:
            return {"error": f"no such anchor '{opponent}'",
                    "anchors": [a.name for a in self.league.anchors]}
        wa, dr, wb = play_match(cand, opp, self.league.pool)
        return {"opponent": opponent, "wins": wa, "draws": dr, "losses": wb,
                "games": wa + dr + wb}

    def _list_anchors(self) -> Dict:
        res = self.league.run()
        return {"anchors": [
            {"name": a.name, "elo": round(res.elo[a.name], 1), "note": a.note}
            for a in sorted(self.league.anchors, key=lambda s: -res.elo[s.name])]}

    # -- convenience for the orchestrator ----------------------------------- #
    def anchor_summary(self) -> List[Dict]:
        return self._list_anchors()["anchors"]
