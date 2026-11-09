import os as _os, sys as _sys; HERE=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _sys.path.insert(0,HERE); _sys.path.insert(0,_os.path.join(HERE,'tools')); _os.chdir(HERE)
"""Spell sweep (skill v5.8): instants/sorceries, role-matched. Protection / phasing / flicker -> least-value protection slot (Flawless Maneuver, -0.5 when cut);
tricks / counters / draw spells -> least-synergy slot (Bast). Removal is listed, not scored (no opponent-threat model yet). Own wipes excluded (anti-synergy)."""
import sys,json,time; import universex as U, sim_r3 as m
GX=U.GX; x=U.x
def role(e): return 'prot' if ('protect' in e or 'flicker' in e) else ('kill' if any(k in e for k in ('trick','counters','drawspell')) else None)
def setup(c):
    d=U.setup(c); e=GX[c]
    if 'drawspell' in e and not any(k in e for k in ('trick','counters','protect','flicker')): m.HOLD.discard(c)
    slot='Flawless Maneuver' if role(e)=='prot' else 'Bast, Panther Goddess'
    d=list(x); d[d.index(slot)]=c; return d
cands=[c for c,e in GX.items() if e.get('inst') and role(e) and e.get('removal')!='wipe' and c not in x and not U.pool[c]['gc']]
log=open('spellsweep.log','w')
def say(*a): print(*a,file=log,flush=True)
say('candidates',len(cands),{r:sum(role(GX[c])==r for c in cands) for r in ('prot','kill')})
U.reset(); b1=U.ev(x,1000,5001)[0]; s1=[]
for i,c in enumerate(cands):
    s1.append((U.ev(setup(c),1000,5001)[0]-b1,c))
    if i%100==0: say('stage1',i)
s1.sort(reverse=True); say('stage1 top 20',[(round(v,1),c) for v,c in s1[:20]])
U.reset(); b2=U.ev(x,4000,5002,('pod','gold')); s2=[]
for v,c in s1[:40]:
    r=U.ev(setup(c),4000,5002,('pod','gold')); s2.append((r[0]-b2[0],r[1]-b2[1],c))
s2.sort(reverse=True); say('stage2 top 12',[(round(a,1),round(b,1),c) for a,b,c in s2[:12]])
U.reset(); b3=U.ev(x,12000,5003,('pod','gold')); out={}
for slot in ('Flawless Maneuver','Bast, Panther Goddess'):
    ctl=list(x); ctl[ctl.index(slot)]='Plains'; c3=U.ev(ctl,12000,5003,('pod','gold')); out[slot]=[round(c3[0]-b3[0],1),round(c3[1]-b3[1],1)]
s3=[]
for a,b,c in s2[:12]:
    r=U.ev(setup(c),12000,5003,('pod','gold')); s3.append((round(r[0]-b3[0],1),round(r[1]-b3[1],1),c,role(GX[c]),{k:v for k,v in GX[c].items() if k in ('trick','counters','drawspell','protect','phase','flicker')}))
s3.sort(reverse=True,key=lambda r:r[0])
json.dump(dict(cands=len(cands),s1=s1,s2=s2,base3=b3,controls=out,s3=s3),open('spellsweep.json','w'),indent=0)
say('DONE controls (slot -> Plains)',out,'base',b3); say('stage3',s3)
