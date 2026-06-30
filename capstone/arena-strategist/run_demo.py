"""End-to-end demo: calibrate the league, then let the agent climb it.

Runs with or without a Gemini key:
  * no key  → deterministic Mock strategist (guided hill-climb); reproducible.
  * key set → Gemini Proposer/Critic (set GOOGLE_API_KEY or GEMINI_API_KEY).

  python run_demo.py            # auto-detect provider
  python run_demo.py --mock     # force the deterministic Mock
  python run_demo.py --budget 30
"""

from __future__ import annotations

import argparse
import sys

# Keep output portable across consoles (Windows cp1252, redirected pipes, etc.).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from arena import League, Strategy
from agent import ArenaStrategist, get_provider


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="force the deterministic Mock provider")
    ap.add_argument("--budget", type=int, default=24, help="proposal rounds")
    ap.add_argument("--memory", default="arena_memory.json", help="memory file path")
    args = ap.parse_args()

    league = League()

    print("=" * 68)
    print("STEP 1 - Calibrated anchor league (the trustworthy eval)")
    print("=" * 68)
    print(league.run().table())

    print("\n" + "=" * 68)
    print("STEP 2 - Agent climbs the ladder (Proposer -> eval tool -> Critic)")
    print("=" * 68)
    provider = get_provider(force_mock=args.mock)
    agent = ArenaStrategist(provider=provider, league=league, memory_path=args.memory)
    report = agent.run(budget=args.budget)

    print("\n" + "=" * 68)
    print("STEP 3 - Verify the discovered champion in a fresh league")
    print("=" * 68)
    champ = Strategy(name="champion", genome=report.best_genome,
                     note="discovered by the Arena Strategist")
    final = league.run(extra=[champ])
    print(final.table())
    print(f"\nChampion genome: {report.best_genome}")
    print(report.headline())
    print(f"\n{agent.memory.summary()}")
    if agent.memory.falsifications:
        print("Falsifications learned:")
        for f in agent.memory.falsifications:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
