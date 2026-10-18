"""Télécharge tout Millionbook (version ancienne, numérotation WW) -> tmp/zh_million/NNNN_<id>.txt (chinois simplifié, un paragraphe par ligne vide)."""
import json, pathlib, re, sys, time
import requests
from bs4 import BeautifulSoup
from opencc import OpenCC

sys.stdout.reconfigure(encoding="utf-8")
t2s = OpenCC("t2s")
OUT = pathlib.Path(__file__).resolve().parents[1] / "tmp" / "zh_million"; OUT.mkdir(exist_ok=True)
H = {"User-Agent": "Mozilla/5.0"}
BASE = "https://millionbook.net/novels/2/2492/"
idx = requests.get(BASE + "index.html", headers=H, timeout=30).content.decode("big5hkscs", "replace")
items = [(a, t2s.convert(b)) for a, b in re.findall(r'<a href="(\d+)\.html"[^>]*>([^<]+)</a>', idx)]
(OUT / "_index.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
NOISE = ("龍騰世紀", "武俠修真", "文 /", "上一章", "本書目錄", "下一章", "章 節目錄", "龙腾世纪", "武侠修真")
for k, (cid, title) in enumerate(items, 1):
    m = re.match(r"第(\d+)章", title)
    f = OUT / f"{k:04d}_{cid}.txt"
    if f.exists() and f.stat().st_size > 100:
        continue
    for a in range(4):
        try:
            r = requests.get(f"{BASE}{cid}.html", headers=H, timeout=30)
            soup = BeautifulSoup(r.content.decode("big5hkscs", "replace"), "html.parser")
            for s in soup.select("script, style, h1, div.toplink, div.bottomlink, a"):
                s.decompose()
            lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip() and not any(x in l for x in NOISE)]
            if len(lines) < 3:
                raise ValueError("court")
            f.write_text(title + "\n\n" + "\n\n".join(t2s.convert(l) for l in lines), encoding="utf-8")
            break
        except Exception:
            time.sleep(2 * (a + 1))
    else:
        print("ECHEC", cid, title, flush=True)
    time.sleep(0.25)
    if k % 200 == 0:
        print(k, flush=True)
print("FIN", len(items))
