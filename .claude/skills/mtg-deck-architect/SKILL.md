---
name: "mtg-deck-architect"
description: "Entry point for any Commander build, audit, tune or card advice. Builds max-power honest Bracket 3 decks by measured, stacking synergy across the whole legal card pool; offers a theme skill tree (every kill route built on a chosen theme resource) and a strategy layer to push each deck to its maximum."
---

# MTG Deck Architect — Commander Deck Builder (v5.6)

**Goal:** the strongest deck that is still honestly Bracket 3 under Seb's pod house rules, won by **synergy**: every card feeds others toward a stated kill. Not popularity, not staples.

**Four laws**
1. **No card fact from memory.** Every card named, in any mode, is checked on Scryfall first. Colour identity = Scryfall's `color_identity` (every mana symbol in cost and rules text, both faces).
2. **The kill comes first.** Gate 2 is the master gate; every slot serves it.
3. **Nothing ships on argument.** It ships on a model run whose code actually ran, with the play policy written down before the run. Anything unmodelled is marked ⚠️.
4. **Every effect has a beneficiary.** Read who a card actually helps: you, each player, each opponent, or a player who "may". Symmetric, opponent-optional or stealable effects are credited to the table too. Commander first.

Markers: ✅ confirmed · ⚠️ assumed/partial/unmodelled · GAP (input missing, ask) · BLOCKED (source down, unresolved name, count ≠ 100, illegal card).

---

## 1. MODES, DECISIONS, TOOLING

| Mode | Trigger | Runs | Ends with |
|---|---|---|---|
| **Build** | "build X" / "rebuild X" | Intake + Gates 1–10 | DONE or DRAFT (stop condition, §7) |
| **Audit** | pasted list / "audit my X" | Intake (confirm commander — never reverse-engineer it) → Gates 1 (clause targets), 2, the existing list as the Gate 2.5 baseline, 3 (seed list + theme-name sweep only), 4–9 | Gap list + Pod-Fit verdict. Never DONE |
| **Tune** | "improve X" / "add Y?" | Package rule (Gate 4) → Gates 7, 8, 9 as a controlled A/B → Gate 10 if written back | Kept / rejected, with the A/B line |
| **Quick** | single card / rules / mid-game | Card-truth check. Any suggested add names its links (Gate 4) and is marked ⚠️ "unmodelled suggestion" | Answer |

Not this skill: `mtg-judge` (rules execution — feed it oracle text). `article-writing` (primers).

**Iteration rule.** Only intake inputs and the kill style are locked. Gates 3–7 make provisional picks; **Gate 9 decides**. A failed Gate 9 target returns to the gate that owns it (mana/colour → 5 · kill speed/stall → 2/4 · disruption/backup → 4/6), then Gate 9 re-runs. Max 3 loops; still failing = UNDERGUNNED, written back as DRAFT.

**Decision rule (one rule everywhere).**
- **Pace (adjustable):** the table's usual game length, set as a preset (turbo T4–5 · fast T6 · mid T8 · casual T10, the default · slow T12+), a median turn, a mix (e.g. 30% T6 / 70% T10), or free text ("usually over by turn 7–9"). Every turn number below follows it: with pace median M, read T(M+2) for "T12" and T(M) for "T10". Always report the **pace sweep**: pod win at table medians T5–T12, and a pace-fit label (fast / mid / slow / all-rounder).
- **Judge:** disruption win-by-T12. **Veto:** goldfish win-by-T10 must not drop by more than the noise bar. When pod calibration is `calibrated` (§5), pod win replaces disruption T12 as the judge, and disruption T12 must still meet its Gate 9 target.
- **Noise bar** (card and package changes): act on a difference only if it exceeds **2 × the paired standard error** and at least 2 points. Report the SE with every delta. Comparisons are paired (same seeds within a comparison).
- **Escalation bar** (ceiling and strategy layer): max(3 points, noise bar). One threshold, used in both places.
- **Many candidates:** screen results are hypotheses. Re-test the top 30 at ≥6,000 games in both modes **on fresh seeds** (paired only within the re-test) before believing any of them — reusing the screen's seeds keeps its selection bias.
- **Workload:** keep the coded-card library and screen results cached across builds (re-screen only cards whose deck context changed); run long sweeps in the background; screen in two stages (500 games to drop clear losers, then 2,000).
- **Owned vs new print:** prefer the owned card unless the new one beats it by the noise bar.

**Tooling fallback.** No Python sandbox → Gates 1–8 only, no numbers, output DRAFT. Spellbook down → hand-read risky cards (Gate 7), mark ⚠️, DRAFT until re-run. EDHREC/Moxfield down → seed list marked GAP. Scryfall down → BLOCKED. Never fill a gap from memory, scrape around a refusal, or claim a source or script you didn't call this run.

---

## 2. DEFAULT INPUTS (Seb's pod — use unless told otherwise)

**House rules**
- Honest Bracket 3. Never Bracket 4.
- **No 2-card infinite combos at any turn — commander + 1 card counts as 2.** 3-card combos allowed in combo decks; disclose them to the pod.
- **Snowballs are allowed at any size, including 2 cards** (Seb's ruling, same logic as Krenko). One test for every repeating line: **can it grow without limit inside a single turn, with no untap step and no new cards?**
  - **Yes → infinite** (rules above apply). Also infinite: a loop limited only by a resource it doesn't refill (library, life, opponents' life) that can be run to the end in one turn. *E.g. Restoration Angel + Felidar Guardian.*
  - **No → snowball, allowed** even when exponential (tokens enter tapped, once-per-turn triggers, needs an untap step). Disclose it. *E.g. Hollowhenge Overlord + a token doubler; T'Challa + Emiel + Panharmonicon + Unwinding Clock + doubler.*
- Kill style locked per deck at intake. Seb's default: **finite, definite kill** — no infinite loop of any size in a finite deck; snowballs are fine.
- **Max 3 Game Changers**, counted live from Scryfall across all 100 cards.
- No mass land denial. No extra-turn chains or recursion. No lock that stops more than one opponent from playing.
- Proxy pod: money is no constraint, **but every new print is a cost** (prints are batched). Ask a new-print cap at intake.

**Seb's play-style red-lines** (default for every deck unless he lifts one)
- **No monarch or initiative engines** — Seb doesn't like them. Cards whose value depends on becoming or keeping the monarch / taking the initiative are rejected at Gate 3 with the reason "red-line: monarch", even when they test well.

**Seb's pod (assumed lists, 9 Nov 2026):** Krenko, Mob Boss (mono-red goblins) · Sephiroth, Fabled SOLDIER (mono-black aristocrats) · Y'shtola, Night's Blessed (Esper spell-drain control). Lists = EDHREC average decks trimmed to B3; replace with the real lists when Seb shares them. Modelled win turns: Krenko 25% by T8 (the fastest; kill Krenko on sight) · Sephiroth bimodal, ~9% by T6 from Gravecrawler + Phyrexian Altar loops, else slow · Y'shtola rarely wins before T12 but carries most of the interaction. **Table's first win: 35% by T8, median T10** — status `calibrated (assumed lists)`. The old turn-5 curve from Arcum data is retired.

**Pod disruption profile (`pod` mode — use for Seb's decks)**
| Event | Rate | Source in their lists |
|---|---|---|
| Creature wipe on turns 5–7 | 68% | Toxic Deluge ×2, Cleansing Nova, The Meathook Massacre, Blasphemous Act |
| **Artifact wipe on turns 6–8** | 25% | Vandalblast (overload), Cleansing Nova — the biggest single threat to artifact/equipment decks (Wakanda: −11 points of disruption T12) |
| Commander removed once by turn 6 (25% of it is an edict that ignores hexproof) | 75% | Swords, Dismember, Snuff Out, Stroke of Midnight, Vindicate, Lightning Bolt, Chaos Warp; Fleshbag Marauder, Plaguecrafter, Sheoldred's Edict |
| Targeted removal of our top non-commander permanent | 50% | as above |
| Answer on the kill turn | 40% | Counterspell, Fierce Guardianship, Force of Negation, Rewind, Sink into Stupor |
| Pillow tax ({2} per attacker) from turn 4 | 30% | Ghostly Prison, Propaganda |

**Generic disruption profile** (other pods; refine from the real 3 decks; record which)
| Event | Rate |
|---|---|
| Creature wipe on turns 5–7 (artifact decks also run an artifact-wipe variant) | 60% |
| Commander removed once by turn 6 | 50% |
| Targeted removal of our **live highest-value non-commander permanent** (ranked by the baseline single-card test), once per game, the turn after it lands | 50% |
| An answer on the kill turn, hitting the highest-impact kill piece | 30% |
| Pillow tax ({2} per attacker) from turn 4 | 25% |

**Mulligan** (Seb and the model): London; first mulligan free in multiplayer (CR 103.5c). Judge the 7 drawn before bottoming. Keep 3+ lands, or 2 lands + a mana source, AND ≥1 engine or fuel piece (a commander engine costing ≤4 counts). Mulligan 0–1 and 6+ landers. From the second mulligan on, keep any hand with 2–5 lands; never go below 5 cards. Bottom the highest-cost cards that don't serve the opening plan.

**Where decks live:** the master print workbook (tabs `Deck - <name>`, sheet `Batch 2`, print list). Notion is an optional mirror.

---

## 3. DATA SOURCES (call them; never recite them)

| Source | Use | Calls |
|---|---|---|
| **Scryfall** — card truth | names, `color_identity`, `legalities.commander`, `game_changer`, `oracle_text`, `cmc`, `oracle_id`, rarity, `released_at` | `POST api.scryfall.com/cards/collection` (≤75) · `GET /cards/named?fuzzy=` · `GET /cards/search?q=` (GC list `is:gamechanger`; commanders `is:commander id=<c>`) |
| **Commander Spellbook** — combos | combos in list (`included`), one card away (`almostIncluded`), bracket estimate, near-infinite search | `POST backend.commanderspellbook.com/find-my-combos` · `POST /estimate-bracket` · `GET /variants/?q=` |
| **EDHREC** — corpus | Gate 3 seed list (candidates only, never evidence); missed-card check; real bracket split | `json.edhrec.com/pages/commanders/<slug>.json` (403 = not in corpus); average decks `edhrec.com/average-decks/<slug>/<bracket>/<theme>` |
| **Moxfield / Archidekt** — public lists | seed list; imports | `api2.moxfield.com/v3/decks/all/<id>`. Its `bracket` field is a claim, never trusted |

**Gotchas**
- Real User-Agent + `Accept: application/json`, ~100 ms between calls.
- Retry every Scryfall `not_found` (fuzzy, then text before ` // `). A retry resolving to a DIFFERENT name is a substitution the user must confirm. Reject token/emblem/memorabilia layouts.
- Count and singleton by `oracle_id`, never by name.
- **Reprint-name aliases** count as owned copies of the original: `Black Panther's Claws` = **Hammer of Nazahn** (Seb-confirmed). Add each new confirmed alias here.
- Spellbook bracket tags: read their meaning from Spellbook's docs at run time and print it next to the tag; fail on any tag Spellbook defines as above bracket 3.
- Bracket caps (B3 = 3 GCs) are doctrine, not an API field — last verified 2026-08-29; re-check at each brackets update.

---

## 4. THE GATES

**INTAKE — 5 inputs** (defaults from §2; mark assumptions ⚠️, ask only true gaps): 1 commander (or candidates, or "open") · 2 pod (default profile or the 3 real decks) · 3 kill style + goal · 4 ceiling (B3 + GC budget) · 5 constraints: owned pool, new-print cap, red-lines, **deck identity** (what must not change, e.g. Wakanda = green-white Black Panther family) and theme, if any.

**Gate 1 — Commander & colours.** Scryfall-confirmed colour identity and legality.
- **Clause targets:** split the commander's oracle text into clauses; each becomes a measured Gate 9 target (Shuri: ≥3 artifacts by T4 in ≥80% of games, ≥6 by T6 in ≥60%).
- **Commander sweep (commander open):** pull every legal commander within the identity (`is:commander id<=<colours>`; report exact-identity and subset counts separately), plus legal partner / Background / friends-forever pairings of the top singles. Script-score each: **score = 3a + 2b + 2c + d + e − 2f**, every term scaled 0–1 (a kill-clause fit to the goal, b one-sided engine clause, c pool cards feeding its clauses ÷ the highest count among candidates, d survives removal/wipes, e mana value ≤4, f symmetric gift per Law 4); range −2 to 9. Top 15 → model the top 5 as **shared core + commander package** (not five full builds). Report "considered / scored / modelled".
- Two candidates → two tailored commander packages on one shared core; never one 99 with the commander picked at the end.

**Gate 2 — Kill & Spine (MASTER).** Before any card is chosen, write:
- **Kill:** primary kill and target turn; **backup kill that works without the commander**; how many cards can fill each kill piece.
- **Engine** (repeated action toward the kill) · **Fuel** (what it consumes) · **Protect** (what keeps engine and kill turn alive).
- **Synergy core as mechanic pairs** (e.g. "double strike × large power", "free equip × high equip cost"). Gate 4 fills them with cards.
- **Role tags and slot budget** (adjust per deck, write it down):

| Slot | Target |
|---|---|
| Lands | Gate 5 formula to start; Gate 9 land sweep decides |
| Mana (rocks/dorks/reducers) | 8–12 |
| Kill pieces | ≥3 cards per piece (or commander-fetchable AND ≥3 protection) |
| Card draw / advantage | ≥8, ≥4 of them repeatable |
| Interaction | ≥8 |
| Protection for engine/commander | ≥3 |
| Engine + fuel | the rest |
| Generic (untagged ramp, tutors, interaction — counted inside the rows above) | ≤14 |

Typical sum: commander + 36 lands + 10 mana + 8 draw + 8 interaction + 3 protection + 9 kill = 75 → 25 for engine + fuel.

**Gate 2.5 — v0 list + baseline run.** Fill the slot budget with the best-linked cards known so far (owned first), verify (Gate 8), then run in this order: (1) goldfish, (2) goldfish single-card test, which ranks permanents for targeted removal (unranked permanents rank by mana value), (3) disruption, (4) dead-weight test, (5) bottleneck read. Re-rank removal targets once from the disruption run. Every later screen, quality floor and "lowest-value slot" uses this baseline.

**Gate 3 — Search.** Everything found here is a candidate; Gate 9 judges it.
1. **Role queries:** Scryfall queries per role inside the identity, narrowed to ≤200 results; script pre-scores keyword hits; read the top 40 per role. Record each shortlisted card's 2 strongest links and kill path as you go; mark owned vs new print. Log every query.
2. **Community seed list:** EDHREC commander page + average decks (each bracket and theme tab) + top 3 public Moxfield/Archidekt lists. Every card in ≥2 **independent sources** (all EDHREC average decks together count as one source; each public list counts as one) and missing from our list is screened, and ends as **tested (number)** or **rejected (reason: off-plan, anti-synergy, who-benefits, bracket, illegal)**. An unexamined seed is a GAP.
3. **Theme-name sweep:** every pool card naming the deck's family, theme resource or the commander's keywords (e.g. Wakanda, Black Panther, Vibranium) — tested or rejected, same as seeds.
4. **Resource map:** list everything the deck produces each turn (combat damage, life, artifacts, tokens, Equipment entering, attack triggers, land drops, cards drawn, monarch). Search the full pool for **payoffs** and **converters** that turn a resource into a kill (lifelink → Aetherflux Reservoir).
5. **Auto-code** cards a parser can read, across all card types: stat boosts and anthems, "for each X" scaling, keywords and evasion, unblockable, combat-damage draw, equip cost/auto-attach, mana abilities, token makers, +1/+1 counters and doublers, copies, extra combats, cost reducers, vehicles/crew, monarch, artifact/enchantment-count payoffs ("for each artifact", metalcraft), "whenever an artifact / Equipment / Aura / creature enters" triggers, attack- and combat-damage-trigger enchantments, sacrifice outlets, protection and phasing, tutors. **Spells by mode:** removal (target / edict / wipe, what it hits, instant or sorcery speed), draw spells, combat tricks, flicker / blink, phasing, and channel / cycling / MDFC. A card with a second mode is coded in both modes. Strip reminder text before parsing; reject tribe-only, conditional ("as long as", "if you") and until-end-of-turn matches; restricted mana ("spend this mana only") is not ramp. **Coverage bar, per card type:** the legal pool includes **every** card type, lands too. Each type (creature, artifact, enchantment, instant, sorcery, planeswalker, land) must be ≥25% effect-coded, and the deck's **theme types** (e.g. artifacts and enchantments for an equipment deck) ≥40%. Plain bodies (a creature coded only by power and keywords) are reported separately and never count toward the bar. Also 100% of seeds and theme-name hits (hand-code what the parser misses). A sweep that skips a whole type (e.g. only equipment, auras and rocks) fails the bar however many cards it tested.
5b. **Utility-land sweep:** every legal non-basic land in the identity is coded by role: fixing, creature land, utility activation (pump, protect, unblockable, draw, token), artifact land, spell-land (MDFC), cycling. Fixing lands are judged by colour-source maths (Gate 5), not the sim. Every other land is screened as a one-for-one swap **for a basic** (never for a spell slot), with a basic-for-basic control arm and the same staged screen and noise bar. A land that clears the bar is a free upgrade.
5c. **Spell sweep (instants, sorceries, channel):** screened by **role-matched swap**, keeping the role floors.
   - Protection, phasing and flicker spells are swapped for the deck's least-valuable protection card, the one whose cut costs least in the single-card test.
   - Tricks, +1/+1 counter spells and draw spells are swapped into the least-synergy slot.
   - Removal is swapped for the least-valuable removal card **only when the engine models opponent threats**. Until then, rank it in an efficiency table (mana value, speed, which of the pod's key threats it answers, who-benefits) and label it unmodelled.
   - Our own wipes are screened only with a protection plan, and pass the anti-synergy scan first.
   - Channel cards and MDFCs are screened in both slot types: as a land against a basic, and as a spell against its role.
   **Phasing is not flicker; the engine must model both.**
   - **Phasing** (CR 702.26): the permanent never leaves the battlefield. Equipment and Auras stay attached, it is the same object, it has no summoning sickness, there is no commander tax, and ETBs don't re-trigger.
   - **Flicker** (exile and return; CR 400.7): the permanent becomes a new object. Equipment falls off (pay to re-equip), Auras go to the graveyard, counters are lost, it is summoning sick unless it has haste, and its ETBs re-trigger (T'Challa: a Vibranium token). A commander that is flickered stays out, with no tax, unless its owner moves it to the command zone while it is exiled (CR 903.9). It then doesn't return.
6. **Screen budget:** screen at most ~400 cards per build, in priority order: seeds and theme hits → resource-map payoffs/converters → other coded cards by parser pre-score. Each is a one-card swap into the baseline's least-synergy slot (Gate 9 cut rule; never an interaction/protection slot or a land; lands go to the utility-land sweep), paired seeds, staged per §1. **Cluster cards** (they pay off only together) are also screened as a package; a card below the noise bar on its own is not rejected until its package has been screened. Top 30 re-tested per §1.
7. **Quality floor:** a linked card that does the same job as an owned generic card at equal or lower mana value must beat it by the noise bar; otherwise mark ⚠️.
8. **Coverage report:** a table by card type, with pool → effect-coded (x%) → plain bodies → screened → re-tested → hand-coded for each type, lands included. Then seeds tested/rejected/GAP, theme hits, uncovered categories, and the uncoded count per theme type. Close with **universe progress**: library coded / full Commander-legal pool (§8).

**Gate 4 — Packages & Link List.**
- A **link** is a specific oracle interaction, `A → B: reason` (A's output is B's input or trigger). "Both are artifacts" is not a link. Types:
  - **Complement:** worth more together (one multiplies or unlocks the other). Only complements count as synergy.
  - **Substitute:** same job. Counts as redundancy, never synergy.
  - **Anti-synergy:** one weakens the other. Scan pairs for "loses flying/abilities", sacrifice on leave/unattach, symmetric effects hitting our board, legend-rule clashes, attach restrictions, vigilance vs tapped-creature payoffs, needs a board the deck doesn't build. Zero unresolved before ship.
- **Fill the Gate 2 core pairs with cards.** Every package (3–5 cards, stated slot cost) must strengthen a core pair. Competing packages are A/B'd in Gate 9.
- **Stack toward the bottleneck** found in the baseline (first lethal turn, hits per turn vs opponents left, mana- or colour-stuck turns, overkill share). Power past the lethal line is wasted.
- **Stacking rule:** in a real synergy cluster each added card adds more than the one before (increasing returns). Prefer multi-payoff cards (feed ≥3 payoffs already in the list); stop adding when marginal gain falls — later cards are backups.
- Every swap names links gained and lost. No 1-for-1 "weakest slot" swaps of unlinked cards. Flex/meta slots pass the same link test; never fill to 100 with filler.
- **Link metrics (scripted):** links come from a full oracle-text scan of all 100 (output keywords → input/trigger keywords), not from the hand-written CSV. **Kill-link %** = share of core nonland cards (not mana, interaction, protection, generic draw) linking directly to a kill piece or to an engine card that does. The commander and the top 10% most-linked cards are left out of the denominator only — they still count as link targets. Target ≥85%. **Kill redundancy** ≥3 per piece. Cards with <2 scanned links = first cut list. Publish the CSV (`from,to,reason,type`) as the readable record.

**Gate 5 — Mana Base** (before interaction). Start: lands = 36, −1 per two cheap mana-positive rocks/dorks, −1 if draw is heavy, floor 30 — the Gate 9 land sweep picks the final number. Each colour with ≥10 pips: ≥15 sources; splash (<10 pips): ≥10. Mono-colour: colourless-only lands ≤ total lands − 18. Utility lands carry a role tag. Count cost reducers separately from ramp. Curve targets (warnings; the model wins if they disagree): average nonland MV ≤3.2, ≥12 plays at MV ≤2.

**Gate 6 — Interaction & Protection.** ≥8 interaction, ≥3 protection covering the commander, the top engine piece and the kill turn. Cheap/free first. Each piece carries a role tag or comes out of the generic slots. **Pilot posture:** don't reveal the kill before the turn you go for it; hold ≥1 interaction on the kill turn.

**Gate 7 — Bracket 3 Ceiling.**
- Spend the 3 GC slots on the biggest modelled impact (confirmed by the Gate 9 single-card test).
- **Combo scan:** Spellbook `find-my-combos` on the full list (commander included). `almostIncluded` infinites become the **forbidden-adds list** for Tune. Hand-read oracle text of the 10–20 risky cards (untap, sacrifice outlets, recursion, free activations, "whenever … you may", replacement effects) for loops and locks Spellbook misses. A clean Spellbook result is a floor, not proof.
- **Snowball check:** classify every "infinite"/"near-infinite" hit with the §2 single-turn test before failing it.
- **Fail:** any 2-card infinite (commander + 1 included) · any infinite in a finite deck · MLD · extra-turn chains/recursion · multi-opponent lock · >3 GCs. **House rules beat Spellbook's tag:** classify snowballs and allowed 3-card combos first; a tag above bracket 3 fails the deck only when it comes from something the house rules ban, otherwise it is reported with its cause. A snowball never fails.
- **OVERSHOOT:** goldfish wins by T6 in >15% of games → trim speed.

**Gate 8 — Verify (BLOCKING).**
- Scryfall-resolve all 100 (zero unconfirmed substitutions); colour identity incl. ability costs; count = 100 and singleton by `oracle_id`; GC count across all 100.
- **Legality:** `legalities.commander` must be `legal` on **every** printing (check `GET /cards/search?q=!"<name>"&unique=prints` and take the strictest — before a set releases, Scryfall's prints can disagree: Federation Resupply showed `legal` via `/cards/collection` and `not_legal` via `/cards/named`). `not_legal` before its set's `released_at` = listed with the release date, legal on release. Anything else (`banned`, `not_legal` after release, `restricted`) = BLOCKED.
- **Who-benefits audit (scripted):** scan all 100 for `each player`, `each other player`, `all players`, `each opponent may`, `an opponent may`, `opponents may`, `its controller`, `that player`, `target player`, `any player`, `players can't`, `you and target opponent`, parley, join forces, tempting offer, council's dilemma, will of the council, **and shared resources** (`monarch`, `initiative`, `target opponent becomes`, `city's blessing`). Classify each hit: ours · gift to the table · symmetric restriction · opponent's choice · stealable. Commander first. Interaction that pays the opponent (Path's land, Beast Within's 3/3) is an accepted cost — list it.
- **Gifts in the race:** an unresolved gift makes the table faster, ⚠️ default 0.25 turn per extra card per opponent per cycle, applied as a modifier on the opponents' clocks in Gate 9 (and so in the pod race); replaced by an engine-derived number when the shared engine can measure it.
- **Gates 7–8 re-run on the exact list before any write-back**, including small tunes.

**Gate 9 — Model & Stress Test.**
1. **Policy first:** write the play and mulligan policy (casts, fetches, holds, attack targets) before coding. The pilot always takes the earliest available win. State every simplification.
2. **One shared engine:** every deck runs on the same engine (mana, mulligan, draw, combat, blocks, disruption, race); a strategy is a plug-in (card behaviour + policy). Comparisons across engine versions are labelled "cross-model, indicative only". **Must support before a verdict:** equipment/auras, **commander damage (21 from a single commander, tracked per commander per opponent)**, commander tax and the command-zone return, tokens, +1/+1 counters and doublers, copies, vehicles/crew, monarch (gain/steal/lose), initiative, extra combats, lifegain converters. A card relying on an unsupported mechanic is ⚠️ unmodelled, never scored as zero. **The shared engine is the §8 Layer 2 engine.** A deck-specific sim is allowed only as a stopgap labelled `one-off`, and its hand-written card code is ported into the shared library before the next build.
3. **Opponent model:** each opponent has a clock (from calibration, §5) and presents threats our interaction can answer (an answer delays that opponent's clock); blocks scale with their board; removal follows the §2 profile (commander removal, then our live highest-value non-commander permanent); gift modifiers from Gate 8 speed their clocks; **archenemy:** removal and attacks aimed at us rise with our board lead; any opponent who connects can steal the monarch.
4. **Pilot targeting policy (politics):** first, any opponent who can win on their next turn; otherwise the opponent closest to death (life or commander damage, whichever is nearer); ties go to the one with the biggest board; don't leave the leader unchecked to finish a weak player (no kingmaking); hold interaction for the kill-turn threat; don't over-extend into a known wipe when the kill isn't ready.
5. **Runs** (paired seeds, ≥5,000 games per version): goldfish (3 × 40 life) · disruption (§2 profile) · backup (primary kill pieces removed from the library) · commander-out (removed twice by T6).
6. **Targets** (disruption decides; goldfish speed set per kill type):

| Test | Target |
|---|---|
| Goldfish win by T10 — go-wide / engine / combo | ≥70% |
| Goldfish win by T10 — single-carrier voltron | ≥60%, and by T12 ≥85% |
| Goldfish no-win by T14 | ≤5% |
| Goldfish win by T6 | ≤15% (else OVERSHOOT) |
| Disruption win by T12 | ≥45% |
| Backup run, win by T14 | ≥25% |
| Commander-out run, win by T14 | ≥40% |
| Commander cast by turn MV+1 | ≥80% |
| Commander clause targets (Gate 1) | met |
| Colour-stuck games / ≤3 mana on T4 | ≤10% / ≤20% |

7. **Card tests** (all paired, noise bar from §1):
   - **Single-card test** on kill/engine cards and GC candidates: any card worth >15 points of disruption T12 alone (goldfish T10 also reported) = single point of failure → add backups; it is the disruption profile's top target.
   - **Dead-weight test:** replace each nonland, non-interaction, non-protection card with a blank (uncastable card). Scoring no better than the blank **flags** the card as dead weight; audit the policy first. Lands belong to the land sweep. Dead weight is a warning, **not** how cut slots are chosen.
   - **Cut slots = least synergy (Seb's rule).** Choose what to cut by synergy, not by blank-card value: (1) scripted link scan of all core cards (links from oracle text, commander counted separately); (2) read the oracle text of the bottom ~10 to fix what the scan misses (tutors with unusual wording, triggers on "spells cast", effects that pump the attacking carrier); (3) substitutes past their cluster's peak (stack curve) count as low synergy; (4) interaction, protection, mana and draw stay protected by their floors. Pick the least-synergy cards, then confirm in the model that cutting them loses nothing beyond the noise bar versus the weakest-slot cuts. *Why: Wakanda v4.1 — cutting Sensei's Divining Top and Kor Outfitter (least synergy) scored the same as cutting the blank-test weakest slots (72.8% vs 73.2% disruption T12), and kept Commander's Plate, which links to the commander and the free-equip cluster. The raw scan wrongly ranked Brightglass Gearhulk and Aetherflux Reservoir as least-linked; both are real contributors (cutting them cost 1.8–2.9 points).*
   - **Role test (the only cut rule):** blank a whole role at once; cut a flagged or candidate card only if blanking it together with its nearest backup costs ≤2 points.
   - **Negative value** (deck better without a card): audit the policy first — usually a pilot bug.
   - **Interaction** is valued only where the model lets it answer something; otherwise the Gate 6 floor protects it and it is never cut or screened on model numbers.
8. **Synergy proof:**
   - **Pair test (2×2, same seeds)** for the core and the top 10 claimed complements. Run all four arms with every other slot held identical: f(neither), f(A only), f(B only), f(A+B) — empty slots hold the same filler in every arm. **Interaction I = f(A+B) − f(A only) − f(B only) + f(neither).** From a full deck by removal, the same thing is **I = loss(A) + loss(B) − loss(A+B)**. I > 0 beyond the noise bar = **complement** (together worth more than apart — real stacking). I < 0 = **substitutes / redundancy** (each covers for the other). *Why: v5.4 and earlier had the sign inverted (positive loss(A+B) − loss(A) − loss(B) was called a complement, but that is redundancy). Check: Hulkbuster Armor + Rogue's Passage, two evasion sources, measured I = −2.1 — substitutes, as expected. Earlier Wakanda pair readings (e.g. Puresteel Paladin + Colossus Hammer) were mislabelled and are void.*
   - **Saturation:** in a threshold kill (21 commander damage, one-shot lethal), multipliers stop stacking once a single hit is lethal — a complement below the threshold turns into a substitute above it. Measure I at the turn the deck is trying to win, and report it next to the stack curve.
   - **Stack curve** per cluster: blank the cluster, add cards back one at a time; real synergy shows rising gains for at least the first 3 cards. Cards past the peak are backups.
   - **Model coverage:** every complement link is modelled or listed "unmodelled"; unmodelled links earn no number.
9. **Land-count sweep:** Gate 5 number −2 to +3 (swapping lowest-value slots for basics); keep the best by the decision rule. Then re-run the **utility-land sweep** (Gate 3, step 5b) at the final count, so utility lands replace basics, not spells.
10. **Controlled A/B** for every change, same seeds, **with a control arm** (the same cuts filled with basics or blanks). New cards are credited only with their gain over the control.
11. Save code, policy and seeds with the deck. **No code that ran = no numbers.** Fallback: 20 logged hand goldfishes, ⚠️, DRAFT only.

**Commander tie** (within the noise bar): disruption win-by-T12, then backup %, then fewer new prints.

**Gate 10 — Write-back.** After Gates 7–8 pass on the exact list: deck tab (version, date, change log, "came in for"), Batch 2 for new prints (with rarity), print list; old version kept as a backup tab. Add a half-page **pilot guide** (mulligan rule, best openings, tutor priorities, when to fire converters, targeting and posture, the policy-search "don'ts") and a **capability line**: goldfish T10 · disruption T12 · pod win with calibration status · coverage % · engine version · ceiling (structural or model) and cause. Then the Pod-Fit verdict: ALIGNED · OVERSHOOT · UNDERGUNNED · BLIND (pod unknown, no default used).

---

## 5. ESCALATION — ceiling, strategy, theme, pod race

**Ceiling rule.** A ceiling counts only after the Gate 3 coverage bar is met and the dead-weight and land tests have run; before that it is a **model ceiling** (deck stays DRAFT, coverage shown). If three different levers each move the judge by less than the escalation bar (§1) (e.g. faster mana, more power, more evasion), the kill type is at its **structural ceiling**: stop card tuning, report the cause (e.g. one carrier hits one opponent per combat) and go to the strategy layer.

**Strategy layer** — work down in order; model every rung; stop at the first that clears the escalation bar (§1):
1. **Pilot play tuning.** Run on every finished version (not only at a ceiling) — it needs no prints.
   - **The model must expose its play as named knobs** in one `POLICY` dict, defaults = the play every earlier number used (re-run the default first: it must reproduce the last result exactly). Minimum knob set: mulligan (standard / loose / strict) · commander timing (on curve / ramp first) · cast order (ramp first / engine first) · tutor priority (evasion / double strike / biggest equipment / deck-specific engine piece) · equip order (double strike first / power first) · evasion-land use (always / only for lethal) · attack target (commander-damage focus / lowest life / biggest threat) · converter and sink timing (before / after the kill pieces) · protection (hold for the wipe / cast proactively) · any engine-specific choice (e.g. what Forgemaster fetches). Add knobs for any new mechanic the deck relies on.
   - **Protocol:** each alternative value one at a time on paired seeds (≥8,000 games, goldfish + pod disruption); anything beyond the noise bar is re-tested on fresh seeds; two winning knobs get a 2×2 before they are combined.
   - **Output:** a half-page pilot guide in the deck tab — the winning play as plain instructions, and every losing alternative that cost ≥2 points as a "don't" with its number.
   - **Limit:** opponent-aware choices (kill the fastest player first, hold removal for Krenko) can only be valued once opponents are agents in the shared engine; until then they are written as pod advice, marked ⚠️ unmodelled.
   - *Why: Wakanda v4.1 — 8 knobs tested; the default play was best or tied on all of them; the real finds were the don'ts: strict mulligan −4.8, double-strike-first tutoring −1.5.*
2. **Second kill axis from the same engine:** a converter that turns something the deck already makes into a kill on a different opponent (lifelink → Aetherflux; tokens → drain). Adding an axis re-runs Gate 2 (the kill style stays locked).
3. **Commander swap inside the identity**, each with its tailored package.
4. **Identity break** (new colour or commander family): modelled as its own deck and offered as the user's choice — never applied without them.

**Theme skill tree** (user names a theme, e.g. "fast Vibranium"): root (every form the resource takes: mana, permanents that count, triggers) → sources (every pool card that makes it; a thin list caps the theme's speed) → branches (every end-game kill that consumes it, each a minimal package on the shared core, modelled) → present the tree with numbers and status; the user picks. A chosen theme is identity: optimise inside it and show its cost in points against the best non-theme list.

**Pod race view.** Maximum capability is measured against the table. Convert the win-turn distribution into a pod win estimate from the pod's kill-turn profile.
- **Calibration method:** run each real opponent list as a plug-in on the shared engine to get its kill-turn distribution; or log ≥5 real games (turn each player won or died) and fit the race curve. Status `calibrated` or `assumed` is printed with every pod-win number; while `assumed`, the §1 decision rule applies unchanged and the opponent lists are asked for once per session.
- **Sanity check:** if every candidate scores under 5% pod win, the target is suspect, not the decks — say so before declaring any deck best.

---

## 5b. BALANCE — win rate AND fun, with guided suggestions

Win rate is not the only objective, and the stated theme is a starting point, not a cage. After Gate 9, place every serious version on **win (pod win, or disruption T12) vs fun**, and finish each Build or Tune with a **guided menu of 3–5 options**.

- **Fun score:** measured from the game logs, each part 0–100 and weighted by the user's fun profile (`mtg-engine/profiles/<user>.yaml`; Seb's defaults are in the repo):
  - Game length in the table's sweet spot (pace median ± 2 turns; default T8–T12; wins far before it are table feel-bad).
  - Non-games (screw, flood, mulligans to 5).
  - Line variety (entropy of winning lines).
  - Stacking moments (big synergy turns, comebacks).
  - Commander and theme centrality.
  - Decision density.
  - Interaction both ways.
  - Table health (stax, long solitaire turns).
  Always show the parts, never just the total.
- **Win target (Pod-Fit):** fair share plus an edge, about 25–35% pod win in a 4-player B3 pod. Above it = OVERSHOOT → offer fun-up / power-down options.
- **Theme strictness:** strict · **lean** (default: up to ~10 off-theme slots, each earning its place) · open.
- **Menu option types:** relax the theme, fun swap (same win within noise, more fun), power swap (more win, less fun, flagged), alternate kill route, alternate commander, table health, pet-card keep.
  - Each option shows: pod win Δ ± noise bar · fun Δ with the parts that moved · theme fidelity Δ · cost and new prints · rarity.
  - Only frontier options (or options within the noise bar of the frontier) are shown.
  - Red lines are never relaxed, and the honest win number is always shown.
- **Learning:** user picks and logged real games (fun 1–5, what felt good or bad, turn of each win) update the fun weights and feed L5 calibration.

**Options and free format.** Every setting (pace, bracket, budget, theme strictness, kill route, win weight, fun weights, pet cards) takes a preset, a number, a mix, or free text. Translate free text into parameters, **echo them back for confirmation**, and ask one question only if something is ambiguous. A conflict with a red line is shown, never applied silently.

**Pace exploration.** The menu adds faster / slower versions (fast pods: lower curve, cheap interaction, earlier kill; slow pods: bigger payoffs, resilience), and 3–5 pace-flex swaps to move a deck between pod nights without a rebuild. Each shows the pace sweep before and after.

## 6. FAILURE MODES (each has cost a build — guardrail in brackets)

1 Commander reverse-engineered from a pasted list, Hapatra [intake] · 2 Engine without a kill, Arcum 37–44% no-win by T14 [Gate 2] · 3 Set-scan stuffing, 1-for-1 swaps [Gate 4 packages] · 4 Plan drift mid-build [kill style locked; new axis = Gate 2 re-run] · 5 Popularity seeding [seeds are candidates only] · 6 Card fact from memory: Cranial Plating's {B}{B} in mono-blue, Synthesizer "costs {2}" [Law 1] · 7 Metrics that can't fail: "≥3 links" passed Arcum at 91% [scanned links, kill-link %, model targets] · 8 Single point of failure: Arcum T10 78% → 18% without Synthesizer [single-card test] · 9 Leave-one-out cutting backups [card + backup rule] · 10 Pilot bug read as weak card: Sol Ring "negative" [policy audit] · 11 Generous pilot gaming targets [policy before run, code + seeds saved] · 12 Staples as "B3 filler" [tags or generic slots] · 13 Uncounted Game Changer: Giada 5 labelled 3 [count across 100] · 14 Combo missed by a clean Spellbook read [risky-card read + forbidden adds] · 15 Count rot, silent substitution [Gate 8] · 16 Soft disruption profile: Arcum 81% → 28% once its engine artifact died [targeted removal] · 17 Hub-inflated synergy score [kill-link % excludes commander and top 10% hubs] · 18 Linear gates forcing invented numbers [provisional picks, Gate 9 decides, DRAFT] · 19 Substitutes counted as synergy [2×2 pair test, I < 0 = substitute] · 20 Unflagged anti-synergy: Colossus Hammer "loses flying" on Sigarda [anti-synergy scan] · 21 Commander picked after a shared 99 [clause targets, tailored packages] · 22 Clusters padded past the peak: double strike +6.0 → +1.1 [stack curve] · 23 Stacking into overkill: −12 points [bottleneck first] · 24 Mana sinks stealing kill mana [sinks last in policy] · 25 Endless swaps at a structural ceiling [ceiling rule → strategy layer] · 26 Converters never searched: Aetherflux [resource map] · 27 Winner's curse: +5.5 → +1.3 [top-30 re-test] · 28 Swaps as the only lever [strategy layer] · 29 Over-mulliganing for pieces: −7 [policy search] · 30 Optimising past the user's theme [theme = identity] · 31 Symmetric gift credited only to us: Selvala, Explorer Returned [Law 4, who-benefits] · 32 Checks skipped on exploratory builds [Gates 7–8 on every modelled build] · 33 Snowball treated as infinite, or as fast: T'Challa snowball assembled 0.5% by T8 [§2 test; report assembly rate, pieces in the 99, turns to kill] · 34 "At ceiling" on 4% coverage, 33 of 42 community cards untested, 8 of 132 commanders [coverage bar, seeds, commander sweep, model-ceiling label] · 35 Decks compared across sims or against an uncalibrated pod [shared engine, calibration status, sanity check] · 36 Dead weight and a short mana base: Wakanda v2, 4 cards below blank, 33 lands vs 36 [dead-weight test, land sweep] · 37 New cards credited with gains from the cuts: +4.7 total, +2.8 from cuts [control arm] · 38 Version written back before Gates 7–8: Wakanda v3, an unreleased card unflagged [Gate 8 legality, re-run before write-back] · 39 Decisions on noise: one-run gaps, 4-run pair surplus [noise bar, paired SE] · 40 Voltron kill speed understated by ignoring commander damage [engine tracks 21 per commander per opponent] · 41 Banned card passing Gate 8 because only `not_legal` was checked [`legal` required] · 42 Re-test on the screen's own seeds keeping its selection bias [fresh seeds] · 43 Circular baseline — removal ranked by a test that needs the removal run [Gate 2.5 order] · 44 Pair-test sign inverted — redundancy read as synergy for 15 versions [I = loss(A) + loss(B) − loss(A+B); validated on two evasion cards] · 45 Pair arms with different filler in the other slot (Wakanda pair search: every pair looked +4 complementary until the single-card arms held the second slot constant) [full 2×2, identical filler] · 46 Universe sweep blind to whole card types: the Wakanda sweep read only equipment, auras and rocks (612 cards). It skipped every creature, instant and non-aura enchantment, 1,169 other artifacts and every land (0%) [per-type coverage bar, theme types ≥40%, utility-land sweep] · 47 Spell modes unscored: the first Wakanda sweeps coded no flicker, phasing or draw spells, sorceries sat at 12%, and removal had no value in the engine [spell sweep with role-matched swaps; phasing ≠ flicker in the engine; removal efficiency table until opponent threats are modelled] · 48 One-off sim that can't grow: the Wakanda sim hard-codes ~150 cards and one kill route, so pointing it at the full card pool would score cards it can't play [§8 shared library + generic engine + regression set]

---

## 7. OUTPUT FORMAT & STOP CONDITION

```
DECK: [name]   VERSION: YYYY-MM-DD-v[N]   MODE: build|audit|tune
INTAKE  Cmdr [..] | Pod [default|3 decks] | Kill style [..] | B3, GC 3 | New-print cap [N] | Identity/theme [..]
G1  Colours [..] | clause targets [..] | commander sweep considered/scored/modelled [N/N/N]
G2  Kill [primary, T?] | Backup w/o commander [..] | Engine | Fuel | Protect | core pairs (mechanics) [..] | slot budget [..]
G2.5 v0 baseline: goldfish T10 [x%] | disruption T12 [x%] | bottleneck [..] | lowest-value slots [..]
G3  Queries [N] | seeds [N]: tested/rejected/GAP [N/N/N] | theme hits [N]: tested/rejected [N/N] | coded [N, x%] | screened [N] | top-30 held [cards]
G4  Packages [..] | links complement/substitute/anti [N/N/N, fixed?] | kill-link [x%] | redundancy [n per piece]
G5  Lands formula [N] → sweep best [N] | utility lands screened [N], kept [..] | colour sources [..] | rocks [N] | reducers [N] | curve warnings [..]
G6  Interaction [N] | protection [N]
G7  GC [n/3: names] | combos [none/N] | forbidden adds [N] | snowballs [line, pieces in 99, assembly T8/T10] | Spellbook tag [.. = meaning] | OVERSHOOT [Y/N]
G8  100 ✓ (oracle_id) | names [n/n] | CI ✓ | legality [✓ / release dates] | who-benefits [hits, classes] | gift speed-up [x turns]
G9  Engine [version] | goldfish T10 [x%] T12 [x%] stall [x%] | disruption T12 [x%] (target: ..) | backup [x%] | cmdr-out [x%] | T6 [x%] | clause targets [met?]
    SPOF [..] | dead weight [..] | pair interaction I [±x ± SE, complement/substitute] | stack curves [..] | links modelled [x%] | A/B [±x ± SE] vs control [±x] | loops [n/3]
G10 Workbook [tabs] | Batch 2 [+N prints] | capability line written
POD  Pod win [x%] ([calibrated/assumed]) | ceiling [structural/model, cause] | strategy rung [..] | Pod-Fit [verdict]
APPENDIX: decklist by package · link CSV · combo/snowball disclosures · policy + seeds
```

**DONE (Build) when:** intake locked · Gate 2 written before cards · Gate 3 per-type coverage bar met (lands included), utility-land sweep run, zero seed GAP · core pairs show positive interaction I beyond noise (true complements) · zero unresolved anti-synergies · kill-link ≥85%, redundancy ≥3 · all Gate 9 targets met · dead-weight and land tests run · Gates 7–8 passed on the final list · calibration status stated · workbook written. Otherwise DRAFT, with what failed.

## 8. UNIVERSE ROADMAP — one card library, one engine, growing with every build

**Target:** every Commander-legal card. On 2026-11-09 that was 32,643 cards (31,408 non-land, 1,223 non-basic lands); re-count from Scryfall (`legal:commander`) each build. Coverage is reported two ways: against the deck's identity pool (the Gate 3 bar) and against the full universe (roadmap progress).

| Layer | What it is | Done when | Status (2026-11-09) |
|---|---|---|---|
| **L1 Card-effect library** | One record per `oracle_id`: effect primitives from a fixed vocabulary, every mode (MDFC, channel, adventure, cycling), confidence (`auto` / `hand-verified` / `unmodelled: reason`), parser version | ≥70% of non-land cards **playable**: at least one handler-backed primitive from a class that passed its 20-card spot-check (≤5% false positives). Tags, keyword-only bodies and lands don't count; clause-level coverage is measured once L2 handlers exist | Parser 1.6 over all 32,643 cards: 58.2% playable (bar not met); per-face modes; repo `mtg-engine` |
| **L2 Generic engine** | Plays any deck from library primitives. Card-specific behaviour lives in the library as a named plug-in, never in the engine | Reproduces every regression deck within the noise bar | Wakanda one-off sim with generic GENX / LANDX hooks |
| **L3 Win-route modules** | Voltron · go-wide tokens · drain / aristocrats · spellslinger · combo (assembly turn from Spellbook pieces) · alt-win | A deck is judged only on modules that exist; anything else is a model ceiling | Voltron only |
| **L4 Opponent agents** | Pod decks run as engine decks that attack, remove and present threats. Removal is valued by how much it delays an opponent's clock. Politics follow the targeting policy | Pod win computed from agents, not an archetype curve | Archetype curves only; removal ranked by an efficiency table |
| **L5 Calibration** | Real opponent lists plus logged games | Each pod `calibrated` (§5) | Assumed lists |

**Primitive vocabulary (start set; extend, never bypass):**
- **Mana:** land, dork, rock, ritual, land ramp, cost reducer.
- **Cards:** draw (spell / engine / trigger), tutor to hand / battlefield / top, recursion.
- **Board:** body, token, +1/+1 counters, doubler, anthem, keyword grant, equipment / aura attach, copy.
- **Combat:** trick, extra combat, evasion.
- **Interaction:** removal by target type and speed, wipe, counterspell, stax piece.
- **Protection:** phase, flicker, hexproof, indestructible, regenerate.
- **Life and triggers:** drain, lifegain, converter, sacrifice outlet; ETB / attack / death / cast triggers.
- **Flags:** monarch / initiative (red-line), alt-win.
- Anything else is tagged `unmodelled: reason`.

**Growth rule (demand-driven, never big-bang).** Every Build or Tune adds four things before Gate 10:
1. Its identity's cards to the library.
2. Any primitive it needs, with an engine handler.
3. Its win-route module, if it's new.
4. A regression entry: deck list, seeds, and the goldfish T10 and disruption T12 results.

No new one-off sims. A deck needing a new mechanic adds a primitive to the library and a handler to the engine. When choosing what to build next, prefer decks that bring uncovered colours or archetypes (e.g. Lathril → black, tokens, drain; Maralen → blue, spells). Report universe coverage after each.

**Regression set.** Every engine change re-runs all regression decks; a drift beyond the noise bar blocks the change until it's explained. Starting entry: **Wakanda v4.1** (T'Challa): disruption T12 ≈ 73%, goldfish T10 ≈ 83%, pod-profile T12 ≈ 73%.

**Quality.**
- Each parser version spot-checks 20 random cards per class. More than 5% false positives in a class blocks that class until it's fixed.
- Strip reminder text; reject tribe-only, conditional and until-end-of-turn matches for static effects.
- Cache records by `oracle_id`; re-parse only when the parser version changes.
- Hand-verified records are never overwritten by the parser.

**Storage.** The workspace is wiped between sessions, so the library, engine and regression set live in a durable store Seb chooses. Each session loads them first and saves additions at Gate 10. If no store is reachable, rebuild from Scryfall and the parser, and say so in the capability line.

**Compute.** Pre-filter by identity and role; staged screens (§1); cap at ~1,000 full-engine candidates per build; run long sweeps in the background.

## Version log
v5.12 (2026-11-09): adjustable pace (preset / median / mix / free text) drives every turn number, the fun sweet spot and the table model; pace sweep (pod win at table medians T5–T12) and pace-fit label always reported; faster/slower versions and pace-flex swaps in the menu; every setting accepts preset, number, mix or free text with echo-back.
v5.11 (2026-11-09): §5b balance layer — win vs fun frontier, measured fun score with visible parts, Pod-Fit win target 25–35%, theme strictness (default lean), guided menu of 3–5 options with win/fun/theme deltas, learning from picks and real-game logs; red lines never relaxed.
v5.10 (2026-11-09): L1 coverage bar redefined as non-land **playable** coverage from spot-check-passed classes (tags, keyword-only bodies and lands excluded) after an independent audit showed the old 71% counted tags; status updated to parser 1.6 (58.2%).
v5.9 (2026-11-09): §8 universe roadmap — shared card-effect library by `oracle_id` (primitive vocabulary, modes, confidence, parser version), generic engine with card plug-ins, win-route modules, opponent agents, calibration; demand-driven growth rule (every build adds cards, primitives, module, regression entry; no new one-off sims); regression set starting with Wakanda v4.1; parser quality gate (20-card spot check per class, ≤5% false positives); durable storage; universe progress in the coverage report; failure mode #48.
v5.8 (2026-11-09): spells covered by mode (removal, draw spells, tricks, flicker, phasing, channel / cycling / MDFC coded in both modes); spell sweep with role-matched swaps that keep the floors; phasing vs flicker rules the engine must model (CR 702.26, 400.7, 903.9); removal ranked by an efficiency table until opponent threats are modelled; failure mode #47.
v5.7 (2026-11-09): the card pool covers every card type, lands included. Per-type coverage bar (≥25% each, theme types ≥40%, plain bodies excluded); wider auto-code classes plus false-positive filters; utility-land sweep (role-coded, swapped against basics, basic-for-basic control, re-run at the final land count); coverage report by type; failure mode #46.
v5.6 (2026-11-09): pilot play tuning made executable — POLICY knobs in the model (defaults reproduce earlier results), minimum knob set, one-at-a-time protocol with fresh-seed re-test and 2×2 before combining, pilot-guide output with don'ts, limit on opponent-aware choices; run on every finished version.
v5.5 (2026-11-09): pair test corrected — full 2×2 on identical filler, I = f(AB) − f(A) − f(B) + f(0); positive = complement, negative = substitute (the sign was inverted before); saturation note for threshold kills; failure modes #44–45.
v5.4 (2026-11-09): cut slots chosen by least synergy (link scan + oracle read + substitutes past peak), confirmed by the model; dead-weight test demoted to a warning.
v5.3 (2026-11-09): Seb's pod recorded (Krenko / Sephiroth / Y'shtola, assumed EDHREC lists) with modelled win turns, the table curve (median T10) and a pod-specific disruption profile incl. artifact wipes and edicts; old turn-5 curve retired.
v5.2 (2026-11-09): Seb's play-style red-lines (no monarch / initiative engines); legality checked on every printing, strictest wins.
v5.1 (2026-11-09): second independent audit — banned cards now BLOCKED (`legal` required); Gate 2.5 run order fixes the circular removal ranking; top-30 re-tests on fresh seeds; dead-weight test only flags, role test is the only cut rule, lands excluded; house rules beat Spellbook tags (snowballs, allowed 3-card combos); kill-link hubs excluded from the denominator only; one escalation bar for ceiling and strategy; commander-sweep score formula with a true range, subset identities and partner/Background pairs; pod win's role as judge when calibrated; gift modifier feeds opponent clocks; engine adds commander tax, command-zone return, initiative, per-commander damage; mulligan rules after the first; package screens for cluster cards; seed list counts independent sources; targeting tie-break; workload caching and staged screens; colour identity from Scryfall; slot arithmetic includes the commander; failure modes #41–43.
v5.0 (2026-11-09): restructure after independent audit — one decision rule (disruption judges, goldfish vetoes, noise bar 2 × paired SE); per-mode stop conditions; tooling fallbacks; Gate 2.5 baseline run so screens no longer depend on later gates; core pairs as mechanics; commander-sweep scoring formula and package-only modelling; screen budget (~400 cards) separate from the 25% coding bar; one targeted-removal rule; commander damage, opponent threats, archenemy and a pilot targeting policy in the engine; calibration method; snowball test covers resource-capped loops; Spellbook tags read at run time; links scanned from oracle text; ceiling → strategy layer, model ceiling = DRAFT; about a third shorter (stories kept only in the failure list); failure modes #39–40. Also logs earlier unlogged rules: owned-vs-new-print preference, new-print cap, reprint aliases.
v4.4 (2026-11-09): dead-weight test, land sweep, control arm, interaction protection, monarch in who-benefits, unreleased-card legality, Gates 7–8 before write-back.
v4.3 (2026-11-08): community seed list, theme-name sweep, all-type auto-coding with coverage bar, commander sweep, shared engine, calibration status.
v4.2 / v4.1 (2026-11-08): snowball ruling; Law 4 and the who-benefits audit.
v4.0 – v3.1 (2026-11-08): theme tree, strategy layer, universe sweep, ceiling rule, bottleneck stacking, stacking synergy, synergy pass, first live build, targeted removal, clean rewrite.