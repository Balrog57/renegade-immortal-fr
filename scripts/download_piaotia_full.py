"""Télécharge tout le texte chinois brut de Piaotia (1 fichier par page, ordre du sommaire) dans tmp/zh_piaotia/."""
import pathlib, re, sys, time, json
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://www.piaotia.com/html/0/54/"
OUT = pathlib.Path(__file__).resolve().parents[1] / "tmp" / "zh_piaotia"
OUT.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
NOISE = ("PT文学", "加入书架", "返回目录", "快捷键", "投推荐票", "上一章", "下一章", "点此举报", "我的藏书架", "重要声明", "All rights reserved")

idx = requests.get(BASE + "index.html", headers=H, timeout=30).content.decode("gbk", "replace")
pages = [(a, t) for a, t in re.findall(r'<li><a href="(\d+\.html)">([^<]+)</a>', idx) if t.startswith("第") or "章" in t]
(OUT / "_index.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")

for i, (href, title) in enumerate(pages, 1):
    f = OUT / f"{i:04d}_{href[:-5]}.txt"
    if f.exists() and f.stat().st_size > 200:
        continue
    for attempt in range(4):
        try:
            r = requests.get(BASE + href, headers=H, timeout=30)
            soup = BeautifulSoup(r.content.decode("gbk", "replace"), "html.parser")
            for s in soup.select("script, style, div.toplink, div.bottomlink, center, table, h1, div#Commenddiv"):
                s.decompose()
            lines = [l.strip() for l in soup.get_text().splitlines() if l.strip() and not any(k in l for k in NOISE)]
            if len(lines) < 3:
                raise ValueError("trop court")
            f.write_text(title + "\n\n" + "\n\n".join(lines), encoding="utf-8")
            break
        except Exception as e:
            time.sleep(2 * (attempt + 1))
    else:
        print("ECHEC", href, title)
    time.sleep(0.3)
    if i % 100 == 0:
        print(i, flush=True)
print("FIN", len(pages))
