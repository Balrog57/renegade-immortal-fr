#!/usr/bin/env python3
"""Audit final du corpus FR : résidus CJK/anglais, variantes de noms (wiki Fandom),
doublons de paragraphes, ratios FR/EN et FR/ZH. Écrit tmp/audit_final.json.

Usage : python -X utf8 scripts/audit_final.py [chemin/wiki_names.json]
wiki_names.json : {titre_wiki: {"zh": "...", "pinyin": "..."}} (dump de xian-ni.fandom.com)."""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FR_GLOB = str(BASE / "src/content/chapters/*/*.md")
EN_GLOB = str(BASE / "tmp/en/*/*.txt")
ZH_GLOB = str(BASE / "tmp/zh_extract/chapters/*.txt")
OUT = BASE / "tmp/audit_final.json"
PRIORITY = [223, 204, 213, 170, 210, 207, 208, 573, 975, 819, 965, 826, 799, 793, 764, 955,
            183, 168, 181, 349, 619, 776, 800, 842, 378, 379, 583, 584, 588, 589, 657, 658]
EN_WORDS = re.compile(
    r"\b(the|and|with|from|that|this|his|her|their|would|could|which|was|were|had|have|into|"
    r"Senior Brother|Junior Brother)\b")
KNOWN = ["pieds", "milles", "Da Lou", "Da Luo", "Tout-Voyant", "Little White", "Domaine Ji",
         "Mer Sanguine", "Clear Water", "Secte de l'Éradication", "Transformation en Esprit"]


def num(p: str) -> int | None:
    m = re.match(r"(\d+)", os.path.basename(p))
    return int(m.group(1)) if m else None


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def body(path: str) -> str:
    return open(path, encoding="utf-8").read().split("---", 2)[-1]


def read_dir(pattern: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for p in glob.glob(pattern):
        n = num(p)
        if n:
            out[n] = out.get(n, "") + open(p, encoding="utf-8-sig", errors="ignore").read()
    return out


def main() -> None:
    names_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    wiki = json.load(open(names_path, encoding="utf-8")) if names_path else {}
    fr = {}
    for p in glob.glob(FR_GLOB):
        n = num(p)
        fr[n] = fr.get(n, "") + body(p)
    en, zh = read_dir(EN_GLOB), read_dir(ZH_GLOB)

    report: dict = {"residual_cjk": [], "residual_en": [], "dup_paragraphs": [], "ratio_en": [],
                    "ratio_zh": [], "known": {}, "names": {}, "priority": PRIORITY}
    known = defaultdict(list)
    for n, t in sorted(fr.items()):
        if re.search(r"[一-鿿]", t):
            report["residual_cjk"].append(n)
        hits = EN_WORDS.findall(t)
        if len(hits) >= 3:
            report["residual_en"].append([n, len(hits)])
        paras = [p.strip() for p in t.split("\n\n") if len(p.strip()) > 60]
        d = [k for k, v in Counter(paras).items() if v > 1]
        if d:
            report["dup_paragraphs"].append([n, len(d)])
        if n in en and len(en[n]) > 500:
            r = len(t) / len(en[n])
            if r < 0.95 or r > 1.5:
                report["ratio_en"].append([n, round(r, 2)])
        if n in zh and len(zh[n]) > 300:
            r = len(t) / len(zh[n])
            if r < 2.3 or r > 6:
                report["ratio_zh"].append([n, round(r, 2)])
        for k in KNOWN:
            if k in t:
                known[k].append(n)
    report["known"] = {k: len(v) for k, v in known.items()}

    # Variantes de noms : pour chaque entrée wiki avec pinyin, formes trouvées dans le corpus.
    alltext = "\n".join(fr.values())
    for title, v in wiki.items():
        py = strip_accents(v.get("pinyin", "")).strip().strip("}")
        words = [w for w in re.split(r"[\s\-]+", py) if w]
        if len(words) < 2 or len(words) > 4:
            continue
        pat = r"[\s\-]?".join(re.escape(w) for w in words)
        forms = Counter(m.group(0) for m in re.finditer(pat, alltext, re.I))
        if len(forms) > 1:
            report["names"][title] = dict(forms)
    json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in report.items()})


if __name__ == "__main__":
    main()
