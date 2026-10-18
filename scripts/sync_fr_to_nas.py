"""Recopie sur le NAS (dossier traduction) les chapitres FR modifiés du dépôt.
Usage : python -X utf8 scripts/sync_fr_to_nas.py [NNNN ...]   (défaut : fichiers modifiés selon git)
Format NAS : "Chapitre N - Titre", ligne vide, corps du markdown ; BOM et fin de ligne (CRLF/LF) conservés par fichier.
Chapitres coupés en deux fichiers a/b sur le NAS : coupe au même paragraphe que le fichier a existant."""
import glob, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAS = pathlib.Path(r"\\192.168.1.150\Media\Livres\EBOOK\Renegade Immortal\traduction")


def md_parts(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    fm, body = text.split("---", 2)[1:]
    n = int(re.search(r"^n:\s*(\d+)", fm, re.M).group(1))
    title = re.search(r"^title:\s*(.+)$", fm, re.M).group(1).strip().strip('"')
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return n, title, paras


def write_like(dest, text):
    raw = dest.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    eol = "\r\n" if b"\r\n" in raw else "\n"
    out = text.replace("\n", eol)
    dest.write_bytes((b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))


def sync(md):
    n, title, paras = md_parts(md)
    targets = sorted(NAS.glob(f"Book */{n:04d}* - *.txt"))
    if not targets:
        print(f"[!] {n}: aucun fichier NAS"); return
    if len(targets) == 1:
        write_like(targets[0], f"Chapitre {n} - {title}\n\n" + "\n\n".join(paras) + "\n")
        print(f"ok {n}"); return
    # a/b : dernier paragraphe du fichier a existant = point de coupe
    old_a = [p.strip() for p in re.split(r"\n\s*\n", targets[0].read_text(encoding="utf-8-sig")) if p.strip()]
    cut = None
    for cand in reversed(old_a[1:]):
        if cand in paras: cut = paras.index(cand) + 1; break
    if cut is None:
        print(f"[!] {n}: point de coupe a/b introuvable, non synchronisé"); return
    heads = [re.split(r"\n\s*\n", t.read_text(encoding="utf-8-sig"))[0].strip() for t in targets]
    write_like(targets[0], heads[0] + "\n\n" + "\n\n".join(paras[:cut]) + "\n")
    write_like(targets[1], heads[1] + "\n\n" + "\n\n".join(paras[cut:]) + "\n")
    print(f"ok {n} (a/b, coupe après le paragraphe {cut})")


if __name__ == "__main__":
    nums = [int(a) for a in sys.argv[1:]]
    if nums:
        files = [pathlib.Path(glob.glob(str(ROOT / f"src/content/chapters/*/{n:04d}-*.md"))[0]) for n in nums]
    else:
        out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "src/content/chapters"], cwd=ROOT, capture_output=True, text=True).stdout
        files = [ROOT / p for p in out.split()]
    for f in files: sync(f)
    print(len(files), "fichiers traités")
