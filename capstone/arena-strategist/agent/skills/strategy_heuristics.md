# Skill: Orbital Skirmish strategy heuristics

Distilled domain knowledge the Proposer loads as context before designing a genome.
A *skill* is just reusable, versioned expertise injected at the right moment — the
course Day-3 idea. These heuristics were learned by watching the calibrated league.

## How the game pays out
- **Bases are the only victory points.** You must EXPAND to win; pure economy draws 0–0.
- **Bases are fragile.** An undefended expander bleeds bases to any standing fleet
  (each net attacking ship destroys one base, every turn). Expansion without defence
  is the classic losing line (`greedy_expander`).
- **Defence is cheap and permanent.** A shield (cost 2) permanently blocks one
  attacking ship. Keeping `shields ≥ enemy fleet` makes you raid-proof.
- **Offence needs an economy.** Raiders with no mining (`all_in_raider`) run out of
  ore and stall; their fleet bounces off a fortified opponent.

## What tends to win
1. **Economy first, expand late.** Mine to a healthy ore bank, then convert to bases
   in the back half (`expand_late_bonus` 0.8–1.5).
2. **Reactive defence.** Don't over-fortify blindly; scale fortification to the
   opponent's fleet (`fortify_threat_scale` 0.5–1.0) so shields track the real threat.
3. **A credible deterrent, not all-in.** Keep `raid` priority moderate and
   `raid_threshold` low-ish (3–5) so you punish undefended expanders without
   starving your own economy.
4. **Balance beats extremes.** Every anchor that maxes one knob sits low on the
   ladder. The top anchor (`adaptive`) is balanced + situational.

## Falsified lines (don't re-propose — wasted budget)
- mine-only / build-only: never scores, bottom of the ladder.
- expand-max with zero fortify: punished hard by any fleet.
- raid-max with zero economy: stalls; loses to anyone who fortifies.

> Methodology note: these are *hypotheses ranked by the league*, not gospel. Always
> trust the Elo number over the heuristic — the calibrated eval is the ground truth.
