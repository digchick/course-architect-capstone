"""Course Architect — the capstone agent.

A vibe-coded, tool-using agent that turns a short outline into a finished, branded
PowerPoint course. Maps to the 5 course days:
  * provider  — Gemini planner + slide-writer, with a no-key Mock fallback   (D1 vibe coding)
  * tools     — MCP-style assemble_deck / check_coverage                     (D2 tools/MCP)
  * memory    — course state across a multi-turn, module-by-module build     (D3 skills/memory)
  * builder   — coverage self-check drives self-correction                   (D4 quality/eval)
  * run_demo  — reproducible, observable, graceful-degradation run           (D5 production)
"""

from .provider import get_provider, CourseProvider, MockProvider, GeminiProvider
from .memory import CourseState
from .tools import CourseToolServer
from .builder import CourseArchitect, BuildReport

__all__ = [
    "get_provider", "CourseProvider", "MockProvider", "GeminiProvider",
    "CourseState", "CourseToolServer", "CourseArchitect", "BuildReport",
]
