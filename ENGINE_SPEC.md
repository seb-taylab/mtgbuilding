# ENGINE_SPEC — generic Commander engine (L2–L4)

Status: design rev 2, 2026-11-09 (after independent audit; changes marked rev2). Owner skill: `mtg-deck-architect` §8. Build it in the order in §10. Each milestone has an acceptance test, and nothing moves on until the test passes.

## 1. Purpose and non-goals

**Purpose:** a Monte Carlo simulator of 4-player Commander games that is good enough to *compare deck versions*. It answers "does swap X make this deck win faster or more often against this pod?", with paired seeds and a noise bar.

**Non-goals:**
- It is not a full rules engine or a rules judge (the `mtg-judge` skill does that).
- No priority-perfect stack, no layer-perfect continuous effects beyond §4, no politics deals, no hidden-information bluffing.

**Every simplification is written down (§4).** A card that depends on an unmodelled rule is flagged `unmodelled`, and its screen result is suppressed. It never gets a number.

## 2. Architecture

```
engine/
  state.py      GameState, Player, Permanent, zones, event log
  cards.py      loads library/cardlib.json + library/hand.json (plug-ins); Card view by oracle_id
  mana.py       sources, colours, restrictions, cost solver, reducers, tax
  turn.py       turn structure and phase loop
  combat.py     attacks, blocks, damage steps, keywords
  sba.py        state-based actions, commander zone moves
  respond.py    response hooks (the stack abstraction, §4.2)
  handlers/     one module per primitive group (mana, cards, board, combat, interaction, protection, life, triggers)
  plugins/      hand-written card behaviours keyed by oracle_id (only where the primitive vocabulary can't express a card)
  modules/      L3 win routes: voltron, wide, drain, spellslinger, combo, altwin
  policy.py     Pilot: POLICY knobs + decision functions (one Pilot per player)
  agents/       L4 opponent decks + their policies; archetype-curve fallback
  run.py        run(deck, table, N, seed, mode) -> Results
tools/sweep.py  staged screens, control arm, role-matched swaps, coverage report
tests/          unit (rules), golden games, property tests, regression
```

### 2.1 State model
- `GameState`: `players[4]`, `turn`, `active`, `rng` (one `numpy.random.Generator` per game, seeded from `(seed, game_index)`), `log` (an optional event list for debugging and golden tests).
- `Player`:
  - `life=40`; `poison`; zones (library, hand, battlefield, graveyard, exile, command); `commander_ids`.
  - `cmd_cast_count[cmd]`: for tax, CR 903.8.
  - `cmd_damage_taken[(owner, cmd)]`: CR 903.10a.
  - `land_played`; `mana_pool`; `flags` (monarch, initiative, has_lost).
- `Permanent`:
  - Identity: `oid`, `card`, `owner`, `controller`, `timestamp`.
  - Status: `tapped`, `summoning_sick` (CR 302.6), `phased_out` (CR 702.26), `face_down`.
  - Values: `counters{}`, `attached_to`, `damage`.
  - Tokens: `is_token`, `token_template`.
  - `is_commander`.
- **Card conservation invariant:** every non-token card is in exactly one zone at every SBA check (property test).

### 2.2 Card view
`Card(oracle_id)` exposes `name, ci, type, mv, cost, p, t, keywords, prims, conf, plugin`. A plug-in, where present, overrides or extends the primitives for that card. Modes (MDFC, adventure, channel, cycling) are separate `Mode` objects, and the Pilot chooses a mode.

## 3. Handler contract (L1 → L2)

Every primitive in the library maps to exactly one handler module that implements some of:

```python
def cast_cost(state, card, mode) -> Cost                 # cost changes (reducers, tax, alt costs)
def on_resolve(state, card, ctx) -> None                 # spells, ETB
def static(state, perm) -> list[Modifier]                # continuous effects (§4.1 layers)
def activations(state, perm) -> list[Action]             # activated abilities the Pilot may use
def triggers(state, perm, event) -> list[Effect]         # triggered abilities (event bus)
def respond(state, perm_or_card, threat) -> Response|None  # response hooks (§4.2)
RULES = ['CR 702.26', ...]   # rules the handler implements
SIMPLIFIES = ['...']          # stated simplifications, surfaced in reports
```

- **Unhandled primitive:** the card enters as its body (or does nothing if it's a spell). The game records `unmodelled_used[card]+=1`, and the sweep tool suppresses that card's delta.
- **rev2: per-face modes.** The parser (1.6) stores each face of a multi-face card as its own Mode with its own primitives, and symbolic amounts (`X`, `var`) that the handler resolves at run time.
- **Parser params are the handler's input.** The handler never re-reads oracle text, with one exception: plug-ins may.
- **Who benefits (planned, parser 1.7 — not yet in parse.py):** every effect record gets `beneficiary ∈ {you, opponent, each_player, target_player}`. Symmetric gifts ("you and target opponent each draw three") feed opponents through the gift modifier (skill Gate 8), not our own draw.

## 4. Rules coverage

| Area | Modelled | Simplified | Excluded |
|---|---|---|---|
| Turn structure | Untap (phasing first, CR 502.1), upkeep, draw (**rev2:** in multiplayer no player skips the first draw, CR 103.8c; a `house.first_player_skips_draw` flag exists only to reproduce the one-off sim and is printed in results), main 1, combat, main 2, end, cleanup (discard to 7, CR 514.1); London mulligan, first mulligan free in multiplayer | Upkeep and end-step triggers batched per step | Split second |
| Mana | Colours, colourless, restrictions ("only artifact spells", "can't cast nonartifact"), reducers by scope, tax, convoke and improvise as cost options, treasures | Greedy cost solver with colour reservation (§5) | Hybrid/Phyrexian optimisation beyond the cheapest legal payment |
| Casting | Sorcery and instant timing, flash, commander from the command zone with tax (CR 903.8), alternative costs (free spells), modes | Instants cast only through response hooks or the Pilot's end-of-turn window | Copying with new targets beyond the simple case |
| Combat | Attack any opponent or planeswalker; blocks; first strike and double strike damage steps (CR 510.4); trample, incl. with deathtouch (CR 702.19b + 702.2c: 1 damage counts as lethal); flying/reach; menace; unblockable; vigilance; lifelink; deathtouch; indestructible; extra combats; **rev2: vehicles and crew** (crew N by tapping power N, the vehicle becomes a creature until end of turn) | Blockers chosen by the defending agent's policy (§7), or by the `abstract_table` profile (§8); damage assigned as the current rules allow (no damage assignment order since 2024) | Banding, provoke, lure-style forced blocks beyond "must be blocked" |
| Commander rules | 40 life; **rev2:** a commander in the graveyard or exile may move to the command zone as a **state-based action** (CR 903.9a), so "dies" triggers fire and an exile-then-return can lose it; hand or library is a replacement (CR 903.9b); tax (CR 903.8); 21 combat damage per commander (CR 903.10a); partner / Background pairs | — | Companion (rules supported later; flagged) |
| Continuous effects | Layer 7 P/T order: 7a CDA → 7b set → 7c modifications, including counters → 7d switching (CR 613.4); keyword grants; "loses all abilities" (layer 6) | Layers 1–5 collapsed: copy = template of the copied card; control change = controller field | Full dependency ordering |
| Replacement effects | **rev2:** every applicable doubler applies (Doubling Season + Parallel Lives = ×4); the affected object's controller chooses the order (CR 616.1); "enters with counters"; commander hand/library replacement; regeneration (CR 701.15); indestructible | — | Self-replacement corner cases |
| Triggers | Event bus: ETB, LTB, dies, attacks, blocks, combat damage to a player, cast, upkeep, end step, landfall, lifegain | APNAP: the active player puts triggers on the stack first, so they resolve last; each player orders their own; no trigger stacking tricks | "Whenever a player chooses" style |
| Stack | Response hooks (§4.2) | Not a full priority loop | Stack tricks beyond the hooks |
| Protection | Hexproof, shroud (a player with hexproof can't be targeted by "target player sacrifices"; non-targeted edicts still work), ward (tax paid or the removal is countered), protection from X (targeting, blocking, damage), phasing (CR 702.26: stays on the battlefield, attachments phase too, no ETB), flicker (CR 400.7: new object, attachments fall off, counters lost, summoning sick, ETB re-fires), indestructible, regeneration | Ward paid automatically if affordable | — |
| SBA (CR 704) | 0 life (704.5a), drawing from an empty library (704.5b), 10 poison (704.5c), 0 toughness (704.5f), lethal damage (704.5g), deathtouch damage (704.5h), planeswalker at 0 loyalty (704.5i), legend rule (704.5j), aura without a legal object (704.5m), illegally attached equipment unattaches (704.5n), +1/+1 and −1/−1 annihilation (704.5q), commander damage 21 (704.6c), commander to the command zone (903.9a) | Checked after each resolution and each combat damage step | — |
| **rev2: Monarch / initiative** | Monarch: draw at your end step, stolen by combat damage to the monarch, passes when the holder leaves the game. Initiative: venture into the Undercity on taking it and at upkeep; stolen by combat damage. Our decks never run them (Seb's red line); opponents' agents may | Undercity rooms as a fixed table of effects | — |
| **rev2: Archenemy and gifts** | Archenemy: P(an opponent targets us with removal or attacks) = base × (1 + 0.5 × our board-lead share), capped at 0.9; board lead = our power on board ÷ the table average. Gift modifier (skill Gate 8): each unresolved gift card speeds every opponent's clock by 0.25 turn per extra card per opponent per cycle | Constants are ⚠️ defaults to be calibrated (L5) | — |
| Combos | Spellbook combos present in the deck are detected; when all pieces and mana are available, the game ends (win) if the house rules allow the combo. 2-card infinites are forbidden by house rule, so their presence is a Gate 7 failure, not a win | Assembly = all pieces on battlefield or castable this turn | Loop execution step by step |
| Politics | Targeting policy (skill Gate 9.4); archenemy pressure; no kingmaking | Deals and table talk excluded | — |
| Alt wins | Library-out (Thassa's Oracle family), life-total, counters | Treated as a module (§6) | — |

### 4.1 Continuous-effect evaluation
Compute P/T on demand: 7a CDA → 7b set effects by timestamp → 7c modifications (anthems, equipment, auras, until-end-of-turn, counters) → 7d switching. Cache per permanent and invalidate on any board change. Keyword grants are evaluated the same way.

### 4.2 Response hooks (the stack abstraction)
Instead of a priority loop, the engine opens a response window at fixed hooks. Each window asks every player's Pilot in APNAP order, and each Pilot may cast at most one instant or ability per window. The resolution is computed after all responses.
- **On a targeted removal / edict / wipe:** the target's controller may phase, flicker, hexproof, indestructible or counter.
- **On a commander or engine cast:** an opponent may counter (from the agents' interaction).
- **On declare-attackers and after blockers:** the attacker may use a trick; the defender may use fog / removal.
- **On a lethal attack (kill turn):** the defender's "answer" (agents: removal or fog; profile: the kill-turn answer rate).
- **End of the opponent's turn:** instant-speed draw / tutor / flash creatures.

## 5. Mana solver
- Sources are enumerated each time a payment is needed: lands, dorks (not summoning sick), rocks, treasures, rituals in hand, and convoke/improvise bodies.
- Payment is greedy: generic is paid last, and restricted mana (Vibranium-type) is spent only on legal spells. Colours keep a reservation for the Pilot's next planned spell this turn.
- Unit test cases: Vibranium can't pay for a nonartifact spell; Ancient Tomb gives {C}{C}; Lush Portico doesn't tap the turn it enters.

## 6. Win-route modules (L3)
A module supplies three things: (a) the extra handlers its plan needs, (b) a policy fragment (attack and sequencing), and (c) its kill check and reported metrics.

| Module | Kill checked by | Metrics |
|---|---|---|
| voltron | Commander damage ≥21 or life ≤0 from one carrier; equipment and aura stacking | Carrier power on the kill turn; turns to assemble |
| wide | Total combat damage through blocks with anthems and overruns | Tokens on the kill turn; wipe recovery |
| drain | Each-opponent life loss from death, ETB and lifegain triggers; sac-outlet loops (finite) | Drain per turn; deaths per turn |
| spellslinger | Spell-cast triggers (burn and drain), copies, cost reducers | Spells per turn |
| combo | Spellbook assembly (allowed combos only) | Assembly turn distribution |
| altwin | Card-specific checks | Assembly turn |

## 7. Pilot and agents (L4)
- **Pilot** (our deck): the POLICY dict from the skill (mulligan, cast order, hold interaction, tutor priority, equip priority, attack target, passage use, sinks last). It always takes the earliest available win. Every knob is tested one at a time on fresh seeds (skill pilot tuning protocol).
- **Agents** (opponents) are real decks run on the same engine, each with an archetype policy (aggro / aristocrats / control). They choose blocks, removal targets (fastest threat first, else our live highest-value permanent), and when to hold up interaction.
  - **Removal finally has a value:** an agent killed earlier delays the table clock.
  - **Fallback:** when a pod list is unknown, use archetype curves (`opp_sim.py`) and label the result `assumed`.
- **Blocks:** the defending agent chump-blocks when an attack would be lethal for it (life or commander damage). Otherwise it blocks only when it kills the attacker or trades favourably, and it never blocks into deathtouch with something valuable.

## 8. Runs, results, determinism
- **rev2: `abstract_table` profile.** A set of fixed odds the one-off sim used, kept as an explicit, named profile so M3 can be reproduced and every later change shows up as an explained delta:
  - Blocks: 50% chance one 2-toughness blocker stops a ground attacker; 15% against fliers; none if unblockable.
  - Chance-based cards: Sensei's Top 0.3, Mystic Forge 0.4, Esper Sentinel 0.3, Adaptive Omnitool 0.5 (draw probability).
  - Disruption schedule: creature wipe T5–7, commander removal T3–6, artifact wipe T6–8, with the skill §2 rates.
  - `cmdout`: commander removed on T3 and T5.
- **rev3: pace.** The table model is parameterised by pace (median first-win turn + spread, or a mix). Agents' curves are reshaped to it; `pace_sweep` runs the deck against table medians T5–T12 and returns the pod-win curve. The judge turn is the pace median + 2 (default T12), and win-by-T(n) is reported for any n.
- **Modes:**
  - `goldfish`: 3 × 40-life opponents. Passive in the generic engine, or blocking per `abstract_table` when reproducing the one-off sim.
  - `disruption`: the skill §2 profile, injected events.
  - `pod`: the profile, or agents when available.
  - `backup`: the deck file's `kill_pieces` list is removed from the library.
  - `cmdout`: commander removed on T3 and T5 (two taxes).
  - `table`: agents.
- **Results JSON:** `{deck, version, engine_version, parser_version, profile, house_flags, mode, N, seed, kill_turn_hist, win_by{T8,T10,T12,T14}, pod_win, pod_calibration, paired_ref, se, unmodelled_used, stats{...}, simplifications[]}`.
- **rev2: Noise bars.** Paired (same engine, same seeds): 2 × paired SE and ≥2 points. Unpaired (across engines, or the one-off sim vs the new engine, where seeds can't be shared): 2 × √(SE₁² + SE₂²) and ≥2 points. Regression entries store N and seeds.
- **Determinism:** the same `(deck, table, mode, N, seed)` always gives identical results, which a CI test enforces (fix `PYTHONHASHSEED`; never iterate over unordered sets in game logic). Paired comparisons share seeds; re-tests use fresh seeds.
- **Performance:** set the target after profiling M3a (rev2: 500 games/s per core is optimistic for an object model). Budget: a 400-card screen × 2 arms × 5,000 games ≈ 4M games, so staged screens and multiprocessing are required. `multiprocessing` splits by seed blocks; results merge deterministically.

## 9. Tests
1. **Rules unit tests** (each cites its CR):
   - Phasing keeps equipment attached and doesn't re-fire ETB.
   - Flicker drops equipment, re-fires ETB, and the creature is summoning sick.
   - Double strike plus first strike damage steps.
   - Trample with deathtouch assigns 1 per blocker.
   - Commander damage counts only combat damage from that commander, and survives zone changes of the commander.
   - Tax increments only on casts from the command zone.
   - Legend rule.
   - Lifelink.
   - Indestructible survives destroy but not exile or −X/−X.
   - Ward fizzles the removal when unpaid.
   - Vibranium restriction.
   - Discard to 7 at cleanup (CR 514.1).
   - A non-targeted edict ignores hexproof creatures; a player with hexproof stops "target player sacrifices".
   - Indestructible doesn't stop sacrifice or the legend rule (test both).
   - A commander that dies goes to the graveyard first (dies triggers fire), then moves to the command zone as an SBA.
   - Doubling Season + Parallel Lives = ×4 tokens.
   - No player skips the first draw in multiplayer.
2. **Golden games:** scripted libraries with exact expected outcomes (turn of kill, life totals).
3. **Property tests:** card conservation; no negative mana; no permanent in two zones; tax is never negative.
4. **Regression set** (`regression/regression.json`): every engine change re-runs all decks, and drift beyond the noise bar blocks the merge until explained. Starting deck: Wakanda v4.1.
5. **Parser quality:** 20-card spot-check per class each parser version (skill §8 quality gate).

## 10. Build order (milestones and acceptance)

| # | Milestone | Acceptance |
|---|---|---|
| M0 | Repo hygiene: `pyproject`, `pytest`, `ruff`, CI that runs tests on every commit | `pytest` green; deterministic-seed test passes |
| M1 | State, zones, turn loop, land drops, mana solver, casting permanents, commander from the command zone with tax | Vanilla 37-land deck, mulligans off, fixed draw rule, N ≥ 20,000: land-drop curve matches the hypergeometric expectation within 1 point at T1–T8 |
| M2 | Combat, keywords, SBA, commander damage, response-hook skeleton | The combat, keyword, SBA, commander and draw-rule tests in §9.1 pass (ward, phasing, flicker, Vibranium and doubler tests belong to M3/M4) |
| M3a | **Faithful port** under `abstract_table` + `house.first_player_skips_draw`: handlers for every primitive Wakanda v4.1 uses, plus plug-ins ported from `engine/oneoff_wakanda/sim_r3.py` (T'Challa, Shuri, Hulkbuster Armor, Kuldotha Forgemaster, Great Mound, Shuri's Fabricator, Dawnsire, Storm, Bast, Rogue's Passage, Ironsoul Enforcer, Retrofitter Foundry, Akroma's Will, and the rest of its hard-coded cards) | **Goldfish T10 = 82.6% within the unpaired bar** on fresh seeds (12,000 games) |
| M3b | Replace each abstraction with the generic mechanism (passive or agent blocks, real draw cards, CR draw rule), one at a time | Each change logged as an explained regression delta; the new baseline is stored |
| M4 | Disruption profile injection, targeted removal, wipes, artifact wipes, protection responses (ward, phasing, flicker tests) | **Disruption T12 = 72.8% and pod-profile T12 = 73.2%, each within the unpaired bar** (under `abstract_table`) |
| M5 | `tools/sweep.py`: staged screens, control arm, role-matched swaps, per-type and universe coverage report, unmodelled suppression; only spot-check-passed classes are scored | Re-run the Wakanda land and spell sweeps; same verdicts (no swap clears the bar) |
| M6 | Agents: Krenko, Sephiroth, Y'shtola as decks (EDHREC average lists trimmed to B3) with archetype policies; removal valuation | Agent table win curve within 1 turn of the archetype curves (median T10), or the difference explained |
| M7 | Wide + drain modules, with Lathril as regression deck #2 | Lathril numbers stable across two fresh-seed runs; engine regression green |
| M8 | Spellslinger + combo modules with Maralen; parser 1.6 (beneficiary field, doubler/copy tightening) | Regression green; coverage report shows blue ≥70% |

## 11. Risks and how they're contained
- **Pilot weaker than a human:** policy knobs, one-at-a-time tuning, and a "don'ts" list in the pilot guide. Results compare versions under the same pilot, never absolute strength.
- **Parser false positives:** spot-check gate; hand-verified records override; suppression when unmodelled.
- **Rules gaps:** this §4 table is the contract. Anything outside it is `unmodelled`, never zero.
- **Overfitting to the model:** fresh seeds, control arms, calibration against real games (L5), and the noise bar.
- **Speed:** profile first; vectorise the mana solver and combat math; multiprocessing by seed blocks.
