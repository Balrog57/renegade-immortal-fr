"""Liste, pour les chapitres FR modifiés (git diff HEAD), les modifications à vérifier à la main :
- perte de texte (suppression, ou remplacement qui retire plus de LOSS caractères),
- grosse insertion (plus de GAIN caractères ajoutés), avec test de doublon dans les chapitres voisins.
Usage : python -X utf8 scripts/check_lossy_hunks.py [--loss 60] [--gain 150] > tmp/relecture/verif.md"""
import argparse, difflib, glob, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--loss", type=int, default=60)
ap.add_argument("--gain", type=int, default=150)
a = ap.parse_args()


def paras(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def neighbours(n):
    out = []
    for k in (n - 1, n + 1):
        for f in glob.glob(str(ROOT / f"src/content/chapters/*/{k:04d}-*.md")):
            out += paras(pathlib.Path(f).read_text(encoding="utf-8").split("---", 2)[2])
    return out


files = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "src/content/chapters"], cwd=ROOT, capture_output=True, text=True).stdout.split()
nloss = ngain = 0
for f in sorted(files):
    n = int(re.search(r"/(\d{4})-", f).group(1))
    old = subprocess.run(["git", "show", "HEAD:" + f], cwd=ROOT, capture_output=True, encoding="utf-8").stdout.replace("\r\n", "\n").split("\n")
    new = (ROOT / f).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    nb = None
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        lo = " // ".join(l for l in old[i1:i2] if l.strip())
        ln = " // ".join(l for l in new[j1:j2] if l.strip())
        if tag == "delete" or (tag == "replace" and len(lo) - len(ln) > a.loss):
            nloss += 1
            print(f"\n### PERTE ch. {n} ({tag}, -{len(lo)} +{len(ln)})\nAVANT : {lo}\nAPRÈS : {ln}")
        elif len(ln) - len(lo) > a.gain:
            if nb is None:
                nb = neighbours(n)
            added = [p for p in paras("\n\n".join(new[j1:j2])) if p not in old]
            dup = [p[:80] for p in added if any(p[:60] in q for q in nb)]
            ngain += 1
            print(f"\n### INSERTION ch. {n} (+{len(ln) - len(lo)}){' DOUBLON VOISIN : ' + str(dup) if dup else ''}\nAVANT : {lo[:300]}\nAPRÈS : {ln[:600]}")
print(f"\n\n{len(files)} fichiers, {nloss} pertes, {ngain} grosses insertions")
