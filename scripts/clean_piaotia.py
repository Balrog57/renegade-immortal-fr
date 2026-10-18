"""Nettoie tmp/zh_piaotia -> tmp/zh_piaotia_clean (un paragraphe par ligne, séparés par une ligne vide)."""
import glob, pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8")
root = pathlib.Path(__file__).resolve().parents[1] / "tmp"
out = root / "zh_piaotia_clean"; out.mkdir(exist_ok=True)
JUNK = ("选择背景颜色", "选择字体大小", "返回顶部")
for f in sorted(glob.glob(str(root / "zh_piaotia" / "[0-9]*.txt"))):
    title, _, body = pathlib.Path(f).read_text(encoding="utf-8").partition("\n\n")
    paras = []
    for line in body.split("\n"):
        if any(j in line for j in JUNK):
            continue
        for p in re.split(r"[\xa0　 ]{2,}", line):
            p = p.strip()
            if p and not re.fullmatch(r"[－—\-=＝]+", p):
                paras.append(p)
    (out / pathlib.Path(f).name).write_text(title + "\n\n" + "\n\n".join(paras), encoding="utf-8")
