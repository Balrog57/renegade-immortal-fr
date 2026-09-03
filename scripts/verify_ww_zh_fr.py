#!/usr/bin/env python3
"""Inventory WW + ZH + FR and report leftover English + rank alignment sample."""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
CH = ROOT / "src" / "content" / "chapters"
ZH_DIR = ROOT / "tmp" / "zh_extract" / "chapters"
WW_ROOT = pathlib.Path(
    r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\wuxiaworld"
)
OUT = ROOT / "tmp" / "zh_extract" / "ww_zh_fr_report.json"

WW_CH_RE = re.compile(r"^(\d{4})\s*-")
FR_CH_RE = re.compile(r"^(\d{4})-")
ZH_CH_RE = re.compile(r"^(\d{4})_")

LEFTOVER = [
    "Hunchback",
    "Moongazer",
    r"\bGreed\b",
    "Nirvana Scryer",
    "Nirvana Cleanser",
    "Nirvana Shatterer",
    "Nirvana Void",
    "Soul Formation",
    "Nascent Soul",
    "Divine Sense",
    "Spirit Severing",
    "Soul Transformation",
    "Core Formation",
    "Foundation Establishment",
    "Qi Condensation",
    "Heaven Defying Bead",
    "Devil Master Nine Heavens",
    "Great Desolation",
    "Ashen Pine",
    "Cloud Soul",
    "Everlasting Sect",
    "Joss Flame",
    "flying sword",
    "Séparation de l'Esprit",
    "All-Seer",
    "Red Butterfly",
    "Qin Lin",
]

RANK_PAIRS = [
    ("化神", "Formation de l'Âme", "Spirit Severing"),
    ("婴变", "Transformation de l'Âme", "Soul Transformation"),
    ("元婴", "Âme Naissante", "Nascent Soul"),
    ("结丹", "Formation du Noyau", "Core Formation"),
    ("窥涅", "Scruteur du Nirvana", "Nirvana Scryer"),
    ("净涅", "Purificateur du Nirvana", "Nirvana Cleanser"),
    ("碎涅", "Briseur du Nirvana", "Nirvana Shatterer"),
    ("天运子", "Omniscient", "All-Seer"),
    ("红蝶", "Papillon Rouge", "Red Butterfly"),
    ("贪狼", "Cupidité", "Greed"),
    ("望月", "yeux de lune", "Moongazer"),
]


def body_of(md: str) -> str:
    if md.startswith("---"):
        parts = md.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return md


def index_ww() -> dict[int, pathlib.Path]:
    out: dict[int, pathlib.Path] = {}
    if not WW_ROOT.exists():
        return out
    for p in WW_ROOT.rglob("*.txt"):
        m = WW_CH_RE.match(p.name)
        if m:
            out[int(m.group(1))] = p
    return out


def index_fr() -> dict[int, pathlib.Path]:
    out: dict[int, pathlib.Path] = {}
    for p in CH.rglob("*.md"):
        m = FR_CH_RE.match(p.name)
        if m:
            out[int(m.group(1))] = p
    return out


def index_zh() -> dict[int, pathlib.Path]:
    out: dict[int, pathlib.Path] = {}
    if not ZH_DIR.exists():
        return out
    for p in ZH_DIR.glob("*.txt"):
        m = ZH_CH_RE.match(p.name)
        if m:
            out[int(m.group(1))] = p
    return out


def leftover_counts(fr: dict[int, pathlib.Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for term in LEFTOVER:
        pat = re.compile(term) if term.startswith(r"\b") else re.compile(re.escape(term))
        n = 0
        for p in fr.values():
            n += len(pat.findall(body_of(p.read_text(encoding="utf-8"))))
        counts[term] = n
    return counts


def sample_rank_check(
    fr: dict[int, pathlib.Path],
    zh: dict[int, pathlib.Path],
    ww: dict[int, pathlib.Path],
    sample: list[int],
) -> list[dict]:
    rows = []
    for n in sample:
        if n not in fr or n not in zh:
            continue
        fr_txt = body_of(fr[n].read_text(encoding="utf-8"))
        zh_txt = zh[n].read_text(encoding="utf-8", errors="replace")
        ww_txt = (
            ww[n].read_text(encoding="utf-8", errors="replace") if n in ww else ""
        )
        flags = []
        for zh_term, fr_term, ww_term in RANK_PAIRS:
            if zh_term in zh_txt and fr_term not in fr_txt:
                flags.append(
                    {
                        "zh": zh_term,
                        "expected_fr": fr_term,
                        "ww_still_in_fr": ww_term in fr_txt,
                        "ww_in_en": ww_term in ww_txt,
                    }
                )
        if flags:
            rows.append({"n": n, "flags": flags})
    return rows


def main() -> None:
    ww = index_ww()
    fr = index_fr()
    zh = index_zh()
    leftover = leftover_counts(fr)
    aligned = sorted(set(fr) & set(zh) & set(ww))
    sample = aligned[:: max(1, len(aligned) // 40)][:40] if aligned else []
    rank_flags = sample_rank_check(fr, zh, ww, sample + [105, 106, 120, 173, 851, 1473])
    report = {
        "ww_chapters": len(ww),
        "fr_chapters": len(fr),
        "zh_chapters": len(zh),
        "triple_aligned": len(aligned),
        "ww_range": [min(ww), max(ww)] if ww else None,
        "zh_range": [min(zh), max(zh)] if zh else None,
        "fr_range": [min(fr), max(fr)] if fr else None,
        "leftover_english_in_fr_body": leftover,
        "rank_sample_flags": rank_flags,
        "rank_sample_size": len(sample),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rank_sample_flags"}, ensure_ascii=False, indent=2))
    print(f"rank_sample_flags: {len(rank_flags)}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
