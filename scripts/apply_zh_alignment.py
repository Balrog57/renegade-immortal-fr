"""Applique les frontières trouvées (tmp/zh_align_res/win_*.json) à tmp/zh_final -> tmp/zh_aligned (2088 fichiers, numérotation WW)."""
import glob, json, pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[1] / "tmp"
SRC, OUT = ROOT / "zh_final", ROOT / "zh_aligned"
OUT.mkdir(exist_ok=True)
norm = lambda s: re.sub(r"[\W_]", "", s)
TITLE = re.compile(r"^第[\d、\-—～~ ]+章.{0,40}$")
BANNER = re.compile(r"^[（(]未完待续|请登陆|章节更多|支持正版")
NOTE_KW = re.compile(r"月票|推荐票|求票|订阅|收藏|三更|二更|更新|未完待续|保底|打赏|冲榜|盟主|票票|章节更多")

F = {}   # n -> (head, [paras])
for f in sorted(glob.glob(str(SRC / "*.txt"))):
    n = int(re.match(r"(\d{4})_", pathlib.Path(f).name).group(1))
    t = pathlib.Path(f).read_text(encoding="utf-8").strip("\n").split("\n\n")
    ps = [p.strip() for p in t[1:] if p.strip()]
    if n == 632:  # fichier à une seule 'ligne' géante : les agents ont indexé par lignes internes
        ps = [l.strip() for p in ps for l in p.splitlines() if l.strip()]
    F[n] = (t[0].strip(), ps)
# stream global : [(file, idx(1-based), texte)]
stream = [(n, i, p) for n in sorted(F) for i, p in enumerate(F[n][1], 1)]
pos = {(n, i): k for k, (n, i, _) in enumerate(stream)}

def at(label, end=False):
    if label.startswith("ALL:"):
        n = int(label[4:]); return pos[(n, len(F[n][1]) if end else 1)]
    n, i = label.split(".")
    n = int(n)
    i = len(F[n][1]) if i == "last" else int(i)
    return pos[(n, min(i, len(F[n][1])))]

def trailing_notes(ps):
    ps = list(ps)
    while ps and len(ps[-1]) < 400 and NOTE_KW.search(ps[-1]) and "“" not in ps[-1] and "”" not in ps[-1]:
        ps.pop()
    return ps

new, log = {}, []
for f in sorted(glob.glob(str(ROOT / "zh_align_res" / "win_*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    excl = {tuple(map(int, x.split("."))) for x in d.get("excl", [])}
    for ch in d["chapters"]:
        paras, head_src = [], None
        for s, e in ch["ranges"]:
            for k in range(at(s), at(e, True) + 1):
                n, i, p = stream[k]
                if (n, i) in excl or TITLE.match(p) or BANNER.match(p):
                    continue
                if head_src is None:
                    head_src = n
                paras.append(p)
        new[ch["en"]] = (head_src, paras)
    if "extra_prev" in d:
        e = d["extra_prev"]
        add = [stream[k][2] for k in range(at(e["start"]), at(e["end"], True) + 1) if not TITLE.match(stream[k][2])]
        new.setdefault(("append", e["to"]), []).extend(add)
    if "extra_next" in d:
        e = d["extra_next"]
        add = [stream[k][2] for k in range(at(e["start"]), at(e["end"], True) + 1) if not TITLE.match(stream[k][2])]
        new.setdefault(("prepend", e["to"]), []).extend(add)

def title_of(head):
    return re.sub(r"^第[\d、\-—～~ ]+章\s*", "", head).strip() or "无题"

nfix = 0
for n in sorted(F):
    head, ps = F[n]
    src = n
    if n in new:
        hs, ps = new[n]; src = hs; head = F[hs][0]; nfix += 1
    if ("append", n) in new:
        ps = ps + new[("append", n)]
    if ("prepend", n) in new:
        have = {norm(p) for p in ps}
        ps = [p for p in new[("prepend", n)] if norm(p) not in have] + ps
    ps = trailing_notes(ps)
    t = title_of(head)
    body = f"第{n}章 {t}\n\n" + "\n\n".join(ps) + "\n"
    safe = re.sub(r'[\/:*?"<>|]', "", t)
    (OUT / f"{n:04d}_{safe}.txt").write_text(body, encoding="utf-8")
print("chapitres réalignés:", nfix, "| fichiers:", len(list(OUT.glob("*.txt"))))
