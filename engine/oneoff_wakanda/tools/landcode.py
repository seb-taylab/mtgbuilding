import os as _os, sys as _sys; HERE=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _sys.path.insert(0,HERE); _sys.path.insert(0,_os.path.join(HERE,'tools')); _os.chdir(HERE)
"""Code every legal non-basic green-white land by role (skill v5.7 Gate 3 step 5b)."""
import json, re, collections
D = 'data/'
pool = json.load(open(D + 'land_pool.json'))
def acost(s):
    n = sum(int(x) for x in re.findall(r'\{(\d+)\}', s)) + len(re.findall(r'\{[GWCBRU](?:/[GWP])?\}', s)) + 3 * len(re.findall(r'\{X\}', s))
    return n
def code(c):
    t = re.sub(r'\([^)]*\)', '', c['text'] or ''); tl = t.lower(); e = {}; roles = set()
    prod = set(c['prod'])
    if {'G', 'W'} <= prod or len(prod) >= 3: roles.add('fixing')
    if re.search(r'enters( the battlefield)? tapped', tl) and 'unless' not in tl and 'you may pay' not in tl: e['tapped'] = 1
    if 'Artifact' in c['type']: e['art'] = 1; roles.add('artifact land')
    if '//' in c['name']: roles.add('spell-land')
    if 'cycling' in tl or 'channel' in tl: roles.add('cycling/channel')
    if re.search(r'becomes? an? [^.]*creature', tl): roles.add('creature land')
    for line in t.split('\n'):
        if ':' not in line: continue
        cost, eff = line.split(':', 1); el = eff.lower(); cl = cost.lower()
        if '{t}' not in cl and 'sacrifice' not in cl: continue
        n = acost(cost)
        if re.search(r"target (attacking )?creature( you control)? can.t be blocked", el): e['unblock'] = n; roles.add('utility')
        m = re.search(r'creatures you control get \+(\d)/\+(\d)', el)
        if m: e['pump'] = (n, int(m.group(1))); roles.add('utility')
        if 'put a +1/+1 counter on each creature you control' in el: e['pump'] = (n, 1); e['perm'] = 1; roles.add('utility')
        m = re.search(r'target creature (you control )?gets \+(x|\d)/\+0', el)
        if m: e['pump'] = (n, 3 if m.group(2) == 'x' else int(m.group(2))); roles.add('utility')
        if re.search(r'target (creature|permanent|legendary creature) you control gains (hexproof|indestructible|shroud|protection)', el) or 'phase out' in el: e['protect'] = n; roles.add('utility')
        if re.search(r'draw a card', el) and 'sacrifice' not in cl: roles.add('utility')
        if re.search(r'create [^.]*creature token', el): roles.add('utility')
    e['roles'] = sorted(roles) or ['other']
    return e
LX = {c['name']: code(c) for c in pool}
json.dump(LX, open(D + 'landx.json', 'w'))
rc = collections.Counter(r for v in LX.values() for r in v['roles'])
sim = sum(1 for v in LX.values() if any(k in v for k in ('unblock', 'pump', 'protect', 'art')))
coded = sum(1 for v in LX.values() if v['roles'] != ['other'])
print('lands', len(LX), '| role-coded', coded, f'{100*coded/len(LX):.0f}%', '| with a sim effect', sim, dict(rc))
for k in ('unblock', 'pump', 'protect'):
    print(k, [n for n, v in LX.items() if k in v][:12])
