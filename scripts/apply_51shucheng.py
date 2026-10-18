import re,os,glob,json,sys,collections,shutil
REPO='C:/Users/Marc/Documents/1G1R/_Programmation/renegade-immortal-fr'
DRY='--apply' not in sys.argv
def norm(s): return re.sub(r'[\s　]+','',s)
ZONE=lambda n: 43<=n<=71
A={}; Afile={}
for f in glob.glob(REPO+'/tmp/zh_aligned/*.txt'):
    n=int(os.path.basename(f)[:4]); lines=open(f,encoding='utf-8').read().split('\n')
    A[n]=[norm(p) for p in lines[1:] if norm(p)]; Afile[n]=(f,lines[0])
B={}
for f in glob.glob('zh51/*.txt'):
    n=int(os.path.basename(f)[:4]); lines=open(f,encoding='utf-8').read().split('\n')
    B[n]=[norm(p) for p in lines[1:] if norm(p) and 'adsbygoogle' not in p]
d=json.load(open('paracmp.json',encoding='utf-8'))
log=[]
# --- step1 variants
pairmap={}  # (m,j)->(n,i)
for n,i,p,m,j,q,r in d['pairs']:
    pairmap[(m,j)]=(n,i)
    if ZONE(n): continue
    ok=(r>=0.9 and len(q)>=len(p)-6) or ('*' in p and r>=0.7) or (len(q)>len(p)+10 and q.startswith(p[:max(10,len(p)-5)]) and r>=0.6) or (r>=0.85 and re.search(r'[（(]?ps[：:]',p,re.I)) or (r>=0.8 and re.search(r'本站.*地址',p))
    if ok and A[n][i]==p:
        A[n][i]=q; log.append(('VAR',n,i,round(r,3),p[:60],q[:60]))
# --- step2 insertions
NOTE=re.compile(r'月票|更新|兄弟|大家|推荐|点滴|去痛片|见谅|莫急|斟酌下笔|酝酿|利息|神作|第[一二三四五六七八九十]+卷|^【.*】$|承诺|哈哈|已经修改|笔误|汗……|我写|大纲|路人甲|配角|牙痛|生日|访谈|中暑|虚汗|动画片|机场|补上|本章|悲催|修改了|见仁见智|决战，王林绝不|我喜欢|希望你也喜欢|慢慢挖|牙科|虐死你')
import difflib
def fuzzy_contained(q,m):
    for k in (m-1,m,m+1):
        for p in A.get(k,[]):
            if q in p: return True
            if len(p)>=len(q)*0.8:
                sm=difflib.SequenceMatcher(None,q,p,autojunk=False)
                if sum(b.size for b in sm.get_matching_blocks())>=0.85*len(q) or sm.ratio()>=0.75: return True
    return False
idxA=collections.defaultdict(list)
def rebuild():
    idxA.clear()
    for n,ps in A.items():
        for i,p in enumerate(ps): idxA[p].append((n,i))
rebuild()
def locate(m,j):
    q=B[m][j]
    if (m,j) in pairmap: return pairmap[(m,j)]
    for n,i in idxA.get(q,[]):
        if abs(n-m)<=2: return (n,i)
    return None
onlyB=[(m,j,q) for m,j,q in d['onlyB'] if 'adsbygoogle' not in q]
for m,j,q in onlyB:
    if 43<=m<=71 or len(q)<6: continue
    if NOTE.search(q): log.append(('SKIPNOTE',m,j,q[:70])); continue
    if fuzzy_contained(q,m): log.append(('CONTAINED',m,j,q[:50])); continue
    anchor=None
    for jj in range(j-1,-1,-1):
        anchor=locate(m,jj)
        if anchor: break
    if anchor:
        n,i=anchor; A[n].insert(i+1,q); rebuild(); log.append(('INS',m,j,'after',n,i,q[:70]))
    else:
        nxt=None
        for jj in range(j+1,len(B[m])):
            nxt=locate(m,jj)
            if nxt: break
        if nxt: n,i=nxt; A[n].insert(i,q); rebuild(); log.append(('INS',m,j,'before',n,i,q[:70]))
        else: A[m].append(q); rebuild(); log.append(('INS',m,j,'append',m,len(A[m])-1,q[:70]))
# --- step3 removals
JUNK=re.compile(r'^#+$|本站.*地址|^第\d+.*章|^>$|^\d+$')
NOTEA=re.compile(r'[一二三四五六七八九]更|更新|月票|爆发|兄弟|推荐|点滴|去痛片|百盟|底稿|12点|第一了|请稍等|新书榜|讨一会|多站稳|成绩|收藏！')
idxB=set(p for ps in B.values() for p in ps)
for n in sorted(A):
    if 43<=n<=71: continue
    newps=[]
    isnote=[(p not in idxB) and ((i==0 and len(p)<25) or bool(JUNK.search(p)) or (bool(NOTEA.search(p)) and len(p)<=130) or ('***' in p and len(p)<15)) for i,p in enumerate(A[n])]
    # chain: onlyA paragraphs adjacent to a note, short, are notes too
    changed=True
    while changed:
        changed=False
        for i,p in enumerate(A[n]):
            if not isnote[i] and p not in idxB and len(p)<=100 and ((i>0 and isnote[i-1]) or (i+1<len(A[n]) and isnote[i+1])) and (i==0 or i>=len(A[n])-4):
                isnote[i]=True; changed=True
    for i,p in enumerate(A[n]):
        if p in idxB: newps.append(p); continue
        if isnote[i]:
            log.append(('DEL',n,i,p[:80])); continue
        # fragment duplicated in adjacent paragraph after variant fix
        nb=[A[n][k] for k in (i-1,i+1) if 0<=k<len(A[n])]
        if len(p)>=6 and any(p in x and x!=p for x in nb): log.append(('DELFRAG',n,i,p[:60])); continue
        newps.append(p)
    A[n]=newps
c=collections.Counter(x[0] for x in log); print(c)
with open('apply51_log.txt','w',encoding='utf-8') as f:
    for x in log: f.write(' | '.join(map(str,x))+'\n')
if not DRY:
    bak=REPO+'/tmp/zh_aligned_pre_51'
    if not os.path.exists(bak): shutil.copytree(REPO+'/tmp/zh_aligned',bak)
    for n,(f,title) in Afile.items():
        open(f,'w',encoding='utf-8').write(title+'\n\n'+'\n\n'.join(A[n])+'\n')
    print('written',len(Afile))
stars=sum(p.count('***') for ps in A.values() for p in ps); print('*** remaining',stars)
