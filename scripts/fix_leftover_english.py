#!/usr/bin/env python3
"""Replace leftover Wuxiaworld English in French chapter bodies (not en:/slug/bookTitle)."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CH = ROOT / "src" / "content" / "chapters"
WIKI = ROOT / "src" / "content" / "wiki"

# Longest first. Applied only to title + body, never to en/bookTitle/slug.
PHRASE_SUBS: list[tuple[str, str]] = [
    ("Devil Master Nine Heavens", "Maître Démon des Neuf Cieux"),
    ("Great Desolation Old Poison", "Vieux Poison de la Grande Désolation"),
    ("Great Desolation", "Grande Désolation"),
    ("Maître Cloud Soul", "Maître Nuage-Âme"),
    ("Master Cloud Soul", "Maître Nuage-Âme"),
    ("compagnon Cloud Soul", "compagnon Nuage-Âme"),
    ("Maître Ashen Pine", "Maître Pin Cendré"),
    ("Master Ashen Pine", "Maître Pin Cendré"),
    ("compagnon Ashen Pine", "compagnon Pin Cendré"),
    ("Ashen Pine", "Pin Cendré"),
    ("Cloud Soul", "Nuage-Âme"),
    ("Everlasting Sect", "Secte Éternelle"),
    ("Sect Everlasting", "Secte Éternelle"),
    ("sect everlasting", "secte éternelle"),
    ("Hunchback Meng", "Bossu Meng"),
    ("Serpent Moongazer", "Serpent aux yeux de lune"),
    ("serpent Moongazer", "serpent aux yeux de lune"),
    ("Serpents Moongazer", "Serpents aux yeux de lune"),
    ("serpents Moongazer", "serpents aux yeux de lune"),
    ("Moongazer Serpent", "Serpent aux yeux de lune"),
    ("Heaven Defying Bead", "Perle défiant les cieux"),
    ("Pseudo Nirvana Void", "Pseudo Vide du Nirvana"),
    ("pseudo-nirvana-void", "pseudo-nirvana-void"),  # no-op guard, skipped via skip
    ("Nirvana Scryer", "Scruteur du Nirvana"),
    ("Nirvana Cleanser", "Purificateur du Nirvana"),
    ("Nirvana Shatterer", "Briseur du Nirvana"),
    ("Nirvana Void", "Vide du Nirvana"),
    ("Spirit Void", "Vide Spirituel"),
    ("Arcane Void", "Vide Arcanique"),
    ("Void Tribulant", "Tribulant du Vide"),
    ("Heaven's Blight", "Fléau des Cieux"),
    ("Heavens Blight", "Fléau des Cieux"),
    ("Heaven Trampling", "Piétinement des Cieux"),
    ("Illusory Yin", "Yin Illusoire"),
    ("Corporeal Yang", "Yang Corporel"),
    ("Spirit Severing", "Formation de l'Âme"),
    ("Soul Transformation", "Transformation de l'Âme"),
    ("Soul Formation", "Formation de l'Âme"),
    ("Nascent Soul", "Âme Naissante"),
    ("Core Formation", "Formation du Noyau"),
    ("Foundation Establishment", "Établissement des Fondations"),
    ("Qi Condensation", "Condensation du Qi"),
    ("Divine Sense", "Sens Divin"),
    ("Joss Flame", "Flamme Joss"),
    ("Joss Flames", "Flammes Joss"),
    ("flying sword", "épée volante"),
    ("Flying Sword", "Épée volante"),
    ("spiritual energy", "énergie spirituelle"),
    ("Spiritual Energy", "Énergie spirituelle"),
]

# Regex substitutions after phrase subs.
REGEX_SUBS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\ble Moongazer\b"), "le serpent aux yeux de lune"),
    (re.compile(r"\bLe Moongazer\b"), "Le serpent aux yeux de lune"),
    (re.compile(r"\bdu Moongazer\b"), "du serpent aux yeux de lune"),
    (re.compile(r"\bau Moongazer\b"), "au serpent aux yeux de lune"),
    (re.compile(r"\bla Moongazer\b"), "le serpent aux yeux de lune"),
    (re.compile(r"\bLa Moongazer\b"), "Le serpent aux yeux de lune"),
    (re.compile(r"\bdes Moongazer\b"), "des serpents aux yeux de lune"),
    (re.compile(r"\bMoongazer\b"), "serpent aux yeux de lune"),
    (re.compile(r"\bHunchback\b"), "Bossu"),
    (re.compile(r"\bGreed\b"), "Cupidité"),
]

SKIP_FM_KEYS = ("en:", "booktitle:", "slug:", "url:")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def apply_subs(s: str) -> str:
    for old, new in PHRASE_SUBS:
        if old == new:
            continue
        s = s.replace(old, new)
    for pat, repl in REGEX_SUBS:
        s = pat.sub(repl, s)
    return s


def fix_frontmatter(fm: str) -> str:
    out_lines = []
    for line in fm.splitlines(True):
        stripped = line.lstrip().lower()
        if any(stripped.startswith(k) for k in SKIP_FM_KEYS):
            out_lines.append(line)
            continue
        out_lines.append(apply_subs(line))
    return "".join(out_lines)


def process_file(path: pathlib.Path) -> int:
    orig = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(orig)
    if fm:
        new = "---" + fix_frontmatter(fm) + "---" + apply_subs(body)
    else:
        new = apply_subs(orig)
    if new != orig:
        path.write_text(new, encoding="utf-8", newline="\n")
        return 1
    return 0


def main() -> None:
    files = sorted(CH.rglob("*.md")) + sorted(WIKI.rglob("*.md"))
    changed = 0
    for p in files:
        changed += process_file(p)
    print(f"Fichiers modifiés: {changed}/{len(files)}")


if __name__ == "__main__":
    main()
