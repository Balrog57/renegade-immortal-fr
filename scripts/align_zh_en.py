"""Alignement paragraphe à paragraphe ZH/EN (Gale-Church simplifié) ; mesure la part de texte sans équivalent de chaque côté.
Usage : python scripts/align_zh_en.py [dossier_zh=tmp/zh_aligned] -> tmp/align_report_<dossier>.json"""
import glob, json, math, os, re, sys, statistics
sys.stdout.reconfigure(encoding="utf-8")
R = 3.0  # caractères anglais attendus par caractère chinois (ajusté ci-dessous)
def phi_cost(e, c, r):
    if c == 0 and e == 0: return 0.0
    mean = c * r
    var = max(c, 1) * r * 6.8
    z = abs(e - mean) / math.sqrt(var)
    p = math.erfc(z / math.sqrt(2))
    return -math.log(max(p, 1e-12))
PEN = {(1,1):0.12,(1,0):5.5,(0,1):5.5,(2,1):2.4,(1,2):2.4,(2,2):4.5,(3,1):6.0,(1,3):6.0,(3,2):6.0,(2,3):6.0}
def align(z, e, r):
    n, m = len(z), len(e)
    INF = 1e18
    cz = [0]; ce = [0]
    for x in z: cz.append(cz[-1] + x)
    for x in e: ce.append(ce[-1] + x)
    D = [[INF] * (m + 1) for _ in range(n + 1)]; B = [[None] * (m + 1) for _ in range(n + 1)]
    D[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            if D[i][j] >= INF: continue
            for (a, b), pen in PEN.items():
                ii, jj = i + a, j + b
                if ii > n or jj > m: continue
                c = D[i][j] + pen + phi_cost(ce[jj] - ce[j], cz[ii] - cz[i], r) + (0 if (a and b) else 0)
                if c < D[ii][jj]: D[ii][jj] = c; B[ii][jj] = (a, b)
    i, j, beads = n, m, []
    while i or j:
        a, b = B[i][j]; beads.append((i - a, i, j - b, j)); i -= a; j -= b
    return D[n][m], beads[::-1]
def en_paras(path):
    t = open(path, encoding="utf-8", errors="replace").read().replace("\r", "")
    ps = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    while ps and re.match(r"^Chapter \d+", ps[0]): ps = ps[1:]
    return ps
def zh_paras(path):
    t = open(path, encoding="utf-8-sig").read().replace("\r", "")
    return [p.strip() for p in re.split(r"\n+", t)[1:] if p.strip()]
if __name__ == "__main__":
    zdir = sys.argv[1] if len(sys.argv) > 1 else "tmp/zh_aligned"
    d = {x["chapter"]: x for x in json.load(open("tmp/alignment_zh_en_fr.json", encoding="utf-8"))}
    enp = {os.path.basename(p): p for p in glob.glob("tmp/en/*/*.txt")}
    RG = statistics.median(sum(len(p) for p in en_paras(enp[d[k]['en']['files'][0]])) / max(sum(len(p) for p in zh_paras(glob.glob(f'{zdir}/{k:04d}_*.txt')[0])), 1) for k in range(100, 2000, 20))
    print('ratio global', RG)
    out = {}
    for n in range(1, 2089):
        zf = glob.glob(f"{zdir}/{n:04d}_*.txt")
        if not zf: continue
        z = zh_paras(zf[0]); e = []
        for fn in d[n]["en"]["files"]: e += en_paras(enp[fn])
        zl = [len(p) for p in z]; el = [len(p) for p in e]
        r = RG
        cost, beads = align(zl, el, r)
        uz = sum(zl[a:b] and sum(zl[a:b]) for a, b, c, dd in beads if c == dd)  # ZH sans EN
        ue = sum(sum(el[c:dd]) for a, b, c, dd in beads if a == b)             # EN sans ZH
        badz = sum(sum(zl[a:b]) for a, b, c, dd in beads if phi_cost(sum(el[c:dd]), sum(zl[a:b]), r) > 9)
        bade = sum(sum(el[c:dd]) for a, b, c, dd in beads if phi_cost(sum(el[c:dd]), sum(zl[a:b]), r) > 9)
        out[n] = {"bad_zh": round(badz / max(sum(zl), 1), 3), "bad_en": round(bade / max(sum(el), 1), 3), "cost_par": round(cost / max(len(z), len(e)), 3), "zh_sans_en": round(uz / max(sum(zl), 1), 3), "en_sans_zh": round(ue / max(sum(el), 1), 3), "nz": len(z), "ne": len(e)}
    json.dump(out, open(f"tmp/align_report_{os.path.basename(zdir.rstrip('/'))}.json", "w"))
    bad = sorted(out, key=lambda k: -(out[k]["zh_sans_en"] + out[k]["en_sans_zh"]))
    print("médiane cost", statistics.median(v["cost_par"] for v in out.values()))
    print("pire 40:", [(k, out[k]["zh_sans_en"], out[k]["en_sans_zh"]) for k in bad[:40]])
    print("> 5% de texte sans équivalent:", sum(1 for v in out.values() if v["zh_sans_en"] + v["en_sans_zh"] > 0.05), "| > 10%:", sum(1 for v in out.values() if v["zh_sans_en"] + v["en_sans_zh"] > 0.10))
