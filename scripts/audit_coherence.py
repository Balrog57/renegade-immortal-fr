#!/usr/bin/env python3
"""Audit coherence of leftover-English replacements across all chapter bodies."""
from __future__ import annotations

import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
CH = ROOT / "src" / "content" / "chapters"

SKIP_FM = ("en:", "booktitle:", "slug:", "url:")

PAIRS = {
    "moongazer": [
        ("yeux de lune", re.compile(r"yeux de lune", re.I)),
        ("serpent lunaire", re.compile(r"serpent lunaire", re.I)),
        ("serpents lunaires", re.compile(r"serpents lunaires", re.I)),
        ("serpent lunivore", re.compile(r"serpent lunivore", re.I)),
        ("clair de lune", re.compile(r"serpent clair de lune", re.I)),
        ("Moongazer leftover", re.compile(r"Moongazer")),
    ],
    "greed": [
        ("Cupidité", re.compile(r"\bCupidité\b")),
        ("Avarice perso", re.compile(r"\b[Ll]'Avarice\b|\bAvarice\b")),
        ("Greed leftover", re.compile(r"\bGreed\b")),
    ],
    "hunchback": [
        ("Bossu Meng", re.compile(r"Bossu Meng")),
        ("Hunchback leftover", re.compile(r"Hunchback")),
    ],
    "scryer": [
        ("Scruteur du Nirvana", re.compile(r"Scruteur du Nirvana")),
        ("Scryer leftover", re.compile(r"Scryer")),
        ("Nirvana Scryer leftover", re.compile(r"Nirvana Scryer")),
    ],
    "cleanser": [
        ("Purificateur du Nirvana", re.compile(r"Purificateur du Nirvana")),
        ("Nettoyant du Nirvana", re.compile(r"Nettoyant du Nirvana")),
        ("Nettoyage du Nirvana", re.compile(r"Nettoyage du Nirvana")),
        ("Cleanser leftover", re.compile(r"Nirvana Cleanser|Cleanser du Nirvana")),
    ],
    "cloud_soul": [
        ("Nuage-Âme", re.compile(r"Nuage-Âme")),
        ("Nuage Âme", re.compile(r"Nuage Âme")),
        ("Cloud Soul leftover", re.compile(r"Cloud Soul")),
    ],
    "ashen": [
        ("Pin Cendré", re.compile(r"Pin Cendré")),
        ("Ashen Pine leftover", re.compile(r"Ashen Pine")),
    ],
    "nine_heavens": [
        ("Maître Démon des Neuf Cieux", re.compile(r"Maître Démon des Neuf Cieux")),
        ("Devil Master leftover", re.compile(r"Devil Master")),
    ],
    "desolation": [
        ("Grande Désolation", re.compile(r"Grande Désolation")),
        ("Great Desolation leftover", re.compile(r"Great Desolation")),
    ],
    "divine_sense": [
        ("Sens Divin", re.compile(r"Sens Divin")),
        ("sens divin", re.compile(r"sens divin")),
        ("Divine Sense leftover", re.compile(r"Divine Sense")),
    ],
    "everlasting": [
        ("Secte Éternelle", re.compile(r"Secte Éternelle", re.I)),
        ("secte éternelle", re.compile(r"secte éternelle")),
        ("Everlasting leftover", re.compile(r"Everlasting")),
    ],
}

BROKEN = [
    ("l'Vide", re.compile(r"l'Vide")),
    ("la Sens Divin", re.compile(r"\bla Sens Divin\b")),
    ("cette Sens Divin", re.compile(r"\bcette Sens Divin\b")),
    ("imprégnée après Sens Divin", re.compile(r"Sens Divin était imprégnée")),
    ("fusionnée après Sens Divin", re.compile(r"Sens Divin.{0,40}fusionnée")),
    ("repoussée après Sens Divin", re.compile(r"Sens Divin.{0,40}repoussée")),
    ("du du", re.compile(r"\bdu du\b")),
    ("de de ", re.compile(r"\bde de ")),
    ("le le ", re.compile(r"\ble le ")),
    ("All-Seers leftover", re.compile(r"All-Seers")),
    ("Qin Lin leftover", re.compile(r"\bQin Lin\b")),
]


def body_of(text: str) -> tuple[str, str]:
    title = ""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    for line in parts[1].splitlines():
        if line.strip().lower().startswith("title:"):
            title = line.split(":", 1)[1].strip().strip('"')
    return title, parts[2]


def main() -> None:
    files = sorted(CH.rglob("*.md"))
    totals: dict[str, Counter] = {k: Counter() for k in PAIRS}
    mixed: dict[str, list[str]] = defaultdict(list)
    broken_hits: list[tuple[str, str, str]] = []
    leftover_en_body = Counter()

    leftover_en_terms = [
        "Hunchback",
        "Moongazer",
        r"\bGreed\b",
        "Nirvana Scryer",
        "Nirvana Cleanser",
        "Nirvana Shatterer",
        "Nascent Soul",
        "Soul Formation",
        "Divine Sense",
        "Devil Master",
        "Ashen Pine",
        "Cloud Soul",
        "Everlasting Sect",
        "All-Seer",
        "flying sword",
        "Joss Flame",
        "Great Desolation",
    ]

    for p in files:
        raw = p.read_text(encoding="utf-8")
        title, body = body_of(raw)
        rel = str(p.relative_to(CH))
        scan = title + "\n" + body
        for group, terms in PAIRS.items():
            present = []
            for name, pat in terms:
                n = len(pat.findall(scan))
                if n:
                    totals[group][name] += n
                    present.append(name)
            names = [n for n in present if "leftover" not in n]
            if len(set(names)) >= 2:
                mixed[group].append(f"{rel}: {', '.join(present)}")
        for name, pat in BROKEN:
            if pat.search(scan):
                m = pat.search(scan)
                broken_hits.append((name, rel, (m.group(0) if m else "")[:80]))
        for term in leftover_en_terms:
            pat = re.compile(term)
            n = len(pat.findall(scan))
            if n:
                leftover_en_body[term] += n

    print("=== COUNTS ===")
    for group, c in totals.items():
        print(f"\n[{group}]")
        for k, v in c.most_common():
            print(f"  {k}: {v}")

    print("\n=== MIXED IN SAME FILE ===")
    for group, rows in mixed.items():
        print(f"\n[{group}] {len(rows)} files")
        for r in rows[:12]:
            print(f"  {r}")
        if len(rows) > 12:
            print(f"  ... +{len(rows)-12}")

    print("\n=== BROKEN ===")
    by = defaultdict(list)
    for name, rel, snip in broken_hits:
        by[name].append((rel, snip))
    for name, rows in by.items():
        print(f"\n[{name}] {len(rows)}")
        for rel, snip in rows[:8]:
            print(f"  {rel}: {snip}")

    print("\n=== LEFTOVER EN IN TITLE+BODY ===")
    for k, v in leftover_en_body.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
