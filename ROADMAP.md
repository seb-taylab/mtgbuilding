# Roadmap status — 2026-11-09

Universe: **32,643** Commander-legal cards (31,408 non-land, 1,223 non-basic lands).

| Layer | Done when | Status |
|---|---|---|
| L1 Card-effect library | **Non-land cards playable ≥70%**: ≥1 handler-backed primitive from a class that passed its 20-card spot-check (tags, keyword-only bodies and lands don't count); full clause-level coverage measured once L2 handlers exist | **Parser 1.6: 18,133 / 31,146 = 58.2% playable ❌ (bar not met).** Any tag or effect: 63.5%. Lands: 1,132 mana-coded, 372 with a utility effect. Per-face modes for 840+ multi-face cards. Classes still failing the spot-check (coded, not counted): tapper (~17%), doubler (static/triggered param), counters (~8%), self_recursion (~25%). The old 71% figure counted tags and lands — retired |
| L2 Generic engine | Reproduces every regression deck within the noise bar | Not started. Stopgap: `engine/oneoff_wakanda` |
| L3 Win-route modules | Voltron · tokens · drain · spellslinger · combo · alt-win | Voltron (one-off) |
| L4 Opponent agents | Pod win from agents | Archetype curves (`opp_sim.py`); removal unvalued |
| L5 Calibration | Pod `calibrated` = real lists + ≥20 logged games (statuses: assumed / partial / calibrated) | **assumed** (EDHREC lists); logs/games.csv ready |
| L6 Deck builder | Builds the best deck for given conditions + theme (BUILDER_SPEC.md) | Designed; manual today via the skill's gates |

## Next steps (demand-driven)
1. Spot-check the remaining classes (20 random cards each); fix any class above 5% false positives.
2. L2: generic engine core (mana, mulligan, draw, casting, combat, commander rules) plus handlers for the primitives Wakanda uses. Port the one-off card code into the library as plug-ins. Gate: Wakanda v4.1 reproduces within the noise bar.
3. L3 / L4 with the next deck: Lathril (black: tokens, drain, sacrifice) brings the go-wide and drain modules and the first opponent agents.

## L1 spot-check log (parser 1.2–1.5, 2026-11-09; ~20 random cards per class)

| Class | Result | Fix |
|---|---|---|
| removal | ~0/10 after fix | 1.1: graveyard-card exile excluded; 1.4: "nonblack" etc. adjectives |
| tutor | 3/10 → ~1/10 | 1.1: basic-land searches excluded, named-card and to-graveyard tutors tagged |
| phase | 8/20 → 1/7 | 1.2: only phasing of your own permanents; phasing keyword drawbacks excluded |
| grant | 4/20 → ~1/20 | 1.2: conditions (as long as, graveyard, kicked, max speed), land/token creatures excluded |
| anthem | 2/20 → ~1/20 | 1.2: planeswalker loyalty lines and +0 boosts excluded |
| alt_win | 3/20 → ~1/20 | 1.2: "when a player loses the game" payoffs excluded |
| stax | 4/20 one-shots → permanents only | 1.2 |
| flag_monarch | ~3/20 → 0 | 1.2: requires becoming the monarch / taking the initiative |
| reducer | scope missing | 1.2: scope + amount recorded (tribal, colour, type, equip) |
| lifegain, regenerate, protect, draw_spell, attach, extra_combat, counterspell, sac_outlet, ritual, rock, burn, drain, token, ramp | ≤1/20 | — |
| doubler, copy, counters, flicker | ~2/20 (loose) | watch; tighten when a deck depends on them |
| trigger tags (cast/etb/attack/death/combat-damage) | ≤2/20 | tags, 10% bar |
| Known parser misses | "you and target opponent each draw" counted as our draw (Secret Rendezvous) | add a who-benefits field in 1.6 |

## Independent audit, 2026-11-09 (fixed in ENGINE_SPEC rev 2 and parser 1.6)
- Blockers fixed: multiplayer first draw (CR 103.8c, house flag for the one-off sim); M3/M4 reproducibility (`abstract_table` profile, M3a faithful port then M3b explained deltas, unpaired noise bar); per-face parsing; keywords from Scryfall's field (menace/hexproof/flying misses).
- Major fixed: commander to command zone is an SBA from graveyard/exile (903.9a); all doublers stack; vehicles, monarch/initiative, archenemy formula, gift modifier, `pod_win`, `kill_pieces`, cmdout turns, London mulligan; missing SBAs; parser recursion/tapper/bounce/doubler/copy/wipe fixes; read-only sampling; honest coverage metric.
- Minor fixed: citations (702.19b + 702.2c, 514.1, layer 7a–7d, APNAP order, hexproof player vs edicts), milestone test assignment, performance target after profiling, PYTHONHASHSEED.
- Open: agadeem/shatterskull-style front faces still miss ("return from your graveyard … any number of target"; "divided among"); tapper/doubler/counters/self_recursion need another pass; who-benefits field.

## Holistic audit, 2026-11-09 (fixed in skill v5.13 and this repo)
- Reproducible: the one-off sim is self-contained (`engine/oneoff_wakanda/`, relative paths), `reproduce.py` gives exact-seed numbers (goldfish T10 82.6, disrupt T12 85.0, pod T12 73.7, pod win 31.3). Earlier "disruption T12 72.8" was the pod profile; relabelled.
- Lifecycle: `tools/decklist.py` (import/export/proxies), `tools/check_all.py` (Gates 7–8 incl. commander pairs, Spellbook 2-card infinites), `decks/`, `owned/`, `pods/`, `logs/games.csv`. Card data now records pull date, price and per-card text hash (errata trigger re-parse). Big data files are regenerated, not committed.
- Skill: three tiers (Quick/Tune/Full), pace offsets for every turn number, calibration statuses with ≥20 games, winner's-curse re-tests + holdout, fun descriptors until validated, commander pair/companion/bracket checks, 5-line layman summary first.
- Open: push to GitHub (repo must be created by Seb); record official bracket definitions with verified date in pods/seb_pod.yaml; beneficiary field (parser 1.7); real opponent lists.
