"""Flag drift between the shared constants (profile = source of truth) and the tools/specs that repeat them: python3 tools/check_constants.py"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prof = open(os.path.join(ROOT, 'profiles/seb.yaml'), encoding='utf-8').read()
max_gc = int(re.search(r'max_gc:\s*(\d+)', prof).group(1))
checks = {'tools/check_all.py': rf'max_gc={max_gc}', 'BUILDER_SPEC.md': r'red_lines: from profile', 'ENGINE_SPEC.md': r'house\.first_player_skips_draw'}
bad = [f for f, pat in checks.items() if not re.search(pat, open(os.path.join(ROOT, f), encoding='utf-8').read())]
print('constants OK' if not bad else f'DRIFT in: {bad}'); sys.exit(1 if bad else 0)
