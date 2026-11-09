# BUILDER_SPEC — L6 deck builder

Goal: build strong, synergistic decks that meet a set of conditions, with selectable themes, and **balance win rate against fun** with guided suggestions (§7). Win rate alone is not the objective. It sits on top of the L1 library and the L2–L4 engine (see ENGINE_SPEC.md) and automates the skill's Gates 1–10.

## 1. Inputs

```yaml
conditions:
  bracket: 3                 # 1-5; caps Game Changers, tutors, combos per bracket doctrine
  house_rules: {no_2card_infinite: true, allow_3card_combo: true, snowball_ok: true, max_gc: 3, finite_definite_kill: true}
  red_lines: from profile               # profiles/<user>.yaml is the single source (monarch, initiative, 2-card infinites, >3 GC, multi-opponent locks, mass land denial, extra-turn chains)
  budget: {max_card: null, max_total: null, currency: USD}   # optional; proxy pods use new_print_cap instead. Prices from Scryfall at pull time (data/universe.json price_usd)
  inventory: inventory/                    # collection.csv (real / printed proxy / pending) + allocations.csv (which deck each copy sits in); see §10
  new_print_cap: 20                        # max cards to print
  pod: {opponents: [Krenko, Mob Boss; Sephiroth, Fabled SOLDIER; "Y'shtola, Night's Blessed"], lists: assumed}
  must_include: [The Great Mound, Shuri's Fabricator]
  must_exclude: []
theme:                                     # any subset; empty = builder proposes
  commander: "T'Challa, the Black Panther" # or null -> commander sweep
  colours: null                            # e.g. [G, W] when no commander is fixed
  tribe_or_family: Wakanda
  resource: Vibranium                      # theme resource for the skill tree
  kill_route: null                         # voltron | wide | drain | spellslinger | combo | altwin | null = rank all
  style: null                              # e.g. "artifacts matter", "lifegain", "+1/+1 counters"
  strictness: lean                         # strict | lean | open (§7.2)
pace:                                      # how fast YOUR table ends games (§9) — presets, a number, a mix, or free text
  preset: casual                           # turbo (T4-5) | fast (T6) | mid (T8) | casual (T10) | slow (T12+) | custom
  table_median: 10                         # custom: median turn the first player wins
  spread: normal                           # tight | normal | wide
  mix: null                                # e.g. {T6: 0.3, T10: 0.7} when the pod varies night to night
  free_text: null                          # e.g. "usually over by turn 7-9, sometimes a turn-5 blowout"
balance:
  win_target: [25, 35]                     # pod win %, fair share plus an edge; above = OVERSHOOT
  win_weight: 0.6                          # 0 = all fun, 1 = all win (§7.2)
  fun_profile: profiles/seb.yaml           # weights for the fun parts (§7.1)
  pet_cards: []                            # kept unless they cost more than the noise bar
```

## 2. Pipeline (each step maps to skill gates)

| Step | Does | Skill gates |
|---|---|---|
| 1 Lock conditions | Validates inputs; resolves the pod; loads owned cards and prices | Intake, Gate 1 |
| 2 Theme and kill route | Builds the theme tree: for each kill route, which library primitives realise it on this theme. If `kill_route` is null, sketches a v0 for every viable route and runs a quick screen to rank them. With no commander, runs the commander sweep over `is:commander` within the colours/theme | Gate 2, theme tree (§5) |
| 3 Candidate pool | Library filter: colour identity, legality (every printing, strictest wins), bracket, red lines, budget. Adds the theme-name sweep, community seeds (EDHREC / public lists) and resource-map payoffs. Typical size 1,000–3,000 | Gate 3 |
| 4 Synergy graph | Nodes = candidates; edges = producer→consumer links from primitives (e.g. `token`→`sac_outlet`→`drain`, `attach`→`double strike`). Edge weight starts as the parser prior, then is updated by measured 2×2 pair interaction I (positive = complement, negative = substitute). Packages = densely linked clusters that feed the kill route | Gate 4 |
| 5 Search and simulate | Starts from v0 (role budget: lands, ramp, draw, interaction, protection, kill, engine). Local search: swap the least-synergy slot for the best candidate, simulate (paired, staged), keep it if it clears the noise bar; package swaps for clusters; land-count and utility-land sweeps; pilot policy tuning. Stops when no swap or package clears the bar in K tries, or at the escalation rule | Gates 5, 6, 9 |
| 6 Final checks | Spellbook combos (no 2-card infinites), Game Changer count, legality on every printing, who-benefits audit, singleton by oracle_id, owned vs print, budget | Gates 7, 8, 10 |

## 3. Search details
- **Objective:** disruption win-by-T12 (or pod win once calibrated), with goldfish T10 as a veto. A synergy prior breaks ties and orders candidates. The model decides, not the prior.
- **Cut rule:** remove the least-synergy card (link scan + oracle read + substitutes past peak). Role floors are never cut below the minimum.
- **Candidate order:** packages for the weakest core pair first, then theme hits and seeds, then resource-map converters, then by prior.
- **Winner's curse:** every kept swap is re-tested on fresh seeds; the final list is A/B-tested against v0 and the last shipped version on held-out seeds, and the screen→holdout shrinkage is reported.
- **Budget:** ~1,000 full-engine candidate evaluations per build; staged 500 → 2,000 → 6,000+ games; fresh seeds for every re-test; a control arm in every final comparison.
- **Theme strength:** each route reports its best-found deck. You choose the theme; the builder shows what it costs in win rate compared with the strongest route.

## 4. Outputs
- The win-vs-fun frontier and the chosen deck, plus a guided menu of 3–5 options (§7.3).
- Ranked decks (best per kill route when the route is open), each with:
  - The 100-card list with role tags, "came in for" lines, owned vs new print, rarity and price.
  - Capability line: goldfish T10 · disruption T12 · pod win (calibration status) · fun score with parts · theme fidelity · coverage · engine and parser version · ceiling.
  - Synergy map: core packages and their measured pair interactions.
  - Pilot guide (half a page) generated from the policy search.
- The workbook tab and print list (skill Gate 10).
- Results JSON in the repo under `builds/<deck>/<version>/`, with seeds, so any result can be reproduced.

## 5. Theme selection (what you can ask for)
- **By commander:** "T'Challa, best Bracket 3 deck".
- **By theme only:** "best Wakanda / elves / artifacts deck in GW", which runs a commander sweep inside the theme.
- **By route:** "drain deck under $200 for my pod".
- **By resource:** "make Vibranium the engine", which builds every kill route on that resource and ranks them.
- **By constraint:** "use only cards I own plus 15 prints".

## 6. Milestones (after ENGINE_SPEC M0–M8)

| # | Milestone | Acceptance |
|---|---|---|
| M9 | Steps 1, 3, 6 (conditions, pool, final checks) as a CLI: `build --spec spec.yaml --dry-run` | Wakanda spec gives a pool containing every v4.1 card; final checks pass on v4.1 |
| M10 | Step 4 synergy graph plus Step 5 local search | Starting from a random legal Wakanda v0, the search reaches within the noise bar of v4.1 on disruption T12 |
| M11 | Step 2 theme tree and commander sweep; budget and owned constraints | Commander ranking for GW Wakanda is stable across two fresh-seed runs (compare with the one-off sim's ranking as a consistency check, not ground truth); a budget run respects the cap |
| M12 | Second theme end to end (Lathril elves, drain/wide) | Lathril result stable across two fresh-seed runs |

## 7. Guided suggestions — balance win rate and fun (rev 2)

The builder doesn't just maximise win rate inside the stated theme. It scores every version on **win** and **fun**, keeps only the best trade-offs (the Pareto frontier), and offers a short menu of guided options. That menu includes options that break the stated theme when the trade is worth it.

### 7.1 Fun score (measured from engine game logs, not guessed)
Each part is 0–100 and has a weight in the user's **fun profile** (`profiles/<user>.yaml`). Defaults follow Seb's stated preferences.

| Part | Measured as | Default weight |
|---|---|---|
| Game length | Share of our wins in the table's sweet spot (B3: T8–T12). Wins ≤T6 count as table feel-bad; stalls past T14 are boring | 15 |
| Non-games | 100 − (mana screw + flood + mulligan-to-5 rate) | 15 |
| Line variety | Entropy of the winning line across games (which kill route, which key cards). One-line decks score low | 15 |
| Stacking moments | Games with a signature turn: a big multi-card synergy turn or a comeback from behind | 15 (Seb: synergy = stackable impact) |
| Commander and theme centrality | Share of wins where the commander or theme cards dealt or enabled most of the damage | 10 |
| Decision density | Meaningful choices per turn (castable options, attack and target choices, response windows used) | 10 |
| Interaction both ways | We answer threats and opponents can answer ours (no hard locks, no blanket hexproof walls) | 10 |
| Table health | Penalties: stax pieces, long solitaire turns (actions per turn above a cap), repeated feel-bad effects | 10 |
| Red lines | Hard filter, not a weight: monarch / initiative, 2-card infinites, more than 3 Game Changers, mass land denial, extra-turn chains | — |

**v1 shows the parts as plain descriptors only (no composite).** The composite Fun = Σ(weight × part) / Σ weights is switched on only after ≥10 rated real games (logs/games.csv) show the parts track the user's ratings; until then the weights below are placeholders. Line variety counts distinct winning routes, never inconsistency.

### 7.2 The dial
- **Win target:** default "fair share plus an edge, without overshooting". For a 4-player B3 pod that's a pod win of about 25–35%. Above that the deck is flagged OVERSHOOT (the skill's Pod-Fit verdict) and the menu offers fun-up / power-down options.
- **Balance setting:** `win_weight` 0–1 (default 0.6). The builder picks the frontier point that maximises win_weight × win_norm + (1 − win_weight) × fun, subject to the win target and red lines.
- **Theme strictness:** `strict` (only on-theme cards) · `lean` (default: up to ~10 off-theme slots if each one earns its place) · `open` (theme is a starting point only).

### 7.3 Guided suggestion types (menu of 3–5, each with measured deltas)
Every option shows: pod win Δ (± noise bar) · fun Δ with the parts that moved · theme fidelity Δ (on-theme slots) · cost / new prints · rarity.

| Type | Example wording |
|---|---|
| Relax the theme | "3 off-theme cards (Garruk's Uprising, …): +2.1 win, +6 fun (more stacking turns), theme 94% → 91%" |
| Fun swap | "Same win rate within noise, +9 fun: more lines to win (variety 41 → 58)" |
| Power swap | "+3.0 win, −7 fun (repetitive line, more T6 kills). Only if your pod is stronger" |
| Alternate route | "Same theme, wide kill instead of voltron: −1 win, +12 fun, survives wipes better" |
| Alternate commander | "Shuri at the helm: −2 win, +8 centrality" |
| Table health | "You're overshooting your pod (38%): these 2 swaps bring it to 31% and add interaction" |
| Pet-card slot | "Your pet card X costs 0.4 win (within noise). Keep it" |

Rules: a suggestion is shown only if it is on the frontier or within the noise bar of it. Suggestions never break red lines. Off-theme suggestions name what they replace and why the theme card lost (least synergy).

### 7.4 Learning the fun profile
- **Start:** a 5-question setup (pace you enjoy, how much you want to interact, combo vs combat, theme strictness, pet cards). Defaults are prefilled from Seb's known preferences.
- **After real games:** log `fun 1–5`, what felt good or bad, and who won on which turn. Each log updates the weights (simple Bayesian update of weights against the measured parts of the decks played), and the turn data feeds L5 calibration.
- **Picks count as feedback too:** when you choose a menu option over the builder's top pick, that nudges the weights.
- **Guard:** fun weights never relax red lines, and the honest win number is always shown next to the fun choice.

### 7.5 Milestones
| # | Milestone | Acceptance |
|---|---|---|
| M13 | Fun metrics from engine logs (all parts in 7.1); fun profile file | Wakanda v4.1 gets a full fun breakdown; re-runs on fresh seeds agree within 3 points per part |
| M14 | Frontier + dial + suggestion menu | For Wakanda, the menu reproduces known findings (Garruk's Uprising / Eldrazi Conscription as relax-theme options; no monarch cards ever offered) |
| M15 | Feedback loop (game logs → weights, L5 calibration) | 5 logged games change the weights in the expected direction on a test profile |

## 8. Options and free format (every setting)
Every input in §1 accepts four forms:
1. **Preset:** a named option (e.g. pace `fast`, strictness `lean`, kill route `voltron`).
2. **Number:** a custom value (e.g. `table_median: 7`, `win_weight: 0.45`).
3. **Mix:** a weighted blend when reality varies (e.g. pace `{T6: 0.3, T10: 0.7}`, or two kill routes).
4. **Free text:** plain words ("my pod is fast and swingy", "I want it to feel like Wakanda but win more", "no stax, I hate feel-bad"). The builder translates it into parameters, **echoes the parsed values back for confirmation** ("read as: pace median T7, wide spread, table-health weight +5"), and asks one question if a word is ambiguous. Free text never overrides a red line silently; a conflict is shown.

Defaults come from the user's profile; anything not given falls back to it.

## 9. Pace — adjustable game length and exploration
Games end at different turns in different pods (T4, T6, T8, T10 and beyond), and a deck tuned for one pace can be wrong for another.

- **Pace setting** (§1): a preset, a median turn, a mix, or free text. It drives:
  - **Every turn number is an offset from the pace median M:** T6 = M−4 (OVERSHOOT), T8 = M−2, T10 = M (veto), T12 = M+2 (judge), T14 = M+4 (stall / backup targets). Disruption event turns scale by M/10 (min T2); commander-out removals at round(0.3M) and round(0.5M). Acceptance tests run at M = 4 and M = 6.
  - **The table model:** the opponent agents' first-win curve, shifted and reshaped to the chosen median and spread. Calibrated from real games when logged (L5).
  - **The fun sweet spot:** pace median ± 2 turns. Wins far before it count as feel-bad.
  - **The win target:** fair share plus an edge at that pace.
- **Pace sweep (always reported, labelled approximate until opponents are real agents):** the deck's pod win at table medians T5–T12. It shows where the deck shines and where it folds, labelled **pace fit**: fast / mid / slow / all-rounder.
  - Example, Wakanda v4.1: 1.8% at T5, 3.8% T6, 7.5% T7, 13.3% T8, 21.3% T9, 31.0% T10, 41.8% T11, 52.8% T12 → a slow-pod deck. Measured 2026-11-09 by shifting the assumed pod's curve; the shape is an approximation until agents are real decks.
- **Pace exploration in the builder:**
  - Build for one pace, or **optimise across a mix** (the expected pod win over the pace distribution).
  - **Per-pace versions:** the menu (§7.3) gains "faster version" / "slower version" options. Fast pods want a lower curve, cheap interaction, earlier kills and fewer setup turns; slow pods want bigger payoffs, resilience and recursion. Each option shows the pace sweep before and after.
  - **Pace-flex slots:** a small set of swaps (e.g. 3–5 cards) to take a deck from casual to fast night without a rebuild, with the measured effect at each pace.

| # | Milestone | Acceptance |
|---|---|---|
| M16 | Pace parameter, table-curve reshaping, pace sweep report, per-pace suggestions, free-text parser for all settings with echo-back | Wakanda pace sweep reproduces the numbers above within the noise bar; "my pod usually ends turn 7" parses to median T7 and asks nothing else |

## 10. Inventory — what you have today and what you need
- **Source of truth:** `inventory/collection.csv` (card, real, proxy_printed, proxy_pending) and `inventory/allocations.csv` (deck, card). Seeded from the print-list workbook (Master "Own" rows, batch 1 = printed, batch 2 = pending) and owned precons pulled from MTGJSON (`tools/inventory.py precon WakandaForever_MSC`).
- **Every card in a build gets a status:** have (free copy) · take from another deck (names it: a conflict to resolve) · coming in the pending print batch · need to print · cheap to buy (< US$2, Scryfall price).
- **Builder cost:** a free copy costs nothing; taking one from another deck is flagged and only kept if it beats a free alternative by the noise bar; each new print counts against `new_print_cap`. Ties go to cards you already have.
- **After a build (Gate 10):** allocations move to the new list; new prints go to `proxy_pending`; when a batch arrives, `pending → printed`.
- **Reports:** `needs <deck>` (shopping / print list for one deck), `conflicts` (same copy wanted by two active decks), `spares` (copies no active deck uses — the pool future builds draw from first).
