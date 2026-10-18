"""Chapitre 63 depuis Millionbook (réparé), nettoyage des notes d'auteur / bannières / titres internes, restitution des *** depuis Millionbook."""
import difflib, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from repair_million import variants, repair_par, best
sys.stdout.reconfigure(encoding="utf-8")
norm = lambda s: re.sub(r"[\W_]", "", s)
M = {}
for f in glob.glob("tmp/zh_million/[0-9]*.txt"):
    t = open(f, encoding="utf-8").read(); m = re.search(r"第(\d+)章", t.split("\n", 1)[0])
    if m: M.setdefault(int(m.group(1)), []).append(t)
def mparas(n):
    return [p.strip().replace("「", "“").replace("」", "”").replace("『", "‘").replace("』", "’").replace("！~！", "") for p in re.split(r"\n+", M[n][0])[1:] if p.strip()]
def path(n): return glob.glob(f"tmp/zh_aligned/{n:04d}_*.txt")[0]
def load(n):
    t = open(path(n), encoding="utf-8").read().rstrip("\n"); h, _, b = t.partition("\n\n")
    return h, [p for p in b.split("\n\n") if p.strip()]
def save(n, h, ps): open(path(n), "w", encoding="utf-8").write(h + "\n\n" + "\n\n".join(ps) + "\n")
inserted = json.load(open("tmp/million_fix/inserted.json", encoding="utf-8"))
# --- chapitre 63 : on prend Millionbook, réparé là où Piaotia correspond
h, Z = load(63)
out = []
for p in mparas(63):
    if re.fullmatch(r">|第\d+章\S{0,20}", p): continue
    b = best(p, Z)
    if b: out.append(repair_par(p, b))
    else: out.append(variants(p)); inserted.append([63, variants(p)])
save(63, h, out); print("63 reconstruit:", len(out), "paragraphes")
# --- nettoyage global
TITLE = re.compile(r"^第[\d、\-—～~ ]+章.{0,40}$")
KW = re.compile(r"月票|推荐票|求票|订阅|收藏|保底|打赏|票票|兄弟们|未完待续|更新|三更|二更|章节更多|冲榜|盟主")
ban = re.compile(r"\s*[（(]未完待续.*$", re.S)
stats = {"watermark": 0, "titre": 0, "note": 0}
for f in sorted(glob.glob("tmp/zh_aligned/*.txt")):
    n = int(os.path.basename(f)[:4]); h, ps = load(n); new = []
    for i, p in enumerate(ps):
        if "、qunaben、" in p: p = p.replace("、qunaben、", "").strip(); stats["watermark"] += 1
        p2 = ban.sub("", p).strip()
        if p2 != p: stats["note"] += 1
        p = p2
        if not p: continue
        if TITLE.match(p): stats["titre"] += 1; continue
        new.append(p)
    while len(new) > 1 and len(new[-1]) < 500 and KW.search(new[-1]) and "“" not in new[-1] and "”" not in new[-1]:
        print("note retirée", n, new[-1][:30]); new.pop(); stats["note"] += 1
    if new != ps: save(n, h, new)
print(stats)
json.dump(inserted, open("tmp/million_fix/inserted.json", "w", encoding="utf-8"), ensure_ascii=False)
