"""L1 card-effect parser (skill §8). Reads data/universe.json (one record per oracle_id) and writes library/cardlib.json:
   oracle_id -> {name, ci, type, mv, prims: {primitive: params}, conf: 'auto'|'hand-verified'|'unmodelled', parser}
Hand-verified records in library/hand.json are never overwritten. Reminder text is stripped before parsing; static effects reject
tribe-only, conditional and until-end-of-turn matches. Each primitive maps to one engine handler (engine/HANDLERS.md)."""
import json, re, collections, os, sys
PARSER = '1.6'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = json.load(open(os.path.join(ROOT, 'data/universe.json')))
HAND = json.load(open(os.path.join(ROOT, 'library/hand.json'))) if os.path.exists(os.path.join(ROOT, 'library/hand.json')) else {}
KW = ('flying', 'double strike', 'trample', "can't be blocked", 'haste', 'indestructible', 'hexproof', 'first strike', 'menace', 'deathtouch', 'lifelink', 'vigilance')
NUM = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'x': 'X', 'that many': 'var'}
def n_(s): return int(s) if s.isdigit() else NUM.get(s, 1)   # 'X' / 'var' are symbolic: the handler resolves them at run time
def sent(t, a, b):
    s = t.rfind('.', 0, a) + 1; e = t.find('.', b); return t[s:(e if e >= 0 else len(t))]
def mana_n(cost): return sum(int(x) for x in re.findall(r'\{(\d+)\}', cost)) + len(re.findall(r'\{[WUBRGCS](?:/[WUBRGP])?\}', cost)) + 3 * cost.count('{X}')
ANCHOR = r'(?:^|\n|\. |, |and )'
def parse(c):
    ty = c['type']; T = re.sub(r'\([^)]*\)', '', c['text'] or ''); t = T.lower(); P = {}
    cre, art, ench, landT = 'Creature' in ty, 'Artifact' in ty, 'Enchantment' in ty, ('Land' in ty and '//' not in ty.split('—')[0] or ty.startswith('Land'))
    spell = 'Instant' in ty or 'Sorcery' in ty; inst = 'Instant' in ty
    ts = '\n'.join(l for l in t.split('\n') if not re.match(r'^\s*[+\-\u2212]?\d+:', l))   # static text: loyalty lines removed
    # ---- mana
    if landT:
        P['land'] = dict(prod=c['prod'], tapped=bool(re.search(r'enters( the battlefield)? tapped', t) and 'unless' not in t and 'you may pay' not in t))
    if cre and 'spend this mana only' not in t and re.search(r'(^|\n)\{t\}: add (\{[wubrgc]\}|one mana|two mana|\{[wubrg]\} or \{[wubrg]\}|mana of any|.*any color)', t): P['dork'] = dict(prod=c['prod'] or ['any'])
    if art and not cre and not landT and c['mv'] <= 4 and "doesn't untap" not in t:
        m = re.search(r'(^|\n)\{t\}: add ((\{[wubrgcs]\})+|one mana of any color)', t)
        if m and 'sacrifice' not in t.split('{t}: add')[0][-30:]: P['rock'] = dict(n=max(1, m.group(2).count('{')), prod=c['prod'])
    if spell and re.search(r'add (\{[wubrgc]\}){2,}|add (two|three) mana', t) and 'land' not in t: P['ritual'] = 1
    if re.search(r'search your library for (up to (one|two|three) )?(basic )?land cards?.{0,80}onto the battlefield|put (a|up to one|up to two) land cards? from your hand onto the battlefield|search your library for (a|up to two) (basic )?(forest|plains|island|swamp|mountain|land)[^.]{0,40}onto the battlefield', t):
        P['ramp'] = 2 if re.search(r'up to two|two basic', t) else 1
    m = re.search(r'(^|\n|\. )([a-z, -]*?)spells you cast cost \{(\d)\} less', t) or re.search(r'(^|\n|\. )()equip abilities you activate cost \{(\d)\} less', t)
    if m and 'for each' not in t[m.end():m.end() + 12]: P['reducer'] = dict(scope=(m.group(2).strip() or ('equip' if 'equip abilities' in m.group(0) else 'all')), n=int(m.group(3)))
    # ---- cards
    m = re.search(r'draw (a|two|three|four|x) cards?', t)
    if spell and m and 'each player' not in t and 'target player' not in t: P['draw_spell'] = n_(m.group(1))
    if not spell and re.search(r'(at the beginning of your (upkeep|end step|draw step)|whenever [^.]{0,60}(attacks|deals combat damage to a player|enters|dies|you cast)[^.]{0,30},)[^.]{0,40}draw (a|two) cards?', t): P['draw_engine'] = 1
    if not spell and re.search(r'(^|\n)[^\n:]*\{t\}[^\n:]*: draw a card', t) and not re.search(r'(^|\n)[^\n:]*sacrifice this[^\n:]*: draw', t): P['draw_engine'] = 1
    m = re.search(r'search your library for (a|an|up to one|up to two|any)[^.]{0,50}?(artifact|equipment|aura|creature|enchantment|instant|sorcery|planeswalker|legendary|land)? ?card', t)
    if m and not re.search(r'basic|land card|(forest|plains|island|swamp|mountain) card', t[m.start():m.end() + 25]):
        dest = 'graveyard' if 'graveyard' in t[m.end():m.end() + 80] and 'into your hand' not in t[m.end():m.end() + 80] else 'battlefield' if 'onto the battlefield' in sent(t, m.start(), m.end()) else ('top' if 'on top' in t[m.end():m.end() + 120] else 'hand')
        P['tutor'] = dict(kind='named' if 'card named' in t[m.start():m.end() + 15] else (m.group(2) or 'any'), dest=dest)
    m = re.search(r'return (target|up to (one|two) target|another target|a|all) [^.]{0,40}cards? from your graveyard to (your hand|the battlefield)', t) or re.search(r'return (target|up to one target) [^.]{0,30}card from your graveyard', t)
    if m: P['recursion'] = dict(kind='reanimate' if 'battlefield' in t[m.start():m.end() + 5] else 'regrowth')
    elif re.search(r'you may cast (target|a|an|up to one target) [^.]{0,40}card from your graveyard', t): P['recursion'] = dict(kind='cast_from_graveyard')
    # ---- board
    if cre:
        try: pw = int(c['p'])
        except Exception: pw = 0
        P['body'] = dict(p=pw if c.get('p') is not None else None, kw=[k for k in KW if k in [x.lower() for x in c.get('kw', [])]] + (["can't be blocked"] if re.search(r"this creature can.t be blocked\.", t) else []))
    m = re.search(r'create (a|an|one|two|three|four|five|x|that many|\d+) [^.]{0,60}?(\d+)/(\d+) [^.]{0,40}creature tokens?', t)
    if m: P['token'] = dict(n=n_(m.group(1)), p=int(m.group(2)), repeat=not spell and bool(re.search(r'(whenever|at the beginning|\{t\}|: create)', t)))
    if re.search(r"create a token that's a copy", t) and not re.search(r'target opponent creates', t): P['copy'] = dict(kind='token')
    elif 'becomes a copy' in t: P['copy'] = dict(kind='becomes')
    m = re.search(r'(twice that many|that many plus one)[^.]{0,30}(tokens|\+1/\+1 counters|counters)|(tokens?|counters?) [^.]{0,40}(twice that many|that many plus one)|double the (number of|amount of) ([a-z+/1 ]+?counters|damage)', t)
    if m and not spell:
        what = 'tokens' if 'token' in m.group(0) else ('+1/+1 counters' if '+1/+1' in m.group(0) else ('damage' if 'damage' in m.group(0) else 'counters'))
        P['doubler'] = dict(what=what, factor='+1' if 'plus one' in m.group(0) else 'x2', static=True)
    elif m: P['doubler'] = dict(what='one_shot', factor='x2', static=False)
    m = re.search(ANCHOR + r'(creatures you control|other creatures you control|commander creatures you control|legendary creatures you control|attacking creatures you control) gets? \+(\d+)/\+(\d+)', ts)
    if m and int(m.group(2)) > 0 and not re.search(r'until end of turn|until your next turn|as long as|if you|for each|graveyard', sent(ts, m.start(), m.end())) and not spell and 'Equipment' not in ty and 'Aura' not in ty: P['anthem'] = int(m.group(2))
    g = re.search(ANCHOR + r'(creatures you control|other creatures you control|commander creatures you control|legendary creatures you control|attacking creatures you control) (have|gain) ([a-z ,]+?)(\.| until| as long)', ts)
    if g and not spell and g.group(4).strip() != 'until' and not re.search(r'until end of turn|until your next turn|as long as|graveyard|kicked|max speed|if ', sent(ts, g.start(), g.end())) and not re.search(r'(land|token|face-down) creatures you control', ts[max(0, g.start() - 6):g.end()]):
        kws = [k for k in KW[:9] if k in g.group(3)]
        if kws: P['grant'] = kws
    if re.search(r'put (a|two|three|x|\d) \+1/\+1 counters? on (target|each|another target|up to one target) creature', t) or re.search(r'enters with (a|two|three|x|\d+|an additional) \+1/\+1 counter', t): P['counters'] = 1
    # equipment / aura attach (v1 logic)
    if 'Equipment' in ty or ('Aura' in ty and 'enchant creature' in t):
        who = 'equipped creature' if 'Equipment' in ty else 'enchanted creature'
        a = dict(pow=0, scale=None, mult=0, kw=[], draw=0, auto='Aura' in ty or bool(re.search(r'when this (equipment|aura) enters, attach it', t)), equip=None)
        m = re.search(who + r' gets \+(\d+)/[+-]\d+(?! for each)', t); a['pow'] = int(m.group(1)) if m else 0
        m = re.search(who + r' gets \+(\d+)/\+\d+ for each (artifact|equipment|land|aura and equipment|creature|color)', t)
        if m: a['mult'] = int(m.group(1)); a['scale'] = m.group(2)
        a['kw'] = [k for k in KW if re.search(who + r'[^.]*(has|have|gains?)[^.]*' + re.escape(k), t)]
        if re.search(r'deals combat damage to a player,[^.]*draw a card', t): a['draw'] = 1
        m = re.findall(r'equip \{(\d+)\}', t); a['equip'] = int(m[-1]) if m else None
        if a['pow'] or a['mult'] or a['kw'] or a['draw']: P['attach'] = a
    # ---- combat
    if spell:
        m = re.search(r'target creature( you control)? gets \+(\d+|x)/\+(\d+|x)', t); kws = [k for k in KW if re.search(r'target creature[^.]*gains? [^.]*' + re.escape(k), t)]
        if m or kws: P['trick'] = dict(n=n_(m.group(2)) if m else 0, kw=kws)
    if 'additional combat phase' in t: P['extra_combat'] = 1
    # ---- interaction
    m = re.search(r'(destroy|exile) (target|each|all|up to one target|up to two target|any number of target) (attacking |tapped |nonland |noncreature |non[a-z]+ |blocking |another )?(creature|artifact|enchantment|nonland permanent|permanent|artifact or enchantment|creature or planeswalker|planeswalker)s?', t)
    if m and 'you control' not in t[m.start():m.end() + 25] and not re.search(r'card (from|in) (a|your|an opponent.s) graveyard', t[m.start():m.end() + 30]) and not re.search(r'exile [^.]{0,40}you (control|own)[^.]*return', t):
        sc = sent(t, m.start(), m.end()); hits = [x for x in ('creature', 'artifact', 'enchantment', 'planeswalker', 'land', 'nonland permanent', 'permanent') if x in sc] or [m.group(4)]
        P['removal'] = dict(scope='wipe' if m.group(2) in ('each', 'all') else 'target', hits=hits, speed='instant' if inst or 'flash' in t else 'sorcery', overload='overload' in t)
    if re.search(r'(each|target) (player|opponent) sacrifices (a|an|two)', t): P.setdefault('removal', dict(scope='edict', hits='creature', speed='instant' if inst else 'sorcery'))
    m = re.search(r'deals (\d+|x) damage to (any target|target creature|each creature|target creature or planeswalker)', t)
    if m and 'removal' not in P: P['removal'] = dict(scope='wipe' if 'each creature' in m.group(2) else 'target', hits='creature', speed='instant' if inst else 'sorcery', dmg=n_(m.group(1)))
    if re.search(r'counter target (spell|noncreature spell|creature spell|instant|activated)', t): P['counterspell'] = 1
    if re.search(r"(players|each player|your opponents|opponents) can't (cast|untap|search|draw more|gain life|activate)|spells your opponents cast cost|each player can't", t) and not spell: P['stax'] = 1
    # ---- protection
    m = re.search(r'(any number of other target creatures|target (creature|permanent|nonland permanent|artifact or creature)s? you control|any number of target nonland permanents you control|(nonland )?permanents you control|creatures you control|you and (other )?permanents you control)[^.]{0,30}phases? out', t)
    if m and "can't phase" not in t: P['phase'] = dict(mass=not m.group(1).startswith('target'))
    if re.search(r'exile (up to (one|two) |another |any number of )?target (creature|creatures|nonland permanent|nonland permanents|artifact or creature|permanent)s?[^.]{0,30}you (control|own)[^.]*(, then return|\. return)', t): P['flicker'] = dict(inst=inst)
    if inst and re.search(r'(target creature you control|creatures you control|permanents you control|target permanent you control)[^.]{0,40}(gains? |have )?(hexproof|indestructible|protection from|shroud)', t): P['protect'] = dict(mass=bool(re.search(r'(creatures|permanents) you control', t)))
    if re.search(r'(^|\n)regenerate', t) or 'regenerate target' in t: P['regenerate'] = 1
    # ---- life, triggers
    m = re.search(r'(each opponent|target opponent|target player|each other player) loses (\d+|x|that much|one) life', t)
    if m: P['drain'] = dict(each='each' in m.group(1), n=n_(m.group(2)) if m.group(2) not in ('that much',) else 2)
    m = re.search(r'deals (\d+|x) damage to (each opponent|target player|any target|each player|target opponent)', t)
    if m and 'drain' not in P: P['burn'] = dict(each=m.group(2) in ('each opponent', 'each player'), n=n_(m.group(1)))
    if re.search(r'you gain (\d+|x|that much) life', t): P['lifegain'] = 1
    if re.search(r'whenever you gain life|for each 1 life you gained|life you gained this turn|if you have \d+ or more life', t): P['life_payoff'] = 1
    if re.search(r'(^|\n)[^\n:]*sacrifice (a|another|an?) (creature|artifact|permanent|token)[^\n:]*:', t): P['sac_outlet'] = 1
    if re.search(r'whenever (a|another|one or more) (nontoken )?(creature|creatures)( you control)? (dies|die|is put into a graveyard)', t): P['death_trigger'] = 1
    if re.search(r'whenever you cast (a|an|your first)? ?(instant|sorcery|noncreature|artifact|enchantment|creature|historic|multicolored|legendary)', t): P['cast_trigger'] = 1
    if re.search(r'whenever (a|another|one or more) (nontoken )?(creature|artifact|equipment|land|enchantment)s? (you control )?enters?', t): P['etb_trigger'] = 1
    if re.search(r'whenever (a creature you control|one or more creatures you control|you) attacks?', t): P['attack_trigger'] = 1
    # ---- flags
    if re.search(r'becomes? the monarch|take the initiative|takes the initiative|you.re the monarch', t): P['flag_monarch'] = 1
    if re.search(r'you win the game|(that player|target player|each opponent|target opponent) loses the game', ts) and not re.search(r'(when|whenever) (enchanted|a) player loses the game', t): P['alt_win'] = 1
    if 'channel' in t: P['mode_channel'] = 1
    # ---- 1.3 additions (coverage push)
    SUPPORTED_KW = ('flying', 'reach', 'vigilance', 'defender', 'haste', 'first strike', 'double strike', 'trample', 'menace', 'deathtouch', 'lifelink', 'hexproof', 'indestructible', 'flash', 'shroud', 'prowess', 'devoid', 'changeling', "this creature can't block", "this creature attacks each combat if able", 'cycling')
    if cre:
        rest = re.sub(r'ward \{\d+\}|ward—[^\n]*|protection from [a-z ]+|cycling \{[^}]+\}(\{[^}]+\})*|[.]', '', t)
        for k in SUPPORTED_KW: rest = rest.replace(k, '')
        if not re.sub(r'[\s,]+', '', rest): P['keywords_only'] = 1
    if re.search(r'gets \+(\d+|x)/\+(\d+|x) for each|power (and toughness )?(is|are each) equal to the number of', t) and not spell: P['scaling_body'] = 1
    m = re.search(r'target creature( an opponent controls)? gets -(\d+|x)/-(\d+|x)', t)
    if m and 'removal' not in P: P['removal'] = dict(scope='target', hits='creature', speed='instant' if inst else 'sorcery', shrink=n_(m.group(2)))
    if re.search(r'(each creature|all creatures|creatures your opponents control) gets? -(\d+|x)/-(\d+|x)', t) and 'removal' not in P: P['removal'] = dict(scope='wipe', hits='creature', speed='instant' if inst else 'sorcery')
    m = re.search(r'return (target|up to one target|another target) (nonland permanent|creature|permanent|artifact|enchantment)[^.]{0,40}to (its|their) owner.s hand', t)
    if m and not re.search(r'you (control|own)', t[m.start():m.end()]) and 'removal' not in P: P['removal'] = dict(scope='bounce', hits='permanent', speed='instant' if inst else 'sorcery')
    if re.search(r'gain control of target', t) and 'removal' not in P: P['removal'] = dict(scope='steal', hits='permanent', speed='instant' if inst else 'sorcery')
    if re.search(r'\bfights? (target|another target|up to one target)', t) and 'removal' not in P: P['removal'] = dict(scope='fight', hits='creature', speed='instant' if inst else 'sorcery')
    m = re.search(r'(?<!un)tap (target|up to (one|two) target|all|each)[^.]{0,25}(creature|permanent|artifact|land)s?', t)
    if m and 'you control' not in t[m.start():m.end() + 15] and not re.search(r'tap or untap', t[max(0, m.start() - 8):m.end()]): P['tapper'] = 1
    if re.search(r'untap (target|all|each|up to (one|two) target|another target) [^.]{0,25}(creature|permanent|land|artifact)s?( you control)?', t): P['untap'] = 1
    if re.search(r'exile the top [^.]* (cards?|card) of your library[^.]*\. (until [^.]*, )?you may (play|cast)', t): P['impulse'] = 1
    if re.search(r'\b(scry|surveil) \d|look at the top (\w+) cards? of your library', t): P['selection'] = 1
    if re.search(r'\bmills?\b', t): P['mill'] = 1
    if re.search(r'prevent all (combat )?damage|prevent the next', t): P['prevent'] = 1
    if re.search(r"\bgoad|can.t block (this turn|target)|target creature can.t block", t): P['goad'] = 1
    m = re.search(r'create (a|an|one|two|three|x|\d+) (tapped )?(treasure|food|clue|blood|map|powerstone|gold) tokens?', t)
    if m: P['artifact_token'] = dict(kind=m.group(3), n=n_(m.group(1)))
    if re.search(r'(target|each) (player|opponent) discards|each other player discards', t): P['discard'] = 1
    if re.search(r'\bcrew \d', t): P['vehicle'] = 1
    if re.search(r'\b(flashback|escape|unearth|disturb|retrace|jump-start|embalm|eternalize|encore)\b|you may cast this card from your graveyard', t): P['self_recursion'] = 1
    if re.search(r'copy (target|that|it|the next) [^.]{0,20}(instant|sorcery|spell)', t): P['copy_spell'] = 1
    if 'proliferate' in t: P['proliferate'] = 1
    if '{e}' in t: P['energy'] = 1
    if re.search(r'(^|\n)\{[^}]+\}[^:\n]*: [^\n]*gets \+\d/\+\d until end of turn', t) and cre: P['firebreathing'] = 1
    if re.search(r'you lose \d+ life|pay \d+ life', t): P['life_cost'] = 1
    if 'Aura' in ty and re.search(r"enchanted (creature|permanent) (can.t attack|can.t attack or block|loses all abilities|doesn.t untap|can.t block, and its activated)", t) and 'removal' not in P: P['removal'] = dict(scope='lockdown', hits='creature', speed='sorcery')
    if cre and re.search(r'whenever this creature (attacks|blocks|becomes blocked|deals combat damage)[^.]{0,30}(it gets \+|gets \+|put a \+1/\+1 counter on (it|this creature))', t): P['attack_pump'] = 1
    m = re.search(r'creatures you control get \+(\d+|x)/\+(\d+|x)[^.]{0,30}until end of turn', t)
    if m and m.group(1) != '0': P['team_pump'] = dict(n=n_(m.group(1)), trample='trample' in t[m.start():m.end() + 40])
    if cre and re.search(r"this creature can.t be blocked|can.t be blocked except by|this creature has (flying|menace|trample)", t): P['evasive_body'] = 1
    if re.search(r'target (opponent|player) reveals (their|his or her) hand[^.]*\. you choose', t): P['discard'] = 1
    if re.search(r'draw (a|two) cards?, then discard', t): P['selection'] = 1
    if re.search(r'whenever [^.]{0,40}deals combat damage to (a player|an opponent|one or more players)', t): P['combat_damage_trigger'] = 1
    if re.search(r'at the beginning of (combat on your turn|each combat)', t): P['begin_combat_trigger'] = 1
    if cre and re.search(r'this creature gets \+\d/\+\d as long as|as long as [^.]{0,60}, this creature (gets|has)', t): P['conditional_body'] = 1
    if re.search(r'when this creature dies', t): P['death_trigger'] = 1
    if re.search(r'whenever (this creature|enchanted creature|equipped creature) (becomes blocked|blocks)', t): P['block_trigger'] = 1
    if re.search(r'(^|\n)[^\n:]*\{t\}[^\n:]*: add [^\n]*(any color|\{[wubrgc]\})', t) and cre and 'dork' not in P: P['dork'] = dict(prod=c['prod'] or ['any'], restricted=True)
    if 'cycling' in t: P['mode_cycling'] = 1
    return P
TAGS = {'cast_trigger', 'etb_trigger', 'attack_trigger', 'death_trigger', 'combat_damage_trigger', 'begin_combat_trigger', 'block_trigger',
        'life_payoff', 'conditional_body', 'mill', 'energy', 'life_cost', 'selection', 'body', 'land', 'mode_channel', 'mode_cycling',
        'flag_monarch', 'untap', 'keywords_only'}
# classes that passed the 20-card spot-check at this parser version (others are coded but don't count toward the bar until re-checked)
PASSED = {'removal', 'token', 'tutor', 'draw_engine', 'drain', 'burn', 'counterspell', 'sac_outlet', 'ritual', 'dork', 'rock', 'lifegain',
          'regenerate', 'protect', 'draw_spell', 'attach', 'extra_combat', 'phase', 'grant', 'anthem', 'alt_win', 'stax', 'reducer', 'ramp',
          'trick', 'flicker', 'discard', 'impulse', 'evasive_body', 'recursion', 'team_pump', 'copy', 'scaling_body', 'firebreathing', 'attack_pump', 'artifact_token', 'prevent', 'goad'}
def faces(c):
    tys = c['type'].split(' // '); txs = (c['text'] or '').split('\n//\n')
    if len(tys) == len(txs) and len(tys) > 1:
        out = []
        for i, (ty, tx) in enumerate(zip(tys, txs)):
            out.append(dict(c, type=ty, text=tx, p=c['p'] if i == 0 else None, t=c['t'] if i == 0 else None))
        return out
    return [c]
def merge(fs):
    P = {}
    for i, f in enumerate(fs):
        for k, v in f.items():
            if k == 'body' and i > 0 and 'body' in P: continue
            P.setdefault(k, v)
    return P
if len(sys.argv) > 1 and sys.argv[1] == 'sample':          # read-only spot-check: python parse.py sample <class> [seed]
    LIB = json.load(open(os.path.join(ROOT, 'library/cardlib.json')))
    import random; random.seed(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    xs = [o for o in LIB if sys.argv[2] in LIB[o]['prims']]
    for o in random.sample(xs, min(20, len(xs))): print('  ', U[o]['name'], '|', LIB[o]['prims'][sys.argv[2]], '|', re.sub(r'\s+', ' ', U[o]['text'])[:120])
    sys.exit()
LIB = {}; cls = collections.Counter()
for oid, c in U.items():
    if oid in HAND: LIB[oid] = HAND[oid]; continue
    fs = faces(c); parsed = [parse(f) for f in fs]; P = merge(parsed)
    if 'body' in P and P['body']['kw'] and any(k in P['body']['kw'] for k in ('flying', 'trample', 'menace', 'double strike', "can't be blocked")): P.setdefault('evasive_body', 1)
    rec = dict(name=c['name'], ci=c['ci'], type=c['type'], layout=c['layout'], mv=c['mv'], prims=P, parser=PARSER)
    if len(fs) > 1: rec['modes'] = [dict(face=i, type=f['type'], prims=pp) for i, (f, pp) in enumerate(zip(fs, parsed))]
    real = set(P) - TAGS
    landonly = set(P) <= {'land', 'mode_channel', 'mode_cycling', 'life_cost'} and 'land' in P
    rec['conf'] = 'auto' if real or landonly else 'unmodelled'
    rec['tier'] = 'playable' if (real & PASSED) else ('tag-only' if real or set(P) - {'body'} else 'none')
    LIB[oid] = rec
    for k in P: cls[k] += 1
json.dump(LIB, open(os.path.join(ROOT, 'library/cardlib.json'), 'w'))
def has_text(c): return bool(re.sub(r'\([^)]*\)', '', c['text'] or '').strip())
txt = [o for o, c in U.items() if has_text(c)]
nonland = [o for o in txt if not U[o]['type'].startswith('Land') and 'Land' not in U[o]['type'].split(' // ')[0]]
lands = [o for o in txt if o not in set(nonland)]
pl = sum(LIB[o]['tier'] == 'playable' for o in nonland)
print(f"parser {PARSER} | universe {len(U)} | with rules text {len(txt)} (non-land {len(nonland)}, land {len(lands)})")
print(f"  non-land PLAYABLE (>=1 handler-backed primitive from a spot-check-passed class): {pl} = {100*pl/len(nonland):.1f}%   [skill bar: 70%]")
print(f"  any tag or effect: {sum(LIB[o]['conf'] != 'unmodelled' for o in txt)} = {100*sum(LIB[o]['conf'] != 'unmodelled' for o in txt)/len(txt):.1f}%")
lu = sum(1 for o in lands if set(LIB[o]['prims']) - {'land', 'mode_channel', 'mode_cycling', 'life_cost', 'body'})
print(f"  lands: {len(lands)} | mana coded {sum('land' in LIB[o]['prims'] for o in lands)} | utility effect coded {lu}")
print(dict(cls.most_common()))
