"""Insertions de paragraphes manquants depuis Millionbook, suppression des notes d'auteur/bannières, restitution des mots censurés (***)."""
import difflib, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from repair_million import variants, repair_par
sys.stdout.reconfigure(encoding="utf-8")
norm = lambda s: re.sub(r"[\W_]", "", s)
M = {}
for f in glob.glob("tmp/zh_million/[0-9]*.txt"):
    t = open(f, encoding="utf-8").read(); m = re.search(r"第(\d+)章", t.split("\n", 1)[0])
    if m: M.setdefault(int(m.group(1)), []).append(t)
def mparas(n):
    t = M[n][0]
    return [p.strip().replace("「", "“").replace("」", "”").replace("『", "‘").replace("』", "’").replace("！~！", "") for p in re.split(r"\n+", t)[1:] if p.strip()]
def path(n): return glob.glob(f"tmp/zh_aligned/{n:04d}_*.txt")[0]
def load(n):
    t = open(path(n), encoding="utf-8").read().rstrip("\n"); h, _, b = t.partition("\n\n")
    return h, [p for p in b.split("\n\n") if p.strip()]
def save(n, h, ps): open(path(n), "w", encoding="utf-8").write(h + "\n\n" + "\n\n".join(ps) + "\n")
def sim(a, b): return difflib.SequenceMatcher(None, norm(variants(a)), norm(b), autojunk=False).ratio()
def best_idx(text, ps):
    return max(range(len(ps)), key=lambda i: sim(text, ps[i]))
inserted = []   # (n, texte) à restaurer ensuite (caractères perdus 在 最…)
def insert_after(n, prev_m, m_list):
    mp = mparas(n); h, ps = load(n)
    i = best_idx(mp[prev_m - 1], ps)
    new = [variants(mp[k - 1]) for k in m_list]
    ps[i + 1:i + 1] = new; save(n, h, ps); inserted.extend((n, t) for t in new)
    print(f"{n}: +{len(new)} paragraphe(s) après le paragraphe {i+1}")
def append_end(n, m_list, fix_prev_dup=True):
    mp = mparas(n); h, ps = load(n); new = [variants(mp[k - 1]) for k in m_list]
    ps += new; save(n, h, ps); inserted.extend((n, t) for t in new); print(f"{n}: +{len(new)} en fin")
insert_after(494, 49, [50, 51, 52, 53])
insert_after(563, 26, [27]); insert_after(563, 28, [29])
insert_after(97, 42, [43, 44])
insert_after(850, 23, [24])
insert_after(994, 45, [46])
insert_after(1418, 5, [6])
append_end(926, [54]); append_end(986, [58]); append_end(1090, [60])
# 1451 : phrase finale manquante (fin du paragraphe M1451.14)
mp = mparas(1451); h, ps = load(1451)
tail = mp[13][mp[13].rfind("「") if "「" in mp[13] else mp[13].rfind("“"):] if False else None
m14 = mp[13]; k = m14.find("以道丹饲养天道"); sentence = variants(m14[k:]) if k >= 0 else None
if sentence:
    i = best_idx(m14[:k] if k > 0 else m14, ps); ps.insert(i + 1, sentence); save(1451, h, ps); inserted.append((1451, sentence)); print("1451: phrase insérée", sentence[:30])
json.dump(inserted, open("tmp/million_fix/inserted.json", "w", encoding="utf-8"), ensure_ascii=False)
