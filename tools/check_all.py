"""Deck health check (skill Gates 7-8, run after every B&R / Game Changer update / set release): python3 tools/check_all.py [deck ...] [--combos]
Checks per deck: 100 cards, singleton (basics excepted), commander legality + pairing (Partner, Partner with, Background, Friends forever, Doctor's companion),
colour identity of every card within the commander(s), Commander legality, Game Changers <= house max, red lines (monarch / initiative), and optionally
Commander Spellbook combos (2-card infinites = FAIL under house rules)."""
import sys, os, re, json, glob, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import decklist as DL
ROOT = DL.ROOT; BASICS = {'Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes'}
HOUSE = dict(max_gc=3, red_lines=('monarch', 'initiative'), max_combo_pieces_infinite=2)
def can_command(c):
    t = c['type'].split(' // ')[0]; tx = (c['text'] or '').lower()
    return ('Legendary' in t and 'Creature' in t) or 'can be your commander' in tx
def pair_ok(a, b):
    ta, tb = (a['text'] or '').lower(), (b['text'] or '').lower()
    if re.search(r'(^|\n)partner(\n|$| \()', ta) and re.search(r'(^|\n)partner(\n|$| \()', tb): return 'Partner'
    if f"partner with {b['name'].lower()}" in ta: return 'Partner with'
    if ('choose a background' in ta and 'Background' in b['type']) or ('choose a background' in tb and 'Background' in a['type']): return 'Background'
    if 'friends forever' in ta and 'friends forever' in tb: return 'Friends forever'
    if ("doctor's companion" in ta and 'Doctor' in b['type']) or ("doctor's companion" in tb and 'Doctor' in a['type']): return "Doctor's companion"
    return None
def combos(names, cmds):
    body = json.dumps({'commanders': [{'card': n} for n in cmds], 'main': [{'card': n} for n in names]}).encode()
    req = urllib.request.Request('https://backend.commanderspellbook.com/find-my-combos', data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'mtg-engine/0.1'})
    r = json.load(urllib.request.urlopen(req, timeout=60))['results']
    bad = [v for v in r.get('included', []) if len(v['uses']) <= 2 and any('nfinite' in p['feature']['name'] for p in v.get('produces', []))]
    return len(r.get('included', [])), bad
def check(name, U, idx, do_combos):
    items = DL.load(name); probs = []; warn = []
    cmds = [n for q, n, c in items if c]; total = sum(q for q, _, _ in items)
    if total != 100: probs.append(f'{total} cards (need 100)')
    for q, n, c in items:
        if q > 1 and n not in BASICS and 'any number of cards named' not in (U[idx[n.lower()]]['text'] or '').lower(): probs.append(f'not singleton: {q} {n}')
    C = [U[idx[n.lower()]] for n in cmds]
    if not C: probs.append('no commander marked (# Commander section)')
    for c in C:
        if not can_command(c): probs.append(f"{c['name']} can't be a commander")
    if len(C) == 2 and not pair_ok(*C): probs.append(f"{C[0]['name']} + {C[1]['name']} is not a legal pair")
    ci = set(x for c in C for x in c['ci'])
    gcs = []
    for q, n, c in items:
        card = U[idx[n.lower()]]
        if not set(card['ci']) <= ci: probs.append(f"colour identity: {n} {card['ci']}")
        if card.get('legal_commander') not in (None, 'legal'): probs.append(f"not Commander-legal: {n} ({card.get('legal_commander')})")
        if card['gc']: gcs.append(n)
        if re.search(r'monarch|the initiative', (card['text'] or '').lower()): probs.append(f'red line (monarch/initiative): {n}')
    if len(gcs) > HOUSE['max_gc']: probs.append(f'{len(gcs)} Game Changers > {HOUSE["max_gc"]}: {gcs}')
    if do_combos:
        try:
            n_c, bad = combos([n for q, n, c in items if not c], cmds)
            if bad: probs.append('2-card infinite(s): ' + '; '.join(' + '.join(u['card']['name'] for u in v['uses']) for v in bad))
            warn.append(f'Spellbook combos present: {n_c}')
        except Exception as e: warn.append(f'Spellbook check skipped ({type(e).__name__}) — run again with network')
    return dict(deck=name, commander=cmds, cards=total, game_changers=gcs, problems=probs, notes=warn, verdict='PASS' if not probs else 'FAIL')
if __name__ == '__main__':
    U, idx = DL.universe(); meta = json.load(open(os.path.join(ROOT, 'data/universe_meta.json'))) if os.path.exists(os.path.join(ROOT, 'data/universe_meta.json')) else {}
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'decks/*/list.txt'))]
    print('card data pulled:', meta.get('pulled', 'unknown — re-pull before trusting legality/GC results'))
    for n in names: print(json.dumps(check(n, U, idx, '--combos' in sys.argv), indent=1))
