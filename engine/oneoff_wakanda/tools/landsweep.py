import os as _os, sys as _sys; HERE=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _sys.path.insert(0,HERE); _sys.path.insert(0,_os.path.join(HERE,'tools')); _os.chdir(HERE)
"""Utility-land sweep (skill v5.7): every legal non-basic GW land swapped for a basic in v4.1. Control = basic-for-basic (Plains -> Forest). Staged 1000 -> 4000 -> 12000 fresh seeds."""
import sys,json,time; 
import podwin as P, sim_r3 as m
LP={c['name']:c for c in json.load(open('data/land_pool.json'))}; LX=json.load(open('data/landx.json'))
x=json.load(open('decks/v41_final.json')); cmd=x[0]; SLOT='Plains'
def setup(c):
    m.LANDX.clear(); p=LP[c]
    if c not in m.C: m.C[c]=dict(cost=p['cost'],mv=p['mv'],type=p['type'],p=p['p'],t=p['t'],text=p['text'],prod=p['prod'])
    m.LANDX[c]={k:v for k,v in LX[c].items() if k!='roles'}
    d=list(x); d[d.index(SLOT)]=c; return d
def ev(d,N,seed,modes=('pod',)): return [P.cum(m.run(d,cmd,N,seed=seed,mode=mo)[0],12 if mo=='pod' else 10) for mo in modes]
cands=[c for c in LX if c not in x and not LP[c]['gc']]
log=open('landsweep.log','w')
def say(*a): print(*a,file=log,flush=True)
say('candidates',len(cands)); m.LANDX.clear(); b1=ev(x,1000,4001)[0]; s1=[]
for i,c in enumerate(cands):
    d=setup(c); s1.append((ev(d,1000,4001)[0]-b1,c))
    if i%100==0: say('stage1',i)
s1.sort(reverse=True); say('stage1 top 20',[(round(v,1),c) for v,c in s1[:20]])
m.LANDX.clear(); b2=ev(x,4000,4002,('pod','gold')); s2=[]
for v,c in s1[:30]:
    d=setup(c); r=ev(d,4000,4002,('pod','gold')); s2.append((r[0]-b2[0],r[1]-b2[1],c))
s2.sort(reverse=True); say('stage2 top 10',[(round(a,1),round(b,1),c) for a,b,c in s2[:10]])
m.LANDX.clear(); b3=ev(x,12000,4003,('pod','gold')); ctl=list(x); ctl[ctl.index(SLOT)]='Forest'; c3=ev(ctl,12000,4003,('pod','gold')); s3=[]
for a,b,c in s2[:10]:
    d=setup(c); r=ev(d,12000,4003,('pod','gold')); s3.append((round(r[0]-b3[0],1),round(r[1]-b3[1],1),c,LX[c]['roles']))
s3.sort(reverse=True,key=lambda r:r[0])
json.dump(dict(cands=len(cands),s1=s1,s2=s2,base3=b3,control3=[round(c3[0]-b3[0],1),round(c3[1]-b3[1],1)],s3=s3),open('landsweep.json','w'),indent=0)
say('DONE control',[round(c3[0]-b3[0],1),round(c3[1]-b3[1],1)],'base',b3); say('stage3',s3)
