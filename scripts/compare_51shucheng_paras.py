import re,os,glob,json,difflib,collections
REPO='C:/Users/Marc/Documents/1G1R/_Programmation/renegade-immortal-fr'
def norm(s): return re.sub(r'[\s　]+','',s)
def load(d,pat):
    out={}
    for f in glob.glob(d+'/'+pat):
        n=int(os.path.basename(f)[:4]); lines=open(f,encoding='utf-8').read().split('\n')
        paras=[norm(p) for p in lines[1:] if norm(p)]
        out[n]=paras
    return out
A=load(REPO+'/tmp/zh_aligned','*.txt'); B=load('zh51','*.txt')
def index(S):
    d=collections.defaultdict(list)
    for n,ps in S.items():
        for i,p in enumerate(ps): d[p].append((n,i))
    return d
iA,iB=index(A),index(B)
unA=[(n,i,p) for n in sorted(A) for i,p in enumerate(A[n]) if p not in iB]
unB=[(n,i,p) for n in sorted(B) for i,p in enumerate(B[n]) if p not in iA]
print('paras A',sum(len(v) for v in A.values()),'B',sum(len(v) for v in B.values()))
print('unmatched A',len(unA),'chars',sum(len(p) for _,_,p in unA)); print('unmatched B',len(unB),'chars',sum(len(p) for _,_,p in unB))
# fuzzy pair unmatched within +-2 chapters
byB=collections.defaultdict(list)
for n,i,p in unB: byB[n].append((i,p))
pairs=[]; usedB=set(); onlyA=[]
for n,i,p in unA:
    best=None;br=0
    for m in range(n-2,n+3):
        for j,q in byB.get(m,[]):
            if (m,j) in usedB: continue
            if abs(len(p)-len(q))>max(len(p),len(q))*0.6: continue
            r=difflib.SequenceMatcher(None,p,q,autojunk=False).quick_ratio()
            if r>br and r>0.6:
                r=difflib.SequenceMatcher(None,p,q,autojunk=False).ratio()
                if r>br: br=r;best=(m,j,q)
    if best and br>0.6: usedB.add(best[:2]); pairs.append((n,i,p,best[0],best[1],best[2],round(br,3)))
    else: onlyA.append((n,i,p))
onlyB=[(n,i,p) for n,i,p in unB if (n,i) not in usedB]
json.dump({'pairs':pairs,'onlyA':onlyA,'onlyB':onlyB},open('paracmp.json','w',encoding='utf-8'),ensure_ascii=False)
print('variant pairs',len(pairs),' onlyA',len(onlyA),'chars',sum(len(p) for *_,p in onlyA),' onlyB',len(onlyB),'chars',sum(len(p) for *_,p in onlyB))
print('pairs with *** in A:',sum(1 for x in pairs if '***' in x[2]), 'stars A total paras',sum(1 for n in A for p in A[n] if '***' in p))
hi=[x for x in pairs if x[6]>=0.9]; print('pairs ratio>=0.9',len(hi))
import itertools
print('--- sample pairs <0.9'); 
for x in [x for x in pairs if x[6]<0.9][:8]: print(x[0],x[6],'\nA:',x[2][:150],'\nB:',x[5][:150])
print('--- onlyA by chapter (top)'); c=collections.Counter(n for n,_,p in onlyA); print(c.most_common(40))
print('--- onlyB by chapter (top)'); c=collections.Counter(n for n,_,p in onlyB); print(c.most_common(40))
