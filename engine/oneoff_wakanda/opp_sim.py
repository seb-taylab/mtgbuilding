"""Opponent win-turn models for Seb's assumed pod (9 Nov 2026).
Lists: EDHREC average decks (Krenko, Mob Boss 45,162 decks; Sephiroth, Fabled SOLDIER 32,463; Y'shtola, Night's Blessed),
trimmed to honest B3 (<=3 Game Changers, house rules: no 2-card infinites). Card text verified on Scryfall.
Each model returns the turn the opponent would WIN (all three other players dead), against a table that interacts:
  - its key engine permanent (commander) is removed once, turn 4-6, with prob P_CMD (re-cast +2 tax)
  - a creature wipe from someone else lands on turn 5-7 with prob P_WIPE
  - a combat-damage tax (blockers / Propaganda-type) is folded into each model as stated.
Opponents' life: 3 x 40. Simplifications are stated inline; these are archetype models, not full decklist sims.
"""
import random, collections

P_CMD = 0.5     # someone removes this opponent's commander once, turns 4-6
P_WIPE = 0.6    # someone else wipes creatures on turns 5-7

def mana_curve(rng, lands=35, ramp=6, deck=99):
    """Mana available on each turn 1..16 from a hypergeometric land/ramp draw (on the play/draw mixed)."""
    lib = ['L'] * lands + ['R'] * ramp + ['x'] * (deck - lands - ramp); rng.shuffle(lib)
    hand = lib[:7]; lib = lib[7:]
    L = R = 0; out = []
    for T in range(1, 17):
        if T > 1 or rng.random() < 0.75: hand.append(lib.pop(0))
        if 'L' in hand: hand.remove('L'); L += 1
        if 'R' in hand and L + R >= 2: hand.remove('R'); R += 1
        out.append(L + R)
    return out

def table_events(rng):
    cmd_T = rng.choice([4, 5, 6]) if rng.random() < P_CMD else 99
    wipe_T = rng.choice([5, 6, 7]) if rng.random() < P_WIPE else 99
    return cmd_T, wipe_T

def krenko(rng):
    """Krenko, Mob Boss ({2}{R}{R}): {T}: create X 1/1 Goblins, X = Goblins you control.
    List: 35 lands, ~6 ramp (Sol Ring, Signet, Ruby Medallion, Skirk Prospector, Brightstone Ritual, Hazoret's Monument),
    ~31 Goblins, haste: Lightning Greaves, Swiftfoot Boots, Goblin Warchief, Thousand-Year Elixir (also an untapper);
    damage payoffs: Impact Tremors (1/ETB each opp), Purphoros (2/ETB each opp), Goblin Bombardment (sac: 1 any target),
    Shared Animosity / Coat of Arms / Goblin King / Chieftain / Battle Hymn for the alpha."""
    mana = mana_curve(rng, 35, 6)
    lib = (['haste'] * 4 + ['tremor'] * 2 + ['bomb'] * 1 + ['anthem'] * 5 + ['gob'] * 30 + ['x'] * 57); rng.shuffle(lib)
    hand = lib[:7]; lib = lib[7:]
    cmd_T, wipe_T = table_events(rng)
    on = False; tax = 0; sick = True; g_other = 0; tok = 0; tok_ready = 0
    have = collections.Counter(); dmg = 0  # damage dealt to EACH opponent (spread evenly)
    for T in range(1, 17):
        hand.append(lib.pop(0))
        m = mana[T - 1]
        # cast permanents (cheap first)
        for k in ('haste', 'tremor', 'bomb', 'anthem'):
            while k in hand and m >= 2:
                hand.remove(k); have[k] += 1; m -= 2
        if not on and m >= 4 + tax:
            on = True; sick = not have['haste']; m -= 4 + tax
        while 'gob' in hand and m >= 2:
            hand.remove('gob'); g_other += 1; m -= 2
            dmg += have['tremor'] * 1.5   # Impact Tremors 1 / Purphoros 2, averaged
        # combat with last turn's tokens + goblins (blockers: 2 per opponent soak the biggest; tokens 1/1)
        atk = tok_ready + g_other
        if atk:
            power = 1 + (2 if have['anthem'] else 0) + (atk // 4 if have['anthem'] >= 2 else 0)
            through = max(0, atk - 6) * power
            dmg += through / 3
        # Krenko activations
        if on and not sick:
            acts = 1 + (1 if have['haste'] and m >= 1 and rng.random() < 0.25 else 0)  # Elixir untap sometimes
            for _ in range(acts):
                x = 1 + g_other + tok
                tok += x
                dmg += have['tremor'] * 1.5 * x
        sick = False
        tok_ready = tok
        # Goblin Bombardment finisher: sac everything if it kills
        if have['bomb'] and (tok + g_other) / 3 + dmg >= 40: return T
        if dmg >= 40: return T
        # table interaction
        if T == cmd_T and on: on = False; tax += 2
        if T == wipe_T: tok = tok_ready = g_other = 0
    return 99

def sephiroth(rng):
    """Sephiroth, Fabled SOLDIER ({2}{B}): enters/attacks: may sac a creature to draw; whenever another creature dies,
    TARGET opponent loses 1 (you gain 1); 4th time in a turn it transforms (emblem: every death drains a target opponent).
    List: ~33 lands, 6 ramp (Sol Ring, Signet, Jet Medallion, Dark Ritual, Crypt Ghast, Cabal Coffers),
    drainers each-opponent: Zulaport Cutthroat, Bastion of Remembrance, Syr Konrad, Gray Merchant (burst), Dictate/Grave Pact (removal);
    single-target: Blood Artist; sac outlets: Viscera Seer, Carrion Feeder, Ashnod's / Phyrexian Altar, Goblin... ;
    fodder: Bitterblossom, Dreadhorde Invasion, recursive Bloodghast / Gravecrawler / Reassembling Skeleton;
    3-card-plus line: Gravecrawler + Phyrexian Altar + another Zombie with any drainer = unbounded drain (allowed: not 2-card).
    Tutors: Demonic Tutor, Diabolic Intent, Victimize."""
    mana = mana_curve(rng, 33, 6)
    lib = (['drainE'] * 4 + ['outlet'] * 4 + ['fodder'] * 10 + ['tutor'] * 3 + ['crawler'] + ['paltar'] + ['zombie'] * 3 + ['gray'] + ['x'] * 72); rng.shuffle(lib)
    hand = lib[:7]; lib = lib[7:]
    cmd_T, wipe_T = table_events(rng)
    on = False; tax = 0; have = collections.Counter(); bodies = 0; dmg = 0.0; emblem = False
    for T in range(1, 17):
        hand.append(lib.pop(0))
        m = mana[T - 1]
        if 'tutor' in hand and m >= 2:
            hand.remove('tutor'); m -= 2
            need = next((k for k in ('paltar', 'crawler', 'outlet', 'drainE') if have[k] == 0 and k not in hand and k in lib), None)
            if need: lib.remove(need); hand.append(need)
        if not on and m >= 3 + tax: on = True; m -= 3 + tax
        for k in ('outlet', 'paltar', 'drainE', 'crawler', 'zombie', 'fodder', 'gray'):
            while k in hand and m >= (2 if k != 'gray' else 4):
                hand.remove(k); have[k] += 1; m -= (2 if k != 'gray' else 4)
                if k in ('fodder', 'zombie', 'crawler'): bodies += 2 if k == 'fodder' else 1
                if k == 'gray': dmg += 3
        drain_each = have['drainE'] + (0.34 if on else 0) + (0.34 * 1 if emblem else 0)  # single-target drains spread over 3
        # 3-card-plus loop: unbounded drain once assembled with any drainer
        if have['crawler'] and have['paltar'] and (have['zombie'] or on) and (have['drainE'] or on):
            return T
        # ordinary turn: sacrifice the fodder made this turn (recursion keeps ~2 bodies a turn coming back)
        if have['outlet'] or have['paltar']:
            deaths = min(bodies, 2 + have['fodder'])
            dmg += deaths * drain_each
            if on and deaths >= 4: emblem = True
            bodies = max(1, bodies - deaths) + have['fodder']
        # attacks are small; skip
        if dmg >= 40: return T
        if T == cmd_T and on: on = False; tax += 2
        if T == wipe_T: bodies = 0; dmg += (have['drainE'] + (0.34 if on else 0)) * 3  # deaths from the wipe drain too
    return 99

def yshtola(rng):
    """Y'shtola, Night's Blessed ({1}{W}{U}{B}): whenever you cast a noncreature spell with MV>=3, 2 damage to each
    opponent and you gain 2; end step: draw if a player lost 4+ life this turn.
    List: ~37 lands, 8 rocks, ~25 noncreature spells with MV>=3, counters/removal/wipes, finishers Exsanguinate,
    Syphon Mind, Sheoldred, Bolas's Citadel (GC). Plays control: holds mana up, so ~1 qualifying spell a turn on average,
    rising with mana."""
    mana = mana_curve(rng, 37, 8)
    cmd_T, wipe_T = table_events(rng)
    on = False; tax = 0; dmg = 0.0
    for T in range(1, 17):
        m = mana[T - 1]
        if not on and m >= 4 + tax: on = True; m -= 4 + tax
        if on:
            spells = 1 if m < 5 else (2 if m < 8 else 3)
            spells = sum(1 for _ in range(spells) if rng.random() < 0.6)   # the deck must draw them and hold counters
            dmg += 2 * spells
            if m >= 8 and rng.random() < 0.15: dmg += m - 2               # Exsanguinate-style burst
        if dmg >= 40: return T
        if T == cmd_T and on: on = False; tax += 2
    return 99

MODELS = {'Krenko, Mob Boss': krenko, 'Sephiroth, Fabled SOLDIER': sephiroth, "Y'shtola, Night's Blessed": yshtola}

def dists(N=8000, seed=7):
    rng = random.Random(seed); out = {}
    for n, f in MODELS.items():
        out[n] = [f(rng) for _ in range(N)]
    return out

if __name__ == '__main__':
    D = dists()
    for n, v in D.items():
        c = collections.Counter(v); N = len(v)
        cum = lambda t: round(100 * sum(x for k, x in c.items() if k <= t) / N, 1)
        print(f"{n:28s} win by T5 {cum(5)} T6 {cum(6)} T7 {cum(7)} T8 {cum(8)} T10 {cum(10)} T12 {cum(12)} | median T{sorted(v)[N//2]}")
    tab = [min(a, b, c) for a, b, c in zip(*D.values())]
    c = collections.Counter(tab); N = len(tab)
    cum = lambda t: round(100 * sum(x for k, x in c.items() if k <= t) / N, 1)
    print(f"{'TABLE (first opponent win)':28s} by T5 {cum(5)} T6 {cum(6)} T7 {cum(7)} T8 {cum(8)} T10 {cum(10)} | median T{sorted(tab)[N//2]}")
