"""GW equipment-voltron model (Wakanda), written to the v3.2 policy below.
POLICY (pre-registered):
- Mulligan: London, first one free. Keep 3-5 lands, or 2 lands + a mana source; plus >=1 engine/kill card (commander counts if MV<=4).
- Main phase order: land (fixing first) -> mana sources -> commander -> tutors -> equipment (kill pieces before value) -> bodies -> equip.
- Tutor picks, in order: evasion if the carrier has none -> a double-strike piece -> Colossus Hammer if a free/cheap equip route exists
  -> Commander's Plate -> Sword of Fire and Ice -> other power.
- Carrier = commander if on battlefield, else the best body (flyers first). All equipment goes on the carrier.
- The carrier attacks every turn it can; the pilot always takes the earliest win (focus the opponent closest to death).
- Blocks: no evasion -> 50% chance it is chump-blocked (trample still pushes excess). Flying -> 15% chump by a flyer/reach. Unblockable/hexproof Ring -> never.
Simplifications: no opposing life gain, no combat tricks, opponents never race us; Jitte = +2 power after its first hit;
Sword of War and Peace = +4 damage (avg hand); The One Ring draws 1/2/3; Top = +0.3 card/turn; Sylvan +1 card/turn while life > 20.
"""
import json, random, collections, re, os
H = os.path.dirname(os.path.abspath(__file__))
LANDX = {}  # auto-coded utility lands (lands/landcode.py): name -> effects
GENX = {}   # wider auto-coded classes (seeds/autocode2.py): name -> effects
GENA = {}   # active auto-coded candidates: name -> parsed effects
C = json.load(open(os.path.join(H, 'db.json')))
for b, k in (('Forest', 'G'), ('Plains', 'W')): C[b] = dict(cost='', mv=0, type='Basic Land', p=None, t=None, text='', prod=[k])
C['Dawnsire, Sunstar Dreadnought'] = dict(cost='{5}', mv=5, type='Legendary Artifact — Spacecraft', p='20', t='20', text='Station', prod=[])
C['Black Panther, Most Dangerous'] = dict(cost='{2}{W}', mv=3, type='Legendary Creature — Human Warrior Hero', p='3', t='3', text='', prod=[])
C['Okoye, Mighty and Adored'] = dict(cost='{2}{G}{W}', mv=4, type='Legendary Creature — Human Warrior Hero', p='3', t='3', text='', prod=[])
C["M'Baku, Jabari Chieftain"] = dict(cost='{1}{G}{G}', mv=3, type='Legendary Creature — Human Noble Warrior', p='3', t='3', text='', prod=[])
C['Nakia, Wakandan Operative'] = dict(cost='{2}{G}', mv=3, type='Legendary Creature — Human Warrior Hero', p='2', t='3', text='', prod=[])
C['The Spear of Bashenga'] = dict(cost='{4}{W}', mv=5, type='Legendary Artifact — Equipment', p='', t='', text='Equip {2}', prod=[])
C['Bast, Panther Goddess'] = dict(cost='{2}{G}{W}', mv=4, type='Legendary Creature — Cat God', p='4', t='4', text='', prod=[])
C["W'Kabi, Shield of the Nation"] = dict(cost='{1}{G}', mv=2, type='Legendary Creature — Human Warrior Hero', p='2', t='2', text='', prod=[])
C['Darksteel Plate'] = dict(cost='{3}', mv=3, type='Artifact — Equipment', p='', t='', text='Equip {2}', prod=[])
C['Swiftfoot Boots'] = dict(cost='{2}', mv=2, type='Artifact — Equipment', p='', t='', text='Equip {2}', prod=[])
C['Darksteel Plate']['text']='Equip {2}'; C['Swiftfoot Boots']['text']='Equip {1}'
for _n, _c, _mv, _t, _p, _tt in (('Kuldotha Forgemaster', '{5}', 5, 'Artifact Creature — Construct', '3', '5'), ('Walking Ballista', '{X}{X}', 0, 'Artifact Creature — Construct', '0', '0'),
        ('Inspiring Statuary', '{3}', 3, 'Artifact', '', ''), ('Teleportation Circle', '{3}{W}', 4, 'Enchantment', '', '')):
    C.setdefault(_n, dict(cost=_c, mv=_mv, type=_t, p=_p, t=_tt, text='', prod=[]))
import json as _json, os as _os
_sp = os.path.join(H, 'data', 'seeddb.json')
if _os.path.exists(_sp):
    for _n, _c in _json.load(open(_sp)).items():
        if _n not in C: C[_n] = dict(cost=_c['cost'] or '', mv=_c['mv'], type=_c['type'], p=_c['p'], t=_c['t'], text=_c['text'], prod=[])
C['Steel Seraph']['cost'] = '{1}{W}{W}'; C['Steel Seraph']['mv'] = 3          # cast as prototype
C['Germ token'] = dict(cost='', mv=0, type='Token Creature — Phyrexian Germ', p='0', t='0', text='', prod=[])
C['Hero token'] = dict(cost='', mv=0, type='Token Creature — Hero', p='1', t='1', text='', prod=[])
def parse(c):
    s = C[c]['cost'] or ''
    g = sum(int(x) for x in re.findall(r'\{(\d+)\}', s))
    return g, len(re.findall(r'\{G\}', s)), len(re.findall(r'\{W\}', s)), len(re.findall(r'\{G/W\}', s))
def land(c): return 'Land' in C[c]['type'] and 'Creature' not in C[c]['type']
def cre(c): return 'Creature' in C[c]['type']
def eq(c): return 'Equipment' in C[c]['type']
def art(c): return 'Artifact' in C[c]['type']
def P0(c):
    try: return int(C[c]['p'])
    except Exception: return 0
def pw(c):
    try: return int(C[c]['p'])
    except: return 0
def equip_cost(c, carrier, cmd):
    t = C[c]['text']
    if c == "Commander's Plate" and carrier == cmd: return 3
    if c == 'Blackblade Reforged' and carrier and 'Legendary' in C[carrier]['type']: return 3
    if c == 'Hulkbuster Armor': return 3 if carrier and 'Hero' in C[carrier]['type'] else 6
    m = re.findall(r'Equip \{(\d+)\}', t)
    return int(m[-1]) if m else 2
DORK = {'Birds of Paradise': 'A', 'Llanowar Elves': 'G', 'Elvish Mystic': 'G', "Avacyn's Pilgrim": 'W'}
ROCK = {'Chrome Mox': ('A', 1), 'Mox Diamond': ('A', 1), 'Sol Ring': ('C', 2), 'Arcane Signet': ('A', 1), 'Talisman of Unity': ('A', 1), 'Mox Opal': ('A', 1)}
RAMP = {"Nature's Lore": 1, 'Three Visits': 1}
DS = {'Fireshrieker', 'Holy Avenger', 'Genji Glove', 'Brass Knuckles'}
POWER = {'Batterskull': 4, 'Panther Habit': 0, 'Hulkbuster Armor': 0, 'The Spear of Bashenga': 2, 'Darksteel Plate': 0, 'Swiftfoot Boots': 0, 'Gold Pan': 1, 'Kaldra Compleat': 5, 'Hammer of Nazahn': 2, 'Colossus Hammer': 10, "Commander's Plate": 3, 'Sword of Fire and Ice': 2, 'Sword of War and Peace': 2, 'Shadowspear': 1,
         'Vibranium Strike Gauntlets': 3, "Umezawa's Jitte": 0, 'Grafted Exoskeleton': 2, "Conqueror's Flail": 2, 'Nettlecyst': 0, 'Blackblade Reforged': 0, "Swordsman's Steel": 0}
EVADE = {"Bilbo's Ring": 'unblock', 'Shadowspear': 'trample', 'Vibranium Strike Gauntlets': 'trample'}
HOLD_VIB = {'Walking Ballista'}
TUTOR_HAND = {"Steelshaper's Gift", 'Federation Resupply'}
PROTECT_WIPE = {"Teferi's Protection": 5, 'Clever Concealment': 4, 'Heroic Intervention': 2, 'Flawless Maneuver': 3}
HOLD = set(PROTECT_WIPE) | {'Swords to Plowshares', 'Path to Exile', 'Dispatch', 'Generous Gift', 'Beast Within', 'Force of Vigor', 'Reprieve',
                            'Silence', "Orim's Chant", 'Vanquish the Horde', "Sigarda's Aid"}
HOLD.add('Walking Ballista')
BODY_RANK = ['Germ token', 'Black Panther, Wakandan King', 'Guidelight Synergist', 'Indomitable Archangel', 'Hero token', 'Tireless Tracker', 'Digsite Engineer', 'Storm, Queen of Wakanda', 'Armored Skyhunter', 'Brightglass Gearhulk', 'Stonehewer Giant', 'Captain America, Liberator',
             "T'Challa, the Black Panther", 'Shuri, the Black Panther', 'Sigarda, Host of Herons', 'Cloud, Midgar Mercenary', 'Ranger-Captain of Eos',
             'Janice Rand, Essential Aide', 'Ardenn, Intrepid Archaeologist', 'Puresteel Paladin', 'Stoneforge Mystic', 'Sram, Senior Edificer']

POLICY = dict(mull='standard', cmd_first=True, cast='ramp_first', tutor='evasion_first', equip='ds_first',
              passage='always', target='cmd_damage', forgemaster='kaldra')
KNOBS = dict(mull=['standard', 'loose', 'strict'], cmd_first=[True, False], cast=['ramp_first', 'engine_first'],
             tutor=['evasion_first', 'ds_first', 'kaldra_first', 'power_first'], equip=['ds_first', 'power_first'],
             passage=['always', 'lethal_only'], target=['cmd_damage', 'lowest_life'], forgemaster=['kaldra', 'best_tutor'])
def game(rng, deck, cmd, mode='gold', maxT=14, stats=None, remove=()):
    lib = [c for c in deck if c != cmd]
    for r in remove:
        if r in lib: lib.remove(r)
    rng.shuffle(lib)
    hand = []
    for a in range(4):
        hand = lib[:7]; L = sum(land(c) for c in hand)
        src = sum(c in DORK or c in ROCK for c in hand)
        piece = any(c in DS or c in POWER or c in EVADE or c in TUTOR_HAND or c in ('Stoneforge Mystic', 'Stonehewer Giant', 'Cloud, Midgar Mercenary') for c in hand)
        if POLICY['mull'] == 'loose': keep = 2 <= L <= 5
        elif POLICY['mull'] == 'strict': keep = 3 <= L <= 5 and piece
        else: keep = (3 <= L <= 5 or (L == 2 and src)) and (piece or C[cmd]['mv'] <= 4)
        if keep or a == 3:
            lib = lib[7:]; bottom = max(0, a - 1)   # first mulligan free
            for _ in range(bottom):
                hand.sort(key=lambda c: (not land(c) and C[c]['mv'] < 4, -C[c]['mv'])); lib.append(hand.pop(0))
            break
        rng.shuffle(lib)
    on_draw = rng.random() < 0.75
    lands = []; bf = {}   # name -> turn entered
    equips = {}           # equipment name -> carrier or None
    cmd_on = False; cmd_T = 99; tax = 0; T = 0; life = 40
    opp = [40, 40, 40]; cdmg = [0, 0, 0]; poison = [0, 0, 0]
    jitte_hit = False; ring_ct = 0; arttok = [0]; servos = [0]; vib = [0, 0]; tch = [0]; bpk = [0]; bpk_on = [0]; charge = [0]; ctr_b = [0]
    POOLREF = [None]; gy_art = []; hatut = [False]
    mon = [None, None]; xc = [0]; rhino = [0, 0]   # monarch holder ('me'/'opp'), opp index; extra counters on carrier; rhinos (ready, new)
    PR = PROF.get(mode, PROF['disrupt'])
    DIS = mode in PROF
    wipe_T = rng.choice([5, 6, 7]) if DIS and rng.random() < PR['wipe'] else 99
    kill_T = rng.choice([3, 4, 5, 6]) if DIS and rng.random() < PR['cmd'] else 99
    edict = DIS and rng.random() < PR['edict']
    art_T = rng.choice([6, 7, 8]) if DIS and rng.random() < PR['artwipe'] else 99
    out_T = {3, 5} if mode == 'cmdout' else set()
    pillow = DIS and rng.random() < PR['pillow']
    target_used = False; answer_used = False
    st = dict(cmd_turn=99, mana_t4=0, colour=0)
    def draw(n=1):
        for _ in range(int(n)):
            if lib: hand.append(lib.pop(0))
    def dead(i): return opp[i] <= 0 or cdmg[i] >= 21 or poison[i] >= 10
    def alldead(): return all(dead(i) for i in range(3))
    def n_art(): return sum(1 for c in bf if art(c)) + sum(1 for l, _ in lands if l in ('Ancient Den', 'Tree of Tales', 'Darksteel Citadel', 'Thornglint Bridge') or (l in LANDX and LANDX[l].get('art'))) + arttok[0] + (1 if 'Brass Knuckles (copy)' in equips else 0)
    def mk_vib(n=1):
        if 'Doubling Season' in bf: n *= 2
        if 'Amulet of Vigor' in bf:
            vib[0] += n
            try: POOLREF[0]['V'] += n
            except Exception: pass
        else: vib[1] += n
        arttok[0] += n
        if "Caretaker's Talent" in bf and st.get('ct') != T: st['ct'] = T; draw()
    def mk_art(n=1, food_clue_treasure=True):
        if food_clue_treasure and 'Academy Manufactor' in bf: n *= 3
        arttok[0] += n
    def carrier():
        if cmd_on: return cmd
        bodies = [b for b in BODY_RANK if b in bf]
        return bodies[0] if bodies else None
    while T < maxT:
        T += 1
        if 'Felidar Sovereign' in bf and bf['Felidar Sovereign'] < T and life >= 40:
            if stats is not None: stats.append(st)
            return T
        if T > 1 or on_draw: draw()
        vib[0] += vib[1]; vib[1] = 0
        if 'The One Ring' in bf: ring_ct += 1; draw(min(ring_ct, 3))
        if 'Sylvan Library' in bf and life > 20: draw(); life -= 4
        if "Sensei's Divining Top" in bf and rng.random() < 0.3: draw()
        if 'Mystic Forge' in bf and rng.random() < 0.4: draw()
        if 'Chimil, the Inner Sun' in bf and bf['Chimil, the Inner Sun'] < T: draw()
        if 'Esper Sentinel' in bf and rng.random() < 0.3: draw()
        if 'Aetherflux Reservoir' in bf: life += 3
        # land drop
        lh = [c for c in hand if land(c)]
        if lh:
            needG = any(parse(c)[1] for c in hand if not land(c)); needW = any(parse(c)[2] for c in hand if not land(c))
            def sc(l):
                p = set(C[l].get('prod', []))
                return (('G' in p) and needG) + (('W' in p) and needW) + len(p & {'G', 'W'}) * 0.5 - (l == 'Lush Portico') * 0.4 + (l == "Urza's Saga" and T <= 2)
            l = max(lh, key=sc); hand.remove(l); lands.append((l, T))
            for lf in ('Tireless Tracker', 'Tireless Provisioner'):
                if lf in bf: mk_art(1 + (1 if l == 'Windswept Heath' else 0))
            if l == 'Windswept Heath': lands[-1] = ('Savannah', T)
        # mana
        G = W = A = Cc = 0
        for l, t in lands:
            p = set(C[l].get('prod', []))
            if l == 'Lush Portico' and t == T: continue
            if l in LANDX and LANDX[l].get('tapped') and t == T: continue
            if l == 'Ancient Tomb': Cc += 2
            elif l == 'Utopia': pass
            elif {'G', 'W'} <= p: A += 1
            elif 'G' in p: G += 1
            elif 'W' in p: W += 1
            else: Cc += 1
        for c, t in bf.items():
            if c in DORK and t < T: k = DORK[c]; G += k == 'G'; W += k == 'W'; A += k == 'A'
            if c in ROCK:
                k, v = ROCK[c]
                if c == 'Mox Opal' and n_art() < 3: continue
                if k == 'C': Cc += v
                else: A += v
            if c == 'Utopia Sprawl': A += 1
        pool = dict(G=G, W=W, A=A, C=Cc, V=vib[0]); POOLREF[0] = pool
        def tot(): return sum(pool.values())
        def tot_na(): return pool['G'] + pool['W'] + pool['A'] + pool['C']
        def red(c):
            r = 0
            if art(c) and 'Foundry Inspector' in bf: r += 1
            if (art(c) or 'Legendary' in C[c]['type']) and "Jhoira's Familiar" in bf: r += 1
            if art(c): r += sum(1 for x in bf if x in GENX and 'reducer' in GENX[x] and x != c)
            return r
        def can(c, extra=0):
            g, gg, ww, hy = parse(c); g = max(0, g - red(c))
            if c == cmd: g += tax
            if (tot() if (art(c) or 'Inspiring Statuary' in bf) else tot_na()) < g + gg + ww + hy + extra: return False
            needG = max(0, gg - pool['G']); needW = max(0, ww - pool['W'])
            return needG + needW <= pool['A']
        def pay(c=None, g=0, gg=0, ww=0):
            if c:
                g, gg, ww, hy = parse(c); g = max(0, g - red(c)); g += hy + (tax if c == cmd else 0)
            for k, n in (('G', gg), ('W', ww)):
                x = min(pool[k], n); pool[k] -= x; n -= x; pool['A'] -= n
            for k in (('V', 'C', 'G', 'W', 'A') if (c is None or art(c)) else (('C', 'V', 'G', 'W', 'A') if 'Inspiring Statuary' in bf else ('C', 'G', 'W', 'A'))):
                x = min(pool[k], g); pool[k] -= x; g -= x
        if T == 4: st['mana_t4'] = tot()
        def put(c):
            bf[c] = T
            if c == 'Okoye, Mighty and Adored': mon[0] = 'me'
            if c == 'Nakia, Wakandan Operative' and cmd_on: mon[0] = 'me'
            if c == 'The Spear of Bashenga' and mon[0] is None: mon[0] = 'me'
            if c in ROCK:
                k, v = ROCK[c]
                if not (c == 'Mox Opal' and n_art() < 3): pool['C' if k == 'C' else 'A'] += v
            if c == 'Chrome Mox':
                x = next((h for h in hand if not land(h) and not art(h) and h not in (cmd,)), None)
                if x: hand.remove(x)
                else: bf.pop(c); pool['A'] -= 1
            if c == 'Mox Diamond':
                x = next((h for h in hand if land(h)), None)
                if x: hand.remove(x)
                else: bf.pop(c); pool['A'] -= 1
            if c == 'Grim Monolith': pool['C'] += 3
            if c == "Shuri's Fabricator": mk_vib(2)
            if c == "T'Challa, the Black Panther": mk_vib(1)
            if c == 'Vibranium Mining Mech': mk_vib(1)
            if c == 'Dora Milaje Elite' and rng.random() < 0.7: mk_vib(1)
            if art(c) and C[c]['mv'] >= 4 and "T'Challa, the Black Panther" in bf and c != "T'Challa, the Black Panther":
                k = 4 if 'Doubling Season' in bf else 2; tch[0] += k
                if 'Terrasymbiosis' in bf and st.get('ts') != T: st['ts'] = T; draw(k)
            if c == 'Verdurous Gearhulk' and carrier():
                k = 8 if 'Doubling Season' in bf else 4; xc[0] += k
                if 'Terrasymbiosis' in bf and st.get('ts') != T: st['ts'] = T; draw(k)
            if c == 'Batterskull': bf['Germ token'] = T; equips['Batterskull'] = 'Germ token' if not carrier() or carrier() == 'Germ token' else None
            if c == 'Hatut Zeraze Strike Force': hatut[0] = True
            if cre(c) and 'Black Panther, Wakandan King' in bf: bpk[0] += 1
            if c == 'Gold Pan': mk_art(1)
            if c == "Machinist's Arsenal": bf['Hero token'] = T
            if art(c) and 'Digsite Engineer' in bf and c != 'Digsite Engineer' and tot() >= 4: pay(g=2); mk_art(1, False)
            if c == 'Iron Man Armor' and carrier(): pass
            if c in GENA and GENA[c]['aura']:
                equips[c] = carrier()
            if eq(c):
                equips[c] = None
                if 'Sram, Senior Edificer' in bf: draw()
                if 'Puresteel Paladin' in bf: draw()
                if c == "Swordsman's Steel": draw(sum(1 for e in equips))
                if c == 'Brass Knuckles': equips['Brass Knuckles (copy)'] = None
                if c in ('Vibranium Strike Gauntlets', 'Iron Man Armor') or (c in GENA and GENA[c]['auto']) or "Sigarda's Aid" in bf or 'Hammer of Nazahn' in bf:
                    if carrier(): equips[c] = carrier()
                if art(c) and C[c]['mv'] >= 4 and "T'Challa, the Black Panther" in bf: pass
        def tutor_pick(limit=99, where='hand'):
            car = carrier(); have = set(equips) | set(hand)
            evasive = car in ('Sigarda, Host of Herons', 'Storm, Queen of Wakanda', 'Armored Skyhunter') or any(e in equips for e in EVADE) or any(e in equips for e in ('Whispersilk Cloak', "Prowler's Helm"))
            free = 'Puresteel Paladin' in bf or 'Ardenn, Intrepid Archaeologist' in bf or "Sigarda's Aid" in bf or 'Forge Anew' in bf
            order = []
            if not evasive: order += ['Whispersilk Cloak', "Prowler's Helm", 'Shadowspear', 'Vibranium Strike Gauntlets']
            if not any(d in have for d in DS): order += ['Holy Avenger', 'Fireshrieker', 'Genji Glove', 'Brass Knuckles']
            if 'Stoneforge Mystic' in bf or 'Stoneforge Mystic' in hand: order.insert(0, 'Kaldra Compleat')
            if free: order.append('Colossus Hammer')
            if POLICY['tutor'] == 'ds_first': order = [o for o in ('Holy Avenger', 'Fireshrieker', 'Genji Glove') if o not in have] + order
            elif POLICY['tutor'] == 'kaldra_first': order = ['Kaldra Compleat'] + order
            elif POLICY['tutor'] == 'power_first': order = ['Hulkbuster Armor', 'Colossus Hammer' if free else 'Kaldra Compleat'] + order
            order = ["Machinist's Arsenal", 'Adaptive Omnitool'] + order + ["Commander's Plate", "Bilbo's Ring", 'Sword of Fire and Ice', 'Sword of War and Peace', 'Grafted Exoskeleton', 'Colossus Hammer', "Umezawa's Jitte", 'Lightning Greaves']
            for o in order:
                if o in lib and o not in have and C[o]['mv'] <= limit: return o
            return None
        progress = True; guard = 0
        while progress and guard < 40 and not alldead():
            guard += 1; progress = False
            ramp_now = [c for c in hand if (c in DORK or c in ROCK or c in RAMP or c == 'Utopia Sprawl') and can(c)]
            if not cmd_on and can(cmd) and (T >= 2) and (POLICY['cmd_first'] or not ramp_now or T >= 4):
                pay(cmd); cmd_on = True; cmd_T = T; mon[0] = 'me' if 'Nakia, Wakandan Operative' in bf else mon[0]; st['cmd_turn'] = min(st['cmd_turn'], T); bf[cmd] = T; progress = True; continue
            order = sorted([c for c in hand if not land(c) and c not in HOLD],
                           key=lambda c: ((0 if POLICY['cast'] == 'ramp_first' else 2) if (c in DORK or c in ROCK or c in RAMP or c == 'Utopia Sprawl') else
                                          (1 if POLICY['cast'] == 'ramp_first' else 0) if c in ('Stoneforge Mystic', 'Cloud, Midgar Mercenary', 'Puresteel Paladin', 'Sram, Senior Edificer', "Steelshaper's Gift", 'Federation Resupply') else
                                          (2 if POLICY['cast'] == 'ramp_first' else 1) if (c in DS or c in POWER or c in EVADE or c in GENA) else 3, C[c]['mv']))
            for c in order:
                if c in GENA and GENA[c]['aura'] and not carrier(): continue
                if can(c):
                    if c == 'Utopia Sprawl' and not any(l in ('Forest',) for l, _ in lands): continue
                    pay(c); hand.remove(c)
                    if c in RAMP:
                        lands.append(('Forest' if c == "Nature's Lore" else 'Savannah', T + (1 if c == 'Three Visits' else 0)))
                        for lf in ('Tireless Tracker', 'Tireless Provisioner'):
                            if lf in bf: mk_art(1)
                    elif c == 'Enlightened Tutor':
                        p = tutor_pick()
                        if p: lib.remove(p); lib.insert(0, p)
                    elif c in TUTOR_HAND:
                        p = tutor_pick()
                        if p: lib.remove(p); hand.append(p)
                    elif c in GENX and GENX[c].get('inst'):
                        draw(GENX[c].get('drawspell', 0))
                    else:
                        put(c)
                        if c in ('Stoneforge Mystic', 'Cloud, Midgar Mercenary'):
                            p = tutor_pick(1 if c == 'Stoneforge Mystic' and False else 99)
                            if p: lib.remove(p); hand.append(p)
                        if c == 'Captain America, Liberator':
                            p = tutor_pick(3)
                            if p: lib.remove(p); put(p)
                        if c == 'Brightglass Gearhulk':
                            for _ in range(2):
                                p = tutor_pick(1)
                                if p: lib.remove(p); hand.append(p)
                        if c == 'Kor Outfitter' and carrier():
                            un = [e for e in equips if equips[e] != carrier()]
                            if un: equips[max(un, key=lambda e: (e in DS, POWER.get(e, 0)))] = carrier()
                    progress = True; break
            if progress: continue
            # Stoneforge: {1}{W},T put Equipment from hand onto battlefield
            if 'Stoneforge Mystic' in bf and bf['Stoneforge Mystic'] < T:
                big = [e for e in hand if eq(e) and C[e]['mv'] >= 3]
                if big and tot() >= 2 and pool['W'] + pool['A'] >= 1:
                    pay(g=1, ww=1); e = max(big, key=lambda e: C[e]['mv']); hand.remove(e); put(e); bf['Stoneforge Mystic'] = T; progress = True; continue
            if 'Stonehewer Giant' in bf and bf['Stonehewer Giant'] < T and tot() >= 2 and pool['W'] + pool['A'] >= 1:
                p = tutor_pick()
                if p: pay(g=1, ww=1); lib.remove(p); put(p); equips[p] = carrier(); bf['Stonehewer Giant'] = T; progress = True; continue
        if 'Kuldotha Forgemaster' in bf and bf['Kuldotha Forgemaster'] < T and vib[0] + vib[1] + max(0, arttok[0] - vib[0] - vib[1]) >= 3:
            p = 'Kaldra Compleat' if ('Kaldra Compleat' in lib and POLICY['forgemaster'] == 'kaldra') else tutor_pick()
            if p and p in lib:
                take = 3
                for k in (1, 0):
                    x = min(vib[k], take); vib[k] -= x; take -= x
                arttok[0] -= 3; pool['V'] = min(pool['V'], vib[0])
                lib.remove(p); put(p); bf['Kuldotha Forgemaster'] = T
        # equip everything onto the carrier
        car = carrier()
        if car:
            free_first = 'Forge Anew' in bf; squire_used = [False]
            for e in sorted(equips, key=(lambda e: (e not in DS, -POWER.get(e, 0))) if POLICY['equip'] == 'ds_first' else (lambda e: (-POWER.get(e, 0) - (6 if e == 'Hulkbuster Armor' else 0), e not in DS))):
                if equips[e] == car: continue
                if e in GENA and GENA[e]['aura']: continue
                if e == 'Brass Knuckles (copy)': cost = 1
                else: cost = 0 if ('Puresteel Paladin' in bf and n_art() >= 3) or e == 'Lightning Greaves' else equip_cost(e, car, cmd)
                if free_first and cost > 0: cost = 0; free_first = False
                if 'Ardenn, Intrepid Archaeologist' in bf: cost = 0
                if 'Auriok Steelshaper' in bf: cost = max(0, cost - 1)
                if 'Brass Squire' in bf and bf['Brass Squire'] < T and not squire_used[0] and cost > 0: cost = 0; squire_used[0] = True
                if tot() >= cost: pay(g=cost); equips[e] = car
        if 'Retrofitter Foundry' in bf and tot() >= 2: pay(g=2); mk_art(1, False)
        if any(l == 'The Great Mound' for l, _ in lands) and tot() >= 4: pay(g=3); mk_vib(1)
        if 'Black Panther, Wakandan King' in bf and bpk[0] >= 2 and tot() >= 3 and carrier(): pay(g=3); bpk_on[0] += bpk[0]; life += bpk[0]; bpk[0] = 0; draw()
        if 'Walking Ballista' in hand and T >= 5 and tot() >= 4:
            X = tot() // 2; pay(g=2 * X); hand.remove('Walking Ballista'); bf['Walking Ballista'] = T; ctr_b[0] = X
        while 'Walking Ballista' in bf and tot() >= 4:
            pay(g=4); ctr_b[0] += 1
        if 'Teleportation Circle' in bf and "Shuri's Fabricator" in bf: mk_vib(2)
        if T == 4: st['art4'] = n_art()
        if T == 6: st['art6'] = n_art()
        if 'Nakia, Wakandan Operative' in bf and bf['Nakia, Wakandan Operative'] < T and carrier() and tot() >= 2: pay(g=2); xc[0] += 2
        rhino[0] += rhino[1]; rhino[1] = 0
        # Dawnsire station: tap other non-carrier, non-dork creatures (sorcery speed)
        car = carrier()
        if 'Dawnsire, Sunstar Dreadnought' in bf and charge[0] < 10:
            charge[0] += sum(pw(x) for x in bf if cre(x) and x != car and x not in DORK)
        dawn_ready = 'Dawnsire, Sunstar Dreadnought' in bf and charge[0] >= 10 and 'Black Panther, Most Dangerous' in bf
        # ---------------- combat ----------------
        car = carrier()
        can_attack = car and (bf.get(car, 99) < T or 'Lightning Greaves' in equips and equips['Lightning Greaves'] == car)
        if car == cmd and cmd_T == T and not (equips.get('Lightning Greaves') == car): can_attack = False
        if can_attack:
            on_car = [e for e, c in equips.items() if c == car]
            p = pw(car) + sum(POWER.get(e.replace(' (copy)', ''), 0) for e in on_car if e in POWER)
            if 'Blackblade Reforged' in on_car: p += len(lands)
            if 'Nettlecyst' in on_car: p += n_art()
            if "Machinist's Arsenal" in on_car: p += 2 * n_art()
            if 'Adaptive Omnitool' in on_car: p += n_art(); draw(1 if rng.random() < 0.5 else 0)
            if 'Iron Man Armor' in on_car: p += 2
            if 'Hulkbuster Armor' in on_car: p += max(0, 9 - P0(car))
            if 'Cosmic Cube' in bf: draw()
            if 'Ironsoul Enforcer' in bf and gy_art:
                e = gy_art.pop(0); put(e)
            gfx = [GENA[e] for e in on_car if e in GENA]
            for g in gfx:
                p += g['pow']
                if g['scale']:
                    v = {'artifact': n_art(), 'equipment': len(equips), 'land': len(lands), 'aura and equipment': len(on_car), 'creature': sum(1 for x in bf if cre(x)), 'color': 2}[g['scale']]
                    p += g['mult'] * v
            gxk = set()
            for x in [x for x in bf if x in GENX and x != car]:
                g = GENX[x]
                if 'anthem' in g: p += g['anthem']
                if 'counters' in g and not g.get('inst'): p += g['counters']
                if 'grant' in g: gxk |= set(g['grant'])
                if 'draw' in g: draw()
            for x in [x for x in hand if x in GENX and ('trick' in GENX[x] or ('counters' in GENX[x] and GENX[x].get('inst')))]:
                if can(x):
                    g = GENX[x]; pay(x); hand.remove(x)
                    p += g.get('trick', {}).get('n', 0) + (g.get('counters', 0) if g.get('inst') else 0); gxk |= set(g.get('trick', {}).get('kw', []))
                    break
            if 'Celestial Mantle' in bf and car == cmd: p += 3
            if car == 'Guidelight Synergist': p += n_art()
            if "Swordsman's Steel" in on_car: p += 2 * len(equips)
            if "Conqueror's Flail" in on_car: p += 0
            if "Umezawa's Jitte" in on_car and jitte_hit: p += 2
            if car == "T'Challa, the Black Panther": p += tch[0]; mk_vib(1)
            if car == cmd: p += bpk_on[0]
            if 'Janice Rand, Essential Aide' in bf and car == cmd: p += min(T - bf['Janice Rand, Essential Aide'], 4)
            if 'Storm, Queen of Wakanda' in bf and bf['Storm, Queen of Wakanda'] < T and car != 'Storm, Queen of Wakanda': p += 4
            myriad = 'Blade of Selves' in on_car
            shuri_trig = (1 + (2 if myriad else 0)) if car == 'Shuri, the Black Panther' else 0
            team_bonus = 2 * shuri_trig if n_art() >= 6 else 0
            if car == 'Shuri, the Black Panther' and n_art() >= 3: draw(shuri_trig)
            p += team_bonus
            if 'Okoye, Mighty and Adored' in bf: xc[0] += 1
            p += xc[0]
            ncre = sum(1 for x in bf if cre(x)) + rhino[0]
            if 'Bast, Panther Goddess' in bf: p += ncre
            live0 = [i for i in range(3) if not dead(i)]
            vs_mon = mon[0] == 'opp' and mon[1] in live0
            if vs_mon and "M'Baku, Jabari Chieftain" in bf: p += 1
            if "W'Kabi, Shield of the Nation" in bf and car == cmd and any(art(x) and C[x]['mv'] >= 4 for x in bf): rhino[1] += 1
            hits = 1
            if any(d in on_car for d in ('Fireshrieker', 'Holy Avenger', 'Genji Glove')) or (sum(1 for e in on_car if 'Brass Knuckles' in e) >= 1 and len(on_car) >= 2): hits = 2
            if "Duelist's Heritage" in bf or any(g['ds'] for g in gfx): hits = 2
            combats = 2 if 'Genji Glove' in on_car else 1
            fly = (any(g['fly'] for g in gfx) and not any(g['lose_fly'] for g in gfx)) or 'Iron Man Armor' in on_car or car in ('Sigarda, Host of Herons', 'Storm, Queen of Wakanda', 'Armored Skyhunter', 'Guidelight Synergist', 'Indomitable Archangel') or ('Storm, Queen of Wakanda' in bf and bf['Storm, Queen of Wakanda'] < T)
            fly = fly or 'Hulkbuster Armor' in on_car or ('Steel Seraph' in bf and bf['Steel Seraph'] < T)
            unblock = any(g['unb'] for g in gfx) or "Bilbo's Ring" in on_car or 'Whispersilk Cloak' in on_car or "Prowler's Helm" in on_car
            if not unblock and not fly and any(l == "Rogue's Passage" for l, _ in lands) and tot() >= 4:
                lv = [i for i in range(3) if not dead(i)]
                if POLICY['passage'] == 'always' or (lv and p * hits >= min(min(opp[i] for i in lv), 21 - max(cdmg[i] for i in lv))): pay(g=4); unblock = True
            for l, _ in lands:
                lx = LANDX.get(l, {})
                if 'unblock' in lx and not unblock and not fly and tot() >= lx['unblock']: pay(g=lx['unblock']); unblock = True
                if 'pump' in lx and tot() >= lx['pump'][0]:
                    pay(g=lx['pump'][0]); p += lx['pump'][1]
                    if lx.get('perm'): xc[0] += lx['pump'][1]   # Gavony-style +1/+1 counters stay on the carrier
            trample = any(g['tr'] for g in gfx) or any(e in on_car for e in ('Kaldra Compleat', 'Shadowspear', 'Vibranium Strike Gauntlets', 'Brightglass Gearhulk'))
            if vs_mon and ('Okoye, Mighty and Adored' in bf or "M'Baku, Jabari Chieftain" in bf): trample = True
            if 'double strike' in gxk: hits = 2
            if 'flying' in gxk: fly = True
            if "can't be blocked" in gxk: unblock = True
            if 'trample' in gxk: trample = True
            if vs_mon and 'Okoye, Mighty and Adored' in bf: hits = 2
            infect = 'Grafted Exoskeleton' in on_car
            if pillow and hatut[0]: pillow = False
            if pillow and T >= 4:
                if tot() >= 2: pay(g=2)
                else: combats = 0
            # Akroma's Will team alpha: flying + double strike for everyone (both modes with a commander out)
            others = [c for c in bf if cre(c) and c != car and bf[c] < T and c not in ('Sigarda, Host of Herons',) or (c == 'Sigarda, Host of Herons' and c != car and cre(c) and bf[c] < T)]
            will = False
            if "Akroma's Will" in hand and tot_na() >= 4 and (pool['W'] + pool['A']) >= 1:
                live = [i for i in range(3) if not dead(i)]
                team = sum((pw(c) + team_bonus) * 2 for c in others)
                if len(live) >= 2 and team >= min(opp[i] for i in live) * 0.8 or (hits == 1 and len(live) >= 1):
                    _v=pool['V']; pool['V']=0; pay(g=3, ww=1); pool['V']=_v; hand.remove("Akroma's Will"); will = True; hits = 2; fly = True
            if will:
                live = [i for i in range(3) if not dead(i)]
                tgt = min(live, key=lambda i: 21 - cdmg[i]) if live else None
                for c in others:
                    live = [i for i in range(3) if not dead(i) and i != tgt] or [i for i in range(3) if not dead(i)]
                    if not live: break
                    j = min(live, key=lambda i: opp[i]); opp[j] -= (pw(c) + team_bonus) * 2
            # Blade of Selves: myriad copies of the carrier attack each other opponent (no equipment, no commander damage)
            if myriad:
                live = [i for i in range(3) if not dead(i)]
                tgt = min(live, key=lambda i: 21 - cdmg[i]) if live else None
                for j in live:
                    if j == tgt: continue
                    if not (fly and rng.random() < 0.15) and not (not fly and rng.random() < 0.5):
                        opp[j] -= (pw(car) + team_bonus) * (2 if will else 1)
            # kill-turn answer (disruption): fires once when this attack would finish the table
            if dawn_ready:
                live = [i for i in range(3) if not dead(i)]
                answered = False
                if DIS and not answer_used and len(live) == 1 and rng.random() < PR['answer']:
                    answer_used = True
                    if any(s_ in hand for s_ in ('Silence', "Orim's Chant")): hand.remove(next(s_ for s_ in ('Silence', "Orim's Chant") if s_ in hand))
                    else: answered = True
                if live and not answered:
                    j = min(live, key=lambda i: opp[i]); opp[j] -= 100
                    if 'Dora Milaje Elite' in bf: bf.pop('Dora Milaje Elite')
                    elif 'Heroic Intervention' in hand: hand.remove('Heroic Intervention')
                    else: bf.pop('Black Panther, Most Dangerous')
            for cb in range(combats):
                live = [i for i in range(3) if not dead(i)]
                if not live: break
                i = min(live, key=lambda i: ((21 - cdmg[i]) if POLICY['target'] == 'cmd_damage' else opp[i]) if not infect else (10 - poison[i]))
                if vs_mon and mon[1] in live: i = mon[1]
                if DIS and not answer_used and rng.random() < PR['answer'] and len(live) == 1:
                    answer_used = True
                    if not ('Grand Abolisher' in bf or any(s in hand for s in ('Silence', "Orim's Chant"))):
                        continue
                blocked = 0
                if unblock: blocked = 0
                elif fly: blocked = rng.random() < 0.15
                else: blocked = rng.random() < 0.5
                dmg_each = p if not blocked else (max(0, p - 2) if trample else 0)
                d = dmg_each * hits
                if d <= 0: continue
                if infect: poison[i] += d
                else: opp[i] -= d
                if mon[0] == 'opp' and mon[1] == i: mon[0] = 'me'
                if car == cmd: cdmg[i] += d
                if car == 'Shuri, the Black Panther' or 'Shadowspear' in on_car or 'Batterskull' in on_car or any(g['ll'] for g in gfx): life += d
                if any(g['draw'] for g in gfx): draw(hits)
                if 'Celestial Mantle' in bf and car == cmd: life *= 2
                if 'Aetherflux Reservoir' in bf:
                    while life >= 60 and [j for j in range(3) if not dead(j)]:
                        j = min((j for j in range(3) if not dead(j)), key=lambda j: opp[j]); life -= 50; opp[j] -= 50
                if 'Sword of Fire and Ice' in on_car: draw(hits); opp[i] -= 2 * hits
                if 'Sword of War and Peace' in on_car: opp[i] -= 4 * hits
                if 'Vibranium Strike Gauntlets' in on_car: draw(hits)
                if "Umezawa's Jitte" in on_car: jitte_hit = True
                if "Bilbo's Ring" in on_car: draw(); life -= 1
                if alldead(): break
        if rhino[0]:
            for _ in range(rhino[0]):
                live = [i for i in range(3) if not dead(i)]
                if not live: break
                j = min(live, key=lambda i: opp[i]); opp[j] -= 4 if rng.random() < 0.5 else 3
        if mon[0] == 'me': draw()
        if mon[0] is None and "M'Baku, Jabari Chieftain" in bf:
            live = [i for i in range(3) if not dead(i)]
            if live: mon[0] = 'opp'; mon[1] = rng.choice(live)
        if 'Kaldra Compleat' in equips and equips['Kaldra Compleat'] != car:
            live = [i for i in range(3) if not dead(i)]
            if live: opp[min(live, key=lambda i: opp[i])] -= 5
        if 'Walking Ballista' in bf and ctr_b[0]:
            live = [i for i in range(3) if not dead(i)]
            if live and ctr_b[0] >= sum(max(0, opp[i]) for i in live):
                for i in live: ctr_b[0] -= max(0, opp[i]); opp[i] = 0
            else:
                for i in sorted(live, key=lambda i: opp[i]):
                    if 0 < opp[i] <= ctr_b[0]: ctr_b[0] -= opp[i]; opp[i] = 0
        if alldead():
            if stats is not None: stats.append(st)
            return T
        # ---------------- opponents' turns (disruption) ----------------
        if mon[0] == 'me' and rng.random() < 0.3:
            live = [i for i in range(3) if not dead(i)]
            if live: mon[0] = 'opp'; mon[1] = rng.choice(live)
        def gfl(): return next((x for x in hand if x in GENX and 'flicker' in GENX[x] and GENX[x].get('inst') and len(lands) >= C[x]['mv']), None)
        def flick_cmd():
            hand.remove(gfl())
            for e in list(equips):
                if equips[e] == cmd: equips[e] = None
                if e in GENX and e in GENA and GENA[e]['aura'] and equips[e] is None: equips.pop(e)
            if cmd == "T'Challa, the Black Panther": mk_vib(1)
        def protected(c): return c == 'Sigarda, Host of Herons' or equips.get('Swiftfoot Boots') == c or (equips.get('Darksteel Plate') == c and rng.random() < 0.5) or (equips.get('Lightning Greaves') == c) or any(m in bf and bf[m] < T + 1 for m in ('Mother of Runes', 'Giver of Runes'))
        if cmd_on and (T == kill_T or T in out_T):
            others = [c for c in bf if cre(c) and c != cmd and c not in DORK]
            gsv = next((x for x in hand if x in GENX and 'protect' in GENX[x] and len(lands) >= C[x]['mv']), None)
            if edict and 'Sigarda, Host of Herons' in bf: pass
            elif gsv and not edict: hand.remove(gsv)   # phasing / hexproof: equipment stays attached (CR 702.26)
            elif not edict and gfl(): flick_cmd()
            elif edict and others: bf.pop(others[0])
            elif mode == 'cmdout' or (edict and 'Sigarda, Host of Herons' not in bf) or (not edict and not protected(cmd)):
                cmd_on = False; tax += 2; bf.pop(cmd, None); tch[0] = 0 if cmd == "T'Challa, the Black Panther" else tch[0]; bpk_on[0] = 0
                for e in list(equips):
                    if equips[e] == cmd: equips[e] = None
                    if e in GENA and GENA[e]['aura'] and equips[e] is None: equips.pop(e)
        if DIS and 'Felidar Sovereign' in bf and bf['Felidar Sovereign'] == T and rng.random() < 0.7: bf.pop('Felidar Sovereign')
        if DIS and not target_used and T >= 4:
            top = [c for c in ('Dawnsire, Sunstar Dreadnought',) if c in bf and charge[0] >= 10] + [c for c in ('Felidar Sovereign', 'Aetherflux Reservoir') if c in bf] + [e for e in equips if (e in DS or e in ("Bilbo's Ring", 'Colossus Hammer')) and equips[e]]
            if top and rng.random() < PR['target'] and not ('Indomitable Archangel' in bf and n_art() >= 3) and not ('Bronze Guardian' in bf and rng.random() < 0.5):
                target_used = True
                if 'Clever Concealment' in hand and tot() >= 0: hand.remove('Clever Concealment')
                else:
                    e = top[0]; equips.pop(e, None); bf.pop(e, None)
                    if C.get(e, {}).get('type', '').find('Artifact') >= 0: gy_art.append(e)
        if T == art_T and 'Darksteel Forge' in bf: art_T = 99
        if T == art_T:
            asv = next((x for x in ('Heroic Intervention', 'Clever Concealment', "Teferi's Protection") if x in hand), None)
            if asv: hand.remove(asv)
            else:
                gone = [c for c in bf if art(c) and not cre(c)]
                for c in gone: bf.pop(c)
                for e in list(equips): equips.pop(e)
                gy_art.extend(sorted([c for c in gone if c in POWER or c in GENA or c in DS], key=lambda c: -POWER.get(c, 3)))
        if T == wipe_T:
            saver = next((s for s in ("Flawless Maneuver", 'Heroic Intervention', 'Clever Concealment', "Teferi's Protection") if s in hand and (s == 'Flawless Maneuver' and cmd_on or tot() >= 0)), None)
            saver = saver or next((x for x in hand if x in GENX and GENX[x].get('mass') and len(lands) >= C[x]['mv']), None)
            if saver: hand.remove(saver)
            elif cmd_on and gfl():
                flick_cmd()
                for c in [c for c in bf if cre(c) and c != cmd and c != 'Bast, Panther Goddess']: bf.pop(c)
                rhino[0] = rhino[1] = 0
            elif cmd_on and equips.get('Darksteel Plate') == cmd:
                for c in [c for c in bf if cre(c) and c != cmd and c != 'Bast, Panther Goddess']: bf.pop(c)
                rhino[0] = rhino[1] = 0
            else:
                rhino[0] = rhino[1] = 0; xc[0] = 0
                for c in [c for c in bf if cre(c) and c != 'Bast, Panther Goddess']: bf.pop(c)
                if cmd_on: cmd_on = False; tax += 2; bpk_on[0] = 0
                tch[0] = 0
                for e in list(equips):
                    equips[e] = None
                    if e in GENA and GENA[e]['aura']: equips.pop(e)
    if stats is not None: stats.append(st)
    return 99

PROF = {'disrupt': dict(wipe=0.6, cmd=0.5, edict=0.0, answer=0.3, pillow=0.25, target=0.5, artwipe=0.0),
        # Seb's assumed pod (9 Nov 2026): Krenko, Mob Boss / Sephiroth, Fabled SOLDIER / Y'shtola, Night's Blessed (EDHREC average lists, B3)
        'pod':     dict(wipe=0.68, cmd=0.75, edict=0.25, answer=0.4, pillow=0.3, target=0.5, artwipe=0.25)}
def run(deck, cmd, N=5000, seed=11, mode='gold', remove=()):
    rng = random.Random(seed); K = collections.Counter(); S = []
    for _ in range(N): K[game(rng, deck, cmd, mode=mode, stats=S, remove=remove)] += 1
    return {t: v / N for t, v in K.items()}, S
