"""Construit tmp/zh_final/ : texte chinois propre (Piaotia) réparti selon la numérotation de tmp/zh_extract (= Wuxiaworld).
Chaque paragraphe Piaotia va au fichier zh_extract qui le contient (le plus recoupé par sa page en cas d'ambiguïté) ;
un paragraphe absent de tout fichier (texte révisé) suit le fichier du paragraphe précédent."""
import collections, glob, json, pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[1] / "tmp"
OUT = ROOT / "zh_final"; OUT.mkdir(exist_ok=True)
norm = lambda s: re.sub(r"[\W_]", "", s)
KEEP_OLD = set(range(52, 62)) | set(range(64, 71))  # chapitres 52-70 : version non abrégée déjà dans zh_extract

files, owners = {}, collections.defaultdict(set)
for f in sorted(glob.glob(str(ROOT / "zh_extract" / "chapters" / "*.txt"))):
    p = pathlib.Path(f); n = int(re.match(r"(\d{4})_", p.name).group(1))
    t = p.read_text(encoding="utf-8"); head, _, body = t.partition("\n")
    files[n] = (p.name, head.strip(), t)
    for q in re.split(r"\n+", body):
        if len(norm(q)) >= 12:
            owners[norm(q)].add(n)

pages = []
for f in sorted(glob.glob(str(ROOT / "zh_piaotia_clean" / "[0-9]*.txt"))):
    i = int(re.match(r"(\d{4})_", pathlib.Path(f).name).group(1))
    title, _, body = pathlib.Path(f).read_text(encoding="utf-8").partition("\n\n")
    pages.append((i, title, body.split("\n\n")))

tkey = lambda t: re.sub(r"[（(][^）)]*[）)]|^第?[\d一二三四五六七八九十百零\-、]+章?|\W", "", t)
# Piaotia contient des pages dupliquées par erreur : page voisine (<=2) -> on garde la première ; page lointaine -> on garde la dernière
where = collections.defaultdict(list)
for i, _t, ps in pages:
    for k, q in enumerate(ps):
        if len(norm(q)) >= 20:
            where[norm(q)].append(i)
drop = set()
for i, _t, ps in pages:
    for k, q in enumerate(ps):
        w = where.get(norm(q), [])
        if len(w) > 1 and ((min(w) < i and i - max(x for x in w if x < i) <= 2) or (max(w) > i and min(x for x in w if x > i) - i > 2)):
            drop.add((i, k))
out = collections.defaultdict(list); unmatched_pages = []; last = 1
for i, title, ps in pages:
    if "章" not in title:
        continue
    mnum = re.match(r"第(\d+)章(?![、\d-])", title)
    multi = bool(re.match(r"第\d+[章、-]*[\d、-]", title)) and not mnum
    if mnum and tkey(title):
        cand = [n for n, v in files.items() if n not in KEEP_OLD and tkey(v[1]) == tkey(title) and abs(n - int(mnum.group(1))) <= 15]
        if cand:
            tgt = min(cand, key=lambda n: abs(n - int(mnum.group(1))))
            out[tgt].extend(q for k, q in enumerate(ps) if (i, k) not in drop)
            last = tgt; continue
    score = collections.Counter()
    for q in ps:
        for n in owners.get(norm(q), ()):
            score[n] += 1
    if sum(score.values()) < 3:
        unmatched_pages.append((i, title))
        key = tkey(title)
        tgt = next((n for n, v in files.items() if n not in KEEP_OLD and tkey(v[1]) == key and key), None)
        if tgt is None:
            tgt = last   # sans équivalent : rattaché au fichier précédent (à relire)
        out[tgt].extend(q for k, q in enumerate(ps) if (i, k) not in drop); continue
    prev = score.most_common(1)[0][0]
    for k, q in enumerate(ps):
        if (i, k) in drop:
            continue
        c = owners.get(norm(q)) if len(norm(q)) >= 12 else None
        if c:
            prev = max(c, key=lambda n: (score[n], -n))
        out[prev].append(q); last = prev

kept = []
for n, (fname, head, old) in files.items():
    cl = lambda x: len(norm(x))
    if n in KEEP_OLD or not out.get(n) or cl("".join(out[n])) < 0.5 * cl(old):
        kept.append(n); (OUT / fname).write_text(old, encoding="utf-8"); continue
    (OUT / fname).write_text(head + "\n\n" + "\n\n".join(out[n]) + "\n", encoding="utf-8")
json.dump({"kept_old": kept, "unmatched_pages": unmatched_pages}, open(ROOT / "zh_final_report.json", "w", encoding="utf-8"), ensure_ascii=False)
print("anciens gardés:", kept); print("pages sans correspondance:", len(unmatched_pages))
for x in unmatched_pages: print(x)
