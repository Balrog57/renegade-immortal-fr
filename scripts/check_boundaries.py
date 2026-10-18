"""Pour chaque frontière de chapitre k|k+1, compare le coût d'alignement ZH/EN avec la frontière actuelle et avec la meilleure frontière possible."""
import glob, json, os, re, sys, statistics
sys.path.insert(0, os.path.dirname(__file__))
from align_zh_en import align, phi_cost, en_paras, zh_paras
sys.stdout.reconfigure(encoding="utf-8")
zdir = sys.argv[1] if len(sys.argv) > 1 else "tmp/zh_aligned"
d = {x["chapter"]: x for x in json.load(open("tmp/alignment_zh_en_fr.json", encoding="utf-8"))}
enp = {os.path.basename(p): p for p in glob.glob("tmp/en/*/*.txt")}
TITLE = re.compile(r"^第[\d、\-—～~ ]+章.{0,40}$|^[（(]未完待续")
def zp(n):
    return [p for p in zh_paras(glob.glob(f"{zdir}/{n:04d}_*.txt")[0]) if not TITLE.match(p)]
def ep(n):
    e = []
    for fn in d[n]["en"]["files"]: e += en_paras(enp[fn])
    return [p for p in e if not re.match(r"^\d+\. ", p)]
RG = 3.27
out = {}
for k in range(1, 2088):
    Zk, Zn, Ek, En = zp(k), zp(k + 1), ep(k), ep(k + 1)
    zl = [len(p) for p in Zk + Zn]; el = [len(p) for p in Ek + En]
    cost, beads = align(zl, el, RG)
    # coût avec frontière actuelle forcée
    c1, b1 = align([len(p) for p in Zk], [len(p) for p in Ek], RG)
    c2, b2 = align([len(p) for p in Zn], [len(p) for p in En], RG)
    forced = c1 + c2
    # position ZH de la frontière EN dans l'alignement libre
    jb = len(Ek); pos = None
    for a, b, c, dd in beads:
        if c <= jb <= dd: pos = (a, b); break
    shift = None if pos is None else (pos[0] - len(Zk) if len(Zk) < pos[0] else (pos[1] - len(Zk) if len(Zk) > pos[1] else 0))
    out[k] = {"gain": round(forced - cost, 2), "shift": shift, "nZk": len(Zk), "beadZ": pos}
json.dump(out, open("tmp/boundaries_report.json", "w"))
bad = sorted([k for k, v in out.items() if v["gain"] > 6], key=lambda k: -out[k]["gain"])
print(len(bad)); print([(k, out[k]["gain"], out[k]["shift"]) for k in bad[:80]])
