"""Pull every Commander-legal card (one record per oracle_id) from the Scryfall search API into data/universe.json."""
import json, time, urllib.request, urllib.parse, sys, hashlib, datetime
q = 'legal:commander'; url = 'https://api.scryfall.com/cards/search?unique=cards&order=name&q=' + urllib.parse.quote(q); out = {}
H = {'User-Agent': 'mtg-engine/0.1 (deck research)', 'Accept': 'application/json'}
while url:
    for k in range(4):
        try: r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60)); break
        except Exception as e: time.sleep(2 + 3 * k)
    for c in r['data']:
        f = c.get('card_faces', [c])
        out[c['oracle_id']] = dict(name=c['name'], layout=c['layout'], type=c['type_line'], ci=c['color_identity'], mv=c.get('cmc', 0),
            cost=f[0].get('mana_cost', '') or c.get('mana_cost', ''), text='\n//\n'.join(x.get('oracle_text', '') for x in f) if 'card_faces' in c else c.get('oracle_text', ''),
            p=f[0].get('power', c.get('power')), t=f[0].get('toughness', c.get('toughness')), prod=c.get('produced_mana', []), rar=c['rarity'],
            gc=c.get('game_changer', False), kw=c.get('keywords', []), released=c.get('released_at'),
            price_usd=(c.get('prices') or {}).get('usd'), legal_commander=c['legalities'].get('commander'))
        out[c['oracle_id']]['hash'] = hashlib.sha1((out[c['oracle_id']]['type'] + '|' + (out[c['oracle_id']]['text'] or '')).encode()).hexdigest()[:12]
    url = r.get('next_page'); time.sleep(0.11)
    if len(out) % 5000 < 175: print(len(out), file=sys.stderr, flush=True)
json.dump(out, open('data/universe.json', 'w'))
json.dump(dict(pulled=datetime.date.today().isoformat(), cards=len(out), query=q, note='GC flag and legality per oracle card; Gate 8 re-checks every printing (strictest wins) for the final list'), open('data/universe_meta.json', 'w'), indent=1); print('oracle cards', len(out))
