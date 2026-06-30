"""Arena Strategist — the capstone agent.

A vibe-coded, tool-using, multi-agent system that discovers winning strategies
for a competitive simulation by optimising against a *calibrated league* — the
same eval-driven methodology that took us to silver (top 5%) in the Orbit Wars
Kaggle competition.

Layers (mapping to the 5 course days):
  * provider   — Gemini-backed Proposer/Critic, with a no-API-key Mock fallback   (D1 vibe coding)
  * tools      — an MCP-style tool server wrapping the arena + league             (D2 tools/MCP)
  * memory     — persistent strategy store + falsification log                    (D3 skills/memory)
  * strategist — orchestration loop with self-correction; the league is the eval  (D4 quality/eval)
  * run_demo   — reproducible, observable end-to-end run                          (D5 production)
"""

from .provider import get_provider, StrategyProvider, MockProvider, GeminiProvider
from .memory import StrategyMemory
from .tools import ArenaToolServer
from .strategist import ArenaStrategist, RunReport

__all__ = [
    "get_provider",
    "StrategyProvider",
    "MockProvider",
    "GeminiProvider",
    "StrategyMemory",
    "ArenaToolServer",
    "ArenaStrategist",
    "RunReport",
]
