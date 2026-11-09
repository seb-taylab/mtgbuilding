"""Inventory: what you have today, where it is, and what you still need.
  python3 tools/inventory.py ingest <workbook.xlsx> [batch1.txt] [batch2.txt]   # seed from the print-list workbook
  python3 tools/inventory.py precon <MTGJSON deck fileName>   # add a precon you own as real cards, e.g. WakandaForever_MSC
  python3 tools/inventory.py add <real|proxy_printed|proxy_pending> <qty> <card name>
  python3 tools/inventory.py needs <deck>        # for a deck in decks/<deck>/list.txt: have / take from another deck / pending print / print / buy
  python3 tools/inventory.py conflicts           # cards needed by more active decks than you have copies
  python3 tools/inventory.py spares              # copies not used by any active deck
Files: inventory/collection.csv (card, real, proxy_printed, proxy_pending, note), inventory/allocations.csv (deck, card, qty, source).
Forms: real = a real card you own · proxy_printed = printed proxy in hand · proxy_pending = ordered/printing (e.g. batch 2)."""
import sys, os, csv, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import decklist as DL
ROOT = DL.ROOT; INV = os.path.join(ROOT, 'inventory'); BASICS = {'Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes'}
def canon():
    U, idx = DL.universe(); return U, idx, (lambda n: U[idx[n.strip().lower()]]['name'] if n and n.strip().lower() in idx else None)
def read_txt(p):
    out = collections.Counter()
    for l in open(p, encoding='utf-8'):
        m = re.match(r'^\s*(\d+)\s*x?\s+(.+?)\s*$', l)
        if m: out[m.group(2)] += int(m.group(1))
    return out
def ingest(xlsx, b1=None, b2=None):
    import openpyxl
    U, idx, nm = canon(); wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    col = collections.defaultdict(lambda: dict(real=0, proxy_printed=0, proxy_pending=0, note=set()))
    m = list(wb['Master'].iter_rows(values_only=True))
    for r in m[4:]:
        if not r[0] or not nm(r[0]): continue
        n = nm(r[0])
        if r[5] == 'Own': col[n]['real'] = max(col[n]['real'], 1); col[n]['note'].add(f'own ({r[2]})')
    if b1:
        for n, q in read_txt(b1).items():
            if nm(n): col[nm(n)]['proxy_printed'] += q
    if b2:
        for n, q in read_txt(b2).items():
            if nm(n): col[nm(n)]['proxy_pending'] += q
    alloc = []
    for ws in wb.worksheets:
        if not ws.title.startswith('Deck - '): continue
        rows = list(ws.iter_rows(values_only=True)); title = ' '.join(str(x) for x in (rows[0] or ()) if x)
        if re.search(r'RETIRED|TORN DOWN', title): continue
        deck = ws.title[7:]
        if deck.startswith('Wakanda') and deck != 'Wakanda v4.1': continue   # older Wakanda versions are history tabs
        try: h = next(i for i, r in enumerate(rows) if r and r[0] and str(r[0]).startswith('Card'))
        except StopIteration: continue
        hdr = [str(x or '') for x in rows[h]]; si = next((i for i, x in enumerate(hdr) if x.startswith('Source')), None)
        for r in rows[h + 1:]:
            if not r or not any(r): break                 # the deck block ends at the first blank row (later blocks = cuts / notes)
            n = nm(str(r[0])) if r[0] else None
            if n: alloc.append(dict(deck=deck, card=n, qty=1, source=str(r[si]) if si is not None and r[si] else ''))
    os.makedirs(INV, exist_ok=True)
    with open(os.path.join(INV, 'collection.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['card', 'real', 'proxy_printed', 'proxy_pending', 'note'])
        for n in sorted(col): w.writerow([n, col[n]['real'], col[n]['proxy_printed'], col[n]['proxy_pending'], '; '.join(sorted(col[n]['note']))])
    with open(os.path.join(INV, 'allocations.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['deck', 'card', 'qty', 'source']); w.writeheader(); w.writerows(alloc)
    print(f'collection: {len(col)} cards | real {sum(v["real"] for v in col.values())} · printed proxies {sum(v["proxy_printed"] for v in col.values())} · pending {sum(v["proxy_pending"] for v in col.values())}')
    print('active decks:', dict(collections.Counter(a['deck'] for a in alloc)))
def save(col):
    rows = list(csv.DictReader(open(os.path.join(INV, 'collection.csv'), encoding='utf-8'))); by = {r['card']: r for r in rows}
    for n, c in col.items():
        r = by.setdefault(n, dict(card=n, real=0, proxy_printed=0, proxy_pending=0, note=''))
        for k in ('real', 'proxy_printed', 'proxy_pending'): r[k] = c[k]
        if c.get('note'): r['note'] = '; '.join(x for x in sorted(set(filter(None, (r.get('note') or '').split('; ') + [c['note']]))))
    with open(os.path.join(INV, 'collection.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['card', 'real', 'proxy_printed', 'proxy_pending', 'note']); w.writeheader(); w.writerows(sorted(by.values(), key=lambda r: r['card']))
def precon(fname):
    import urllib.request
    U, idx, nm = canon(); col, _ = load()
    d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://mtgjson.com/api/v5/decks/{fname}.json', headers={'User-Agent': 'mtg-engine/0.1'}), timeout=60))['data']
    added = 0
    for part in ('commander', 'mainBoard', 'sideBoard', 'displayCommander'):
        for c in d.get(part, []) or []:
            n = nm(c['name']) or nm(c.get('faceName', '') or '')
            if not n: continue
            e = col.setdefault(n, dict(real=0, proxy_printed=0, proxy_pending=0)); e['real'] += c.get('count', 1); e['note'] = f"precon: {d['name']}"; added += c.get('count', 1)
    save(col); print(f"added {added} real cards from {d['name']} ({d.get('code')})")
def add(form, qty, name):
    U, idx, nm = canon(); col, _ = load(); n = nm(name)
    if not n: print('unknown card:', name); return
    e = col.setdefault(n, dict(real=0, proxy_printed=0, proxy_pending=0)); e[form] += int(qty); save(col); print(n, e)
def load():
    col = {r['card']: dict(real=int(r['real']), proxy_printed=int(r['proxy_printed']), proxy_pending=int(r['proxy_pending'])) for r in csv.DictReader(open(os.path.join(INV, 'collection.csv'), encoding='utf-8'))}
    alloc = list(csv.DictReader(open(os.path.join(INV, 'allocations.csv'), encoding='utf-8')))
    return col, alloc
def needs(deck):
    U, idx, nm = canon(); col, alloc = load()
    items = [(q, n) for q, n, c in DL.load(deck)]
    used = collections.defaultdict(list)
    for a in alloc:
        if a['deck'].lower().replace(' ', '') not in (deck.lower(), deck.lower() + 'v4.1') and not a['deck'].lower().startswith(deck.lower()): used[a['card']].append(a['deck'])
    out = collections.defaultdict(list)
    for q, n in items:
        if n in BASICS: out['basic land'].append(n); continue
        c = col.get(n, dict(real=0, proxy_printed=0, proxy_pending=0)); inhand = c['real'] + c['proxy_printed']; elsewhere = used.get(n, [])
        if inhand > len(elsewhere): out['have (free copy)'].append(n)
        elif inhand > 0: out['have, but used in ' + '/'.join(sorted(set(elsewhere)))].append(n)
        elif c['proxy_pending']: out['coming in pending print batch'].append(n)
        else:
            price = U[idx[n.lower()]].get('price_usd')
            out['need: print proxy' if not price or float(price) >= 2 else 'need: cheap to buy (< US$2)'].append(n + (f' (${price})' if price else ''))
    print(f'# {deck}: {sum(q for q, _ in items)} cards')
    for k in sorted(out, key=lambda k: (not k.startswith('have (free'), k)): print(f'\n## {k} — {len(out[k])}\n' + '\n'.join('  ' + x for x in sorted(out[k])))
def conflicts():
    col, alloc = load(); need = collections.defaultdict(set)
    for a in alloc: need[a['card']].add(a['deck'])
    for n, ds in sorted(need.items()):
        c = col.get(n, dict(real=0, proxy_printed=0, proxy_pending=0)); have = c['real'] + c['proxy_printed']
        if len(ds) > have + c['proxy_pending'] and n not in BASICS: print(f'{n}: needed by {sorted(ds)}, have {have} (+{c["proxy_pending"]} pending)')
def spares():
    col, alloc = load(); used = collections.Counter(a['card'] for a in alloc)
    for n, c in sorted(col.items()):
        free = c['real'] + c['proxy_printed'] - used.get(n, 0)
        if free > 0: print(f'{free} {n}' + (' (real)' if c['real'] else ''))
if __name__ == '__main__':
    a = sys.argv[1]
    if a == 'ingest': ingest(*sys.argv[2:5])
    elif a == 'precon': precon(sys.argv[2])
    elif a == 'add': add(sys.argv[2], sys.argv[3], ' '.join(sys.argv[4:]))
    elif a == 'needs': needs(sys.argv[2])
    elif a == 'conflicts': conflicts()
    elif a == 'spares': spares()
