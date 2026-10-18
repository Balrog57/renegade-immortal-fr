"""Répare un chapitre Millionbook (caractères 在 最 更 新 尽 索 搜 咔 perdus par le site, 著/籐/舖 variantes) en s'appuyant sur Piaotia quand le paragraphe correspond."""
import difflib, re
LOST = set("在最更新尽索搜咔")
VAR = {"著": "着", "籐": "藤", "舖": "铺", "瞇": "眯", "礡": "磅"}

def variants(s):
    return "".join(VAR.get(c, c) for c in s)

def repair_par(m, p):
    """Réinsère dans m (Million) les caractères perdus, d'après le paragraphe p (Piaotia)."""
    m = variants(m)
    sm = difflib.SequenceMatcher(None, m, p, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.append(m[i1:i2])
        elif op == "insert" and set(p[j1:j2]) <= LOST:
            out.append(p[j1:j2])
        elif op == "insert":
            pass
        else:
            out.append(m[i1:i2])
    return "".join(out)

def best(m, ps):
    b, br = None, 0
    for p in ps:
        r = difflib.SequenceMatcher(None, re.sub(r"\W", "", variants(m)), re.sub(r"\W", "", p), autojunk=False).quick_ratio()
        if r > br:
            b, br = p, r
    if b and difflib.SequenceMatcher(None, re.sub(r"\W", "", variants(m)), re.sub(r"\W", "", b), autojunk=False).ratio() >= 0.75:
        return b
    return None
