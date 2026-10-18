"""Déplace les paragraphes entre chapitres voisins pour minimiser le coût d'alignement ZH/EN (décalage -12..+12 paragraphes)."""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from align_zh_en import align, en_paras, zh_paras
sys.stdout.reconfigure(encoding="utf-8")
zdir = "tmp/zh_aligned"
d = {x["chapter"]: x for x in json.load(open("tmp/alignment_zh_en_fr.json", encoding="utf-8"))}
enp = {os.path.basename(p): p for p in glob.glob("tmp/en/*/*.txt")}
TITLE = re.compile(r"^第[\d、\-—～~ ]+章.{0,40}$|^[（(]未完待续")
SKIP = {235}
rep = json.load(open("tmp/boundaries_report.json"))
cands = [int(x) for x in sys.argv[1:]] or sorted(int(k) for k, v in rep.items() if v["gain"] > 6 and int(k) not in SKIP)
def path(n): return glob.glob(f"{zdir}/{n:04d}_*.txt")[0]
def load(n):
    t = open(path(n), encoding="utf-8").read().rstrip("\n")
    head, _, body = t.partition("\n\n")
    return head, [p for p in body.split("\n\n") if p.strip()]
def ep(n):
    e = []
    for fn in d[n]["en"]["files"]: e += en_paras(enp[fn])
    return [p for p in e if not re.match(r"^\d+\. ", p)]
def cost(zp, en): return align([len(p) for p in zp], [len(p) for p in en], 3.27)[0]
for k in cands:
    hk, Zk = load(k); hn, Zn = load(k + 1)
    Zk = [p for p in Zk if not TITLE.match(p)]; Zn0 = [p for p in Zn if not TITLE.match(p)]
    Ek, En = ep(k), ep(k + 1)
    best = (cost(Zk, Ek) + cost(Zn0, En), 0)
    allz = Zk + Zn0
    for s in range(-12, 13):
        if s == 0: continue
        cut = len(Zk) + s
        if cut < 3 or cut > len(allz) - 3: continue
        c = cost(allz[:cut], Ek) + cost(allz[cut:], En)
        if c < best[0] - 0.01 and c < best[0]: best = (c, s)
    base = cost(Zk, Ek) + cost(Zn0, En)
    if best[1] != 0 and base - best[0] > 6:
        cut = len(Zk) + best[1]
        for n, h, ps in ((k, hk, allz[:cut]), (k + 1, hn, allz[cut:])):
            open(path(n), "w", encoding="utf-8").write(h + "\n\n" + "\n\n".join(ps) + "\n")
        print(f"{k}|{k+1}: décalage {best[1]:+d} paragraphes (gain {base-best[0]:.1f})")
    else:
        print(f"{k}|{k+1}: laissé (meilleur {best[1]:+d}, gain {base-best[0]:.1f})")
