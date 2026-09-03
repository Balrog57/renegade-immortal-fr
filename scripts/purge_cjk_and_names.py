#!/usr/bin/env python3
"""Purge hanzi from src/ and unify remaining French names."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CH = SRC / "content" / "chapters"

CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]+")
NOM_CN = re.compile(r"^- \*\*Nom chinois :\*\*.*\n", re.M)
EMPTY_PARENS = re.compile(r"[（(]\s*[，,;:：/\-–—]*\s*[)）]")
EMPTY_PARENS2 = re.compile(r"[（(]\s*[)）]")
SPACE_PUNCT = re.compile(r" +([,.;:!?])")
MULTI_SPACE = re.compile(r"[ \t]{2,}")

# Names in running text (not URLs / filenames)
NAME_SUBS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"l['’]All-Seer"), "l'Omniscient"),
    (re.compile(r"L['’]All-Seer"), "L'Omniscient"),
    (re.compile(r"(?<![/\-_])\bAll-Seer\b(?![/\-_.])"), "Omniscient"),
    (re.compile(r"\bRed Butterfly\b"), "Papillon Rouge"),
    (re.compile(r"\bQin Lin\b"), "Qing Lin"),
    (re.compile(r"\bRussell\b"), "Luo Su"),
    (re.compile(r"\bYunzhu\b"), "Yunque"),
    (re.compile(r"\bLi Yuanfei\b"), "Li Yuanfeng"),
    (re.compile(r"\bLi Yunzi\b"), "Lie Yunzi"),
    (re.compile(r"Maître Zhong Shen"), "Maître Zhong Xuan"),
    (re.compile(r"\bTa Shen\b"), "Ta Shan"),
    (re.compile(r"Clan des Immortels Choisis"), "Clan des Immortels Délaissés"),
    (re.compile(r"\bThousand Fantasy Ruthless\b"), "Mille Illusions Impitoyables"),
]

CHAPTER_EXTRAS = [
    (
        "tome-7/0871-lenfant.md",
        "nourrir son Âme Naissante",
        "nourrir son esprit originel",
    ),
    (
        "tome-7/0871-lenfant.md",
        "son Âme Naissante de dragon de tonnerre antique",
        "son esprit originel de dragon de tonnerre antique",
    ),
    (
        "tome-8/0975-esprit-effraye.md",
        "comme s'il allait perdre la raison s'il ne se retirait pas immédiatement",
        "comme si son âme allait se dissiper s'il ne se retirait pas immédiatement",
    ),
    (
        "tome-7/0825-les-pensees-du-dieu-sanglant-2.md",
        "Clan des Immortels Choisis",
        "Clan des Immortels Délaissés",
    ),
    (
        "tome-2/0108-vieux-ami.md",
        "terrifia于 tant",
        "terrifia tant",
    ),
    (
        "tome-3/0200-yun-fei.md",
        "ri de façon狂 démente",
        "ri de façon démente",
    ),
    (
        "tome-6/0513-racine-desprit-doree.md",
        "s'膨胀 (gonfla)",
        "gonfla",
    ),
    (
        "tome-9/1388-nayez-pas-peur.md",
        "lui faisait于 une douleur",
        "lui faisait une douleur",
    ),
]


def clean_text(text: str) -> str:
    text = NOM_CN.sub("", text)
    text = CJK.sub("", text)
    text = EMPTY_PARENS.sub("", text)
    text = EMPTY_PARENS2.sub("", text)
    # leftover " ( Ning Qi)" after hanzi gone
    text = re.sub(r"\(\s*-\s*", "(", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = EMPTY_PARENS2.sub("", text)
    text = MULTI_SPACE.sub(" ", text)
    text = SPACE_PUNCT.sub(r"\1", text)
    text = re.sub(r" ·  · ", " · ", text)
    text = re.sub(r" · \n", "\n", text)
    return text


def apply_names(text: str) -> str:
    for pat, repl in NAME_SUBS:
        text = pat.sub(repl, text)
    return text


def safe_write(path: pathlib.Path, text: str) -> None:
    import time

    for attempt in range(8):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError:
            time.sleep(0.2 * (attempt + 1))
    path.write_text(text, encoding="utf-8")


def main() -> None:
    for rel, old, new in CHAPTER_EXTRAS:
        p = CH / rel
        t = p.read_text(encoding="utf-8")
        if old in t:
            safe_write(p, t.replace(old, new))

    n_files = 0
    for path in SRC.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".astro", ".ts", ".tsx", ".js", ".mjs"}:
            continue
        original = path.read_text(encoding="utf-8")
        text = apply_names(original)
        text = clean_text(text)
        # CJK leftovers like 于 glued to French
        text = text.replace("et atterrit", "et atterrit")
        text = re.sub(r"et\s+atterrit", "et atterrit", text)
        text = text.replace("mais se dirigea", "mais se dirigea")
        if text != original:
            safe_write(path, text)
            n_files += 1
    print(f"updated {n_files} files under src/")


if __name__ == "__main__":
    main()
