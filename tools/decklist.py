"""Decklists in, decklists out. One plain-text format in the repo: decks/<name>/list.txt, lines "1 Card Name", commander(s) under "# Commander".
Import:  python3 tools/decklist.py import <file> <deck-name>   (accepts "1 Name", "1x Name", Moxfield "1 Name (SET) 123 *F*", Archidekt/any CSV with Quantity,Name columns)
Export:  python3 tools/decklist.py export <deck-name> [text|moxfield|csv|proxies]   (proxies = cards not in owned/owned.txt, for the print list)"""
import sys, os, re, csv, json, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def universe():
    U = json.load(open(os.path.join(ROOT, 'data/universe.json'))); idx = {}
    for oid, c in U.items():
        idx[c['name'].lower()] = oid
        for f in c['name'].split(' // '): idx.setdefault(f.lower(), oid)
    return U, idx
def parse_lines(text):
    if text.lstrip().lower().startswith(('quantity', 'count', 'qty', '"quantity"')) or ',' in text.splitlines()[0] and 'name' in text.splitlines()[0].lower():
        rows = list(csv.DictReader(io.StringIO(text)))
        qk = next(k for k in rows[0] if k.lower() in ('quantity', 'count', 'qty')); nk = next(k for k in rows[0] if k.lower() in ('name', 'card', 'card name'))
        return [(int(r[qk] or 1), r[nk].strip(), 'commander' in json.dumps(r).lower()) for r in rows if r[nk].strip()]
    out = []; section = ''
    for line in text.splitlines():
        l = line.strip()
        if not l: continue
        if l.startswith('#') or l.endswith(':') or l.lower() in ('commander', 'deck', 'sideboard', 'maybeboard'):
            section = l.lower(); continue
        m = re.match(r'^(\d+)\s*x?\s+(.+?)(\s+\([A-Za-z0-9]+\)\s*[\w-]*)?(\s+\*[A-Z]\*)?$', l)
        if m: out.append((int(m.group(1)), m.group(2).strip(), 'commander' in section))
        else: out.append((1, l, 'commander' in section))
    return out
def resolve(items):
    U, idx = universe(); res = []; bad = []
    for q, n, isc in items:
        oid = idx.get(n.lower())
        (res if oid else bad).append((q, U[oid]['name'] if oid else n, isc))
    return res, bad
def write(name, res):
    d = os.path.join(ROOT, 'decks', name); os.makedirs(d, exist_ok=True)
    cmd = [n for q, n, c in res if c]; main = [(q, n) for q, n, c in res if not c]
    with open(os.path.join(d, 'list.txt'), 'w', encoding='utf-8') as f:
        f.write('# Commander\n' + ''.join(f'1 {n}\n' for n in cmd) + '# Deck\n' + ''.join(f'{q} {n}\n' for q, n in main))
    return os.path.join(d, 'list.txt')
def load(name):
    return parse_lines(open(os.path.join(ROOT, 'decks', name, 'list.txt'), encoding='utf-8').read())
if __name__ == '__main__':
    act = sys.argv[1]
    if act == 'import':
        res, bad = resolve(parse_lines(open(sys.argv[2], encoding='utf-8').read()))
        print('wrote', write(sys.argv[3], res), '| cards', sum(q for q, _, _ in res), '| unresolved', bad)
    elif act == 'export':
        items = load(sys.argv[2]); fmt = sys.argv[3] if len(sys.argv) > 3 else 'text'
        if fmt in ('text', 'moxfield'): print('\n'.join(f'{q} {n}' for q, n, c in items))   # Moxfield and Archidekt both accept "1 Name"
        elif fmt == 'csv': print('Quantity,Name,Commander\n' + '\n'.join(f'{q},"{n}",{int(c)}' for q, n, c in items))
        elif fmt == 'proxies':
            owned_p = os.path.join(ROOT, 'owned', 'owned.txt'); owned = {n.lower(): q for q, n, _ in parse_lines(open(owned_p, encoding='utf-8').read())} if os.path.exists(owned_p) else {}
            basics = {'plains', 'island', 'swamp', 'mountain', 'forest', 'wastes'}
            need = [(q, n) for q, n, c in items if n.lower() not in basics and owned.get(n.lower(), 0) < q]
            print(f'# Proxies to print: {sum(q for q, _ in need)}\n' + '\n'.join(f'{q} {n}' for q, n in need))
