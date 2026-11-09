"""Reproduce the Wakanda v4.1 regression numbers with exact seeds (run from anywhere): python3 engine/oneoff_wakanda/reproduce.py"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sim_r3 as m, podwin as P
x = json.load(open(os.path.join(HERE, 'decks', 'v41_final.json'))); cmd = x[0]
RUNS = [('goldfish_T10', 'gold', 10, 12000, 2026), ('disruption_T12', 'disrupt', 12, 12000, 2027), ('pod_T12', 'pod', 12, 12000, 2028)]
out = {}
for name, mode, T, N, seed in RUNS:
    K, _ = m.run(x, cmd, N, seed=seed, mode=mode); out[name] = dict(value=P.cum(K, T), N=N, seed=seed, mode=mode)
    if mode == 'pod': out['pod_win'] = dict(value=round(P.podwin(K), 1), N=N, seed=seed, table_seed=7)
print(json.dumps(out, indent=1))
if len(sys.argv) > 1 and sys.argv[1] == '--write':
    p = os.path.join(HERE, '..', '..', 'regression', 'regression.json'); r = json.load(open(p)); r['expected_exact'] = out; json.dump(r, open(p, 'w'), indent=1)
