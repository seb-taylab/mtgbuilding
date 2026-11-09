# mtg-engine

Shared Commander engine for the `mtg-deck-architect` skill (§8 Universe roadmap).
One card-effect library, one engine, growing with every build. Every session loads this repo first and pushes additions at Gate 10.

| Path | What |
|---|---|
| `data/universe.json` | Every Commander-legal card, one record per `oracle_id` (Scryfall `legal:commander`). Re-pull with `tools/pull_universe.py` |
| `library/parse.py` | L1 parser: oracle text → effect primitives. Strips reminder text; rejects tribe-only, conditional and until-end-of-turn static matches |
| `library/cardlib.json` | L1 library output: `oracle_id → {name, ci, type, mv, prims, conf, parser}` |
| `library/hand.json` | Hand-verified records (never overwritten by the parser) — create as cards are verified |
| `library/coverage.txt` | Last parser run: coverage and class counts |
| `engine/HANDLERS.md` | Primitive → engine handler status |
| `engine/oneoff_wakanda/` | Stopgap one-off sim (Wakanda voltron). Its card code is to be ported into the library + generic engine (L2) |
| `regression/` | Regression decks, seeds and expected results. Every engine change re-runs them |
| `tools/pull_universe.py` · `library/parse.py` | Regenerate the card data and library (not committed) |
| `tools/decklist.py` | Import / export decklists (text, Moxfield/Archidekt text, CSV, proxy list) |
| `tools/inventory.py` | What you own (real / printed proxy / pending), where each copy is, and what a deck still needs (`needs`, `conflicts`, `spares`, `precon`, `add`) |
| `tools/check_all.py` | Health check for every deck (Gates 7–8); run after each B&R / GC update / set release |
| `tools/check_constants.py` | Flags drift between the profile and the specs/tools |
| `decks/` `owned/` `pods/` `logs/` `profiles/` | Decklists, collection, pod files, game log, fun/house profile |
| `engine/oneoff_wakanda/reproduce.py` | Exact-seed Wakanda regression numbers |

Status: see `ROADMAP.md`.

## First run (Claude Code)
```
python3 tools/pull_universe.py      # ~3 min, writes data/universe.json + universe_meta.json
python3 library/parse.py            # writes library/cardlib.json, prints coverage
python3 tools/check_all.py --combos # health check every deck
python3 engine/oneoff_wakanda/reproduce.py   # regression numbers
```
