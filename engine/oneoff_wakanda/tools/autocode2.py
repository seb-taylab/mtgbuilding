import os as _os, sys as _sys; HERE=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _sys.path.insert(0,HERE); _sys.path.insert(0,_os.path.join(HERE,'tools')); _os.chdir(HERE)
"""Auto-code v2: read oracle text of every legal green-white non-land card and map it to effects the Wakanda model can run.
Classes (a card can have several):
  dork        creature with a mana ability                      -> extra mana from next turn
  ramp        spell/permanent that puts lands onto the battlefield -> +1 mana permanently
  rock        artifact mana (from v1)                           -> already in gen.json ROCKS
  anthem      static '+N/+N' to creatures you control / commander creatures / equipped creature  -> carrier power
  grant       static keyword grant to your creatures/commander (flying, double strike, trample, unblockable, haste, indestructible, hexproof)
  trick       instant/sorcery: target creature gets +N/+N and/or keyword until end of turn -> one-shot on a lethal combat
  tutor       searches the library for an artifact / equipment / aura / creature card -> tutor to hand
  reducer     artifact / equipment spells or equip abilities cost less
  draw        repeatable draw engine (upkeep / attack / artifact or equipment entering / combat damage)
  protect     instant giving hexproof / indestructible / protection / phasing to your creature(s) -> saves the commander once
  counters    puts +1/+1 counters on a creature you control (ETB or repeatable) -> carrier power
  combat      additional combat phase
Everything else is 'uncoded'. Thresholds are conservative: a card is coded only if a regex matches its oracle text."""
import json, re, collections
pool = json.load(open('data/gw_pool.json'))
g1 = json.load(open('data/gen.json'))
KW = ('flying', 'double strike', 'trample', "can't be blocked", 'haste', 'indestructible', 'hexproof', 'first strike', 'vigilance', 'lifelink')
def num(s):
    return {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'x': 3}.get(s, None) if not s.isdigit() else int(s)
def code(c):
    t = re.sub(r'\([^)]*\)', '', (c['text'] or '').lower()); ty = c['type']; out = {}   # reminder text removed
    cre = 'Creature' in ty
    if cre and 'spend this mana only' not in t and re.search(r'(^|\n)\{t\}: add (\{[wgc]\}|one mana|two mana|\{[wg]\} or \{[wg]\})', t): out['dork'] = 1
    if re.search(r'search your library for (up to (one|two) )?basic land cards?.{0,80}onto the battlefield|put (a|up to one|up to two) land cards? from your hand onto the battlefield|search your library for (a|up to two) (forest|plains|land) cards?.{0,60}onto the battlefield', t):
        out['ramp'] = 2 if re.search(r'up to two|two basic', t) else 1
    m = re.search(r'(?:^|\n|\. |and )(creatures you control|other creatures you control|commander creatures you control|equipped creature|enchanted creature|other creatures you control|legendary creatures you control|heroes you control) gets? \+(\d+)/\+(\d+)', t)
    sent = lambda a, b: t[t.rfind('.', 0, a) + 1: (t.find('.', b) if t.find('.', b) >= 0 else len(t))]
    if m and not re.search(r'until end of turn|as long as|if you|for each', sent(m.start(), m.end())) and not any(x in ty for x in ('Equipment', 'Aura', 'Planeswalker', 'Saga', 'Instant', 'Sorcery')):
        out['anthem'] = int(m.group(2))
    g = re.search(r'(?:^|\n|\. )(creatures you control|other creatures you control|commander creatures you control|legendary creatures you control|attacking creatures you control) (have|gain) ([a-z ,]+?)(\.| until| as long)', t)
    if g and g.group(4).strip() not in ('until',) and 'until end of turn' not in sent(g.start(), g.end()):
        kws = [k for k in KW[:7] if k in g.group(3)]
        if kws: out['grant'] = kws
    if ('Instant' in ty or 'Sorcery' in ty):
        m = re.search(r'target creature( you control)? gets \+(\d+|x)/\+(\d+|x)', t)
        kws = [k for k in KW if re.search(r'target creature[^.]*gains? [^.]*' + k, t)]
        if m or kws:
            out['trick'] = dict(n=num(m.group(2)) if m else 0, kw=kws)
    if re.search(r'search your library for (a|an|up to one|up to two)[^.]{0,40}(artifact|equipment|aura|creature) card', t) and 'basic land' not in t:
        out['tutor'] = 1
    if re.search(r'(artifact|equipment|historic) spells you cast cost \{?\d?\}? ?less|equip abilities you activate cost \{\d\} less|equip costs you pay cost', t):
        out['reducer'] = 1
    if not ('Instant' in ty or 'Sorcery' in ty) and re.search(r'(at the beginning of your (upkeep|end step|draw step)|whenever (this creature|equipped creature|enchanted creature|a creature you control|you attack|an? (artifact|equipment) (you control )?enters|you cast an? (artifact|equipment))[^.]{0,40}(attacks|deals combat damage to a player|enters|,))[^.]{0,40}draw (a|two) cards?', t):
        out['draw'] = 1
    if 'Instant' in ty and re.search(r'(target creature you control|creatures you control|permanents you control|target permanent you control)[^.]{0,40}(gains? |have )?(hexproof|indestructible|protection from|phase out)', t):
        out['protect'] = 1
    if re.search(r'put (a|two|three|x) \+1/\+1 counters? on (target|each) creature you control|put (a|two|three) \+1/\+1 counters? on target creature', t) and 'opponent' not in t:
        mm = re.search(r'put (a|two|three|x) \+1/\+1', t); out['counters'] = {'a': 1, 'two': 2, 'three': 3, 'x': 2}[mm.group(1)]
    if 'additional combat phase' in t: out['combat'] = 1
    spell = 'Instant' in ty or 'Sorcery' in ty
    m = re.search(r'draw (a|two|three|four|x) cards?', t)
    if spell and m and 'each player' not in t and 'target player' not in t: out['drawspell'] = {'a': 1, 'two': 2, 'three': 3, 'four': 4, 'x': 3}[m.group(1)]
    if re.search(r'exile (up to (one|two) |another |any number of )?target (creature|creatures|nonland permanent|nonland permanents|artifact or creature|permanent)s?[^.]{0,30}you (control|own)[^.]*(, then return|\. return)', t): out['flicker'] = 1
    if 'phase out' in t or 'phases out' in t:
        if re.search(r'(you control|you phase out|your )', t): out['phase'] = 1; out['protect'] = 1
    m = re.search(r'(destroy|exile) (target|each|all|up to one target) (attacking )?(creature|artifact|enchantment|nonland permanent|permanent|artifact or enchantment|creature or planeswalker)', t)
    if m and 'you control' not in t[m.start():m.end() + 40]: out['removal'] = 'wipe' if m.group(2) in ('each', 'all') else 'target'
    if 'channel' in t: out['channel'] = 1
    if cre and not out:
        try: pw = int(c['p'])
        except Exception: pw = 0
        if pw >= 2: out['body'] = dict(p=pw, kw=[k for k in ('flying', 'trample', 'double strike', 'first strike', "can't be blocked", 'haste', 'hexproof', 'indestructible') if k in t])
    return out
GENX = {}; cats = collections.Counter()
for c in pool:
    if c['name'] in g1['GEN'] or c['name'] in g1['ROCKS']: continue
    e = code(c)
    if e:
        e['inst'] = 'Instant' in c['type'] or 'Sorcery' in c['type']
        if 'protect' in e: e['mass'] = bool(re.search(r'(creatures|permanents) you control', (c['text'] or '').lower()))
        GENX[c['name']] = dict(e, mv=c['mv'], cost=c['cost'], type=c['type'], rar=c['rar'], gc=c['gc'], p=c['p'], t=c['t'])
        for k in e:
            if k not in ('inst', 'mass'): cats[k] += 1
nb = sum(1 for v in GENX.values() if 'body' not in v)
coded = len(GENX) + len(g1['GEN']) + len(g1['ROCKS'])
json.dump(GENX, open('data/genx.json', 'w'))
print('effect-coded (no vanilla bodies)', nb + len(g1['GEN']) + len(g1['ROCKS']), f"= {100*(nb + len(g1['GEN']) + len(g1['ROCKS']))/len(pool):.1f}%"); print('new coded', len(GENX), '| total coded', coded, f'of {len(pool)} = {100*coded/len(pool):.1f}%'); print(dict(cats))
