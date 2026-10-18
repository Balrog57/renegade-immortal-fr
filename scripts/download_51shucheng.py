import re, sys, os, time, json, urllib.request, concurrent.futures as cf
SP=os.path.dirname(os.path.abspath(__file__))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
h=open(SP+'/probe/7697db8a.html','rb').read().decode('utf-8','ignore')
links=re.findall(r'href="(https?://www\.51shucheng\.net/xuanhuan/xianni/(\d+)\.html)"[^>]*>([^<]+)</a>',h)
seen={}; order=[]
for u,i,t in links:
    t=t.strip()
    if t in('开始阅读','开始阅读 &rsaquo;') or not t: continue
    if i not in seen: seen[i]=t; order.append(i)
json.dump([(i,seen[i]) for i in order],open(SP+'/dl51/index.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('chapters',len(order))
def get(i):
    out=f'{SP}/dl51/{i}.html'
    if os.path.exists(out) and os.path.getsize(out)>3000: return i,'cached'
    for a in range(4):
        try:
            r=urllib.request.Request(f'https://www.51shucheng.net/xuanhuan/xianni/{i}.html',headers={'User-Agent':UA})
            b=urllib.request.urlopen(r,timeout=30).read()
            if b'id="neirong"' in b:
                open(out,'wb').write(b); return i,'ok'
        except Exception as e: err=e
        time.sleep(2+a*3)
    return i,'FAIL'
with cf.ThreadPoolExecutor(6) as ex:
    n=0
    for i,s in ex.map(get,order):
        n+=1
        if s=='FAIL' or n%200==0: print(n,i,s,flush=True)
print('done')
