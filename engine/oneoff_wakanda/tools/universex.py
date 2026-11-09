import os as _os, sys as _sys; HERE=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _sys.path.insert(0,HERE); _sys.path.insert(0,_os.path.join(HERE,'tools')); _os.chdir(HERE)
"""Universe sweep v2: every auto-coded card (GENX classes) into v4.1's least-synergy slot (Bast). Staged 1000 -> 4000 -> 12000 fresh seeds, control Bast -> Plains."""
import sys,json,time,re; 
import podwin as P, sim_r3 as m
GX=json.load(open('data/genx.json')); pool={c['name']:c for c in json.load(open('data/gw_pool.json'))}
x=json.load(open('decks/v41_final.json')); cmd=x[0]; SLOT='Bast, Panther Goddess'
B=dict(DORK=dict(m.DORK),RAMP=dict(m.RAMP),TUT=set(m.TUTOR_HAND),HOLD=set(m.HOLD),BODY=list(m.BODY_RANK))
def reset():
    m.GENX.clear(); m.DORK.clear(); m.DORK.update(B['DORK']); m.RAMP.clear(); m.RAMP.update(B['RAMP'])
    m.TUTOR_HAND.clear(); m.TUTOR_HAND.update(B['TUT']); m.HOLD.clear(); m.HOLD.update(B['HOLD']); m.BODY_RANK[:]=B['BODY']
def setup(c):
    reset(); p=pool[c]
    if c not in m.C: m.C[c]=dict(cost=p['cost'],mv=p['mv'],type=p['type'],p=p['p'],t=p['t'],text=p['text'],prod=p['prod'])
    e=GX[c]; m.GENX[c]=e
    if 'dork' in e: m.DORK[c]='A'
    if 'ramp' in e: m.RAMP[c]=e['ramp']
    if 'tutor' in e: m.TUTOR_HAND.add(c)
    if e.get('inst'): m.HOLD.add(c)
    if 'Creature' in p['type']: m.BODY_RANK.append(c)
    d=list(x); d[d.index(SLOT)]=c; return d
def ev(d,N,seed,modes=('pod',)):
    return [P.cum(m.run(d,cmd,N,seed=seed,mode=mo)[0],12 if mo=='pod' else 10) for mo in modes]
def keep(c,e):
    if c in x or c not in pool or pool[c]['gc'] or 'monarch' in (pool[c]['text'] or '').lower(): return False
    if 'body' in e: return e['body']['p']>=4 or bool(e['body']['kw'])
    return True
if __name__=='__main__':
    cands=[c for c,e in GX.items() if keep(c,e)]
    log=open('universex.log','w')
    def say(*a): print(*a,file=log,flush=True)
    say('candidates',len(cands)); reset(); b1=ev(x,1000,3001)[0]; s1=[]; t0=time.time()
    for i,c in enumerate(cands):
        d=setup(c); s1.append((ev(d,1000,3001)[0]-b1,c))
        if i%250==0: say('stage1',i,len(cands),round(time.time()-t0))
    s1.sort(reverse=True); say('stage1 top 25',[(round(v,1),c) for v,c in s1[:25]])
    reset(); b2=ev(x,4000,3002,('pod','gold')); s2=[]
    for v,c in s1[:60]:
        d=setup(c); r=ev(d,4000,3002,('pod','gold')); s2.append((r[0]-b2[0],r[1]-b2[1],c))
    s2.sort(reverse=True); say('stage2 top 15',[(round(a,1),round(b,1),c) for a,b,c in s2[:15]])
    reset(); b3=ev(x,12000,3003,('pod','gold')); ctl=list(x); ctl[ctl.index(SLOT)]='Plains'; c3=ev(ctl,12000,3003,('pod','gold')); s3=[]
    for a,b,c in s2[:15]:
        d=setup(c); r=ev(d,12000,3003,('pod','gold')); s3.append((round(r[0]-b3[0],1),round(r[1]-b3[1],1),c,{k:v for k,v in GX[c].items() if k in ('dork','ramp','anthem','grant','trick','tutor','reducer','draw','protect','counters','body')}))
    s3.sort(reverse=True,key=lambda r:r[0])
    json.dump(dict(cands=len(cands),s1=s1[:80],s2=s2,base3=b3,control3=[round(c3[0]-b3[0],1),round(c3[1]-b3[1],1)],s3=s3),open('universex.json','w'),indent=0)
    say('DONE control',[round(c3[0]-b3[0],1),round(c3[1]-b3[1],1)],'base',b3); say('stage3',s3)
