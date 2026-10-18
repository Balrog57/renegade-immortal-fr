"""Complète tmp/zh_million en parallèle (8 threads) ; saute les fichiers déjà présents."""
import json, pathlib, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from opencc import OpenCC

sys.stdout.reconfigure(encoding="utf-8")
OUT = pathlib.Path(__file__).resolve().parents[1] / "tmp" / "zh_million"
items = json.loads((OUT / "_index.json").read_text(encoding="utf-8"))
H = {"User-Agent": "Mozilla/5.0"}
BASE = "https://millionbook.net/novels/2/2492/"
NOISE = ("龍騰世紀", "武俠修真", "文 /", "上一章", "本書目錄", "下一章", "章 節目錄", "龙腾世纪", "武侠修真")

def work(arg):
    k, (cid, title) = arg
    f = OUT / f"{k:04d}_{cid}.txt"
    if f.exists() and f.stat().st_size > 100:
        return
    t2s = OpenCC("t2s")
    for a in range(5):
        try:
            r = requests.get(f"{BASE}{cid}.html", headers=H, timeout=30)
            soup = BeautifulSoup(r.content.decode("big5hkscs", "replace"), "html.parser")
            for s in soup.select("script, style, h1, div.toplink, div.bottomlink, a"):
                s.decompose()
            lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip() and not any(x in l for x in NOISE)]
            if len(lines) < 3:
                raise ValueError("court")
            f.write_text(title + "\n\n" + "\n\n".join(t2s.convert(l) for l in lines), encoding="utf-8")
            return
        except Exception:
            time.sleep(2 * (a + 1))
    print("ECHEC", cid, title, flush=True)

with ThreadPoolExecutor(8) as ex:
    list(ex.map(work, list(enumerate(items, 1))[::-1]))
print("FIN")
