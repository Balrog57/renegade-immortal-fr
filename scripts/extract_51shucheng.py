import re,os,json,glob,html,difflib
REPO='C:/Users/Marc/Documents/1G1R/_Programmation/renegade-immortal-fr'
idx=json.load(open('dl51/index.json',encoding='utf-8'))
CN={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'千':1000,'零':0}
def cn2int(s):
    if s.isdigit(): return int(s)
    tot=cur=0
    for ch in s:
        v=CN[ch]
        if v>=10: cur=(cur or 1)*v; tot+=cur; cur=0
        else: cur=v
    return tot+cur
altitles={int(os.path.basename(f)[:4]):os.path.basename(f)[5:-4] for f in glob.glob(REPO+'/tmp/zh_aligned/*.txt')}
rows=[]
for i,t in idx:
    t=html.unescape(t).strip()
    mm=re.match(r'第([0-9一二三四五六七八九十百千零]+)章[\s-]*(.*)',t)
    rows.append([i,t,cn2int(mm.group(1)),mm.group(2).strip()])
def body_of(i):
    h=open(f'dl51/{i}.html','rb').read().decode('utf-8','ignore')
    m=re.search(r'id="neirong"[^>]*>(.*?)</div>',h,re.S)
    b=html.unescape(re.sub(r'<[^>]+>','\n',m.group(1)))
    return [p.strip() for p in b.split('\n') if p.strip()]
nums=[r[2] for r in rows]
seenn=set()
for k,r in enumerate(rows):
    n=r[2]
    if r[1].startswith('第890章 怨殿副殿'): r[2]=899; nums[k]=899; print('renum',r[1],'-> 899'); continue
    if nums.count(n)>1:
        if n in seenn and n+1 not in nums: print('renum',r[1],'->',n+1); r[2]=n+1; nums[k]=n+1
        elif n not in seenn and n-1 not in nums: print('renum',r[1],'->',n-1); r[2]=n-1; nums[k]=n-1
    seenn.add(r[2])
out={}
for i,t,n,title in rows:
    paras=body_of(i)
    if n in out:
        if out[n][1]==paras: print('exact dup page dropped',t); continue
        print('MERGE a/b',n,t); out[n]=(out[n][0],out[n][1]+paras)
    else: out[n]=(title,paras)
os.makedirs('zh51',exist_ok=True)
for f in glob.glob('zh51/*.txt'): os.remove(f)
for n,(title,paras) in out.items():
    open(f'zh51/{n:04d}.txt','w',encoding='utf-8').write(f'第{n}章 {title}\n\n'+'\n\n'.join(paras))
print('written',len(out),'missing',sorted(set(range(1,2089))-set(out)))
