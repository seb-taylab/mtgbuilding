import sys,os,json,collections; HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import sim_r3 as m, opp_sim as O
G=json.load(open(os.path.join(HERE,'data','gen.json'))); m.GENA['Adaptive Omnitool']=G['GEN']['Adaptive Omnitool']
D=O.dists(8000,seed=7); TAB=collections.Counter(min(a,b,c) for a,b,c in zip(*D.values())); NT=sum(TAB.values())
def podwin(K, shift=0):
    tab={t+shift:v/NT for t,v in TAB.items()}
    gt=lambda t: sum(v for k,v in tab.items() if k>t); eq=lambda t: tab.get(t,0)
    return round(100*sum(p*(gt(t)+0.5*eq(t)) for t,p in K.items() if t<99),1)
def cum(K,t): return round(100*sum(v for k,v in K.items() if k<=t),1)
def report(name,d,cmd,N=8000,seed=202):
    out={}
    for mode in ('gold','disrupt','pod'):
        K,_=m.run(d,cmd,N,seed=seed,mode=mode); out[mode]=K
    P=out['pod']
    print(f"{name:34s} gold T10 {cum(out['gold'],10)} | old-disrupt T12 {cum(out['disrupt'],12)} | POD-disrupt T8 {cum(P,8)} T10 {cum(P,10)} T12 {cum(P,12)} | POD WIN {podwin(P)}%  (table 1 turn faster {podwin(P,-1)}% / slower {podwin(P,1)}%)",flush=True)
    return out
if __name__=='__main__':
    V3=json.load(open(os.path.join(HERE,'decks','v3.json')))
    def sw(d,o,i):
        d=list(d)
        for a,b in zip(o,i): d[d.index(a)]=b
        return d
    V3n=sw(V3,['Okoye, Mighty and Adored','The Spear of Bashenga'],['Forest','Plains'])
    json.dump(V3n,open('wk/v3_nomonarch.json','w'))
    report('Wakanda v3 (no monarch)',V3n,'Shuri, the Black Panther')
    report('Wakanda v2',json.load(open(os.path.join(HERE,'decks','shuri_final.json'))),'Shuri, the Black Panther')
