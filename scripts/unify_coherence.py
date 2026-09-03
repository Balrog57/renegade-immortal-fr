#!/usr/bin/env python3
"""Unify leftover-English replacements so the same entity has one French name."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "src" / "content" / "chapters",
    ROOT / "src" / "content" / "wiki",
]
SKIP_FM = ("en:", "booktitle:", "slug:", "url:")

# Longest first.
SUBS = [
    # Rank calques still in WW order
    ("stade intermédiaire de la Scryer Nirvana", "stade intermédiaire du Scruteur du Nirvana"),
    ("stade tardif Scryer Nirvana", "stade tardif du Scruteur du Nirvana"),
    ("sommet du Scryer Nirvana", "sommet du Scruteur du Nirvana"),
    ("stade du Scryer Nirvana", "stade du Scruteur du Nirvana"),
    ("stade de Scryer Nirvana", "stade du Scruteur du Nirvana"),
    ("stade Scryer Nirvana", "stade du Scruteur du Nirvana"),
    ("étape du Scryer Nirvana", "étape du Scruteur du Nirvana"),
    ("stade du Scryer de Nirvana", "stade du Scruteur du Nirvana"),
    ("stade de Scryer de Nirvana", "stade du Scruteur du Nirvana"),
    ("cultivateur Scryer de Nirvana", "cultivateur Scruteur du Nirvana"),
    ("cultivateur Scryer Nirvana", "cultivateur Scruteur du Nirvana"),
    ("cultivateurs Scryeur de Nirvana", "cultivateurs Scruteur du Nirvana"),
    ("Scryeur de Nirvana", "Scruteur du Nirvana"),
    ("Scryer de Nirvana", "Scruteur du Nirvana"),
    ("Scryer Nirvana", "Scruteur du Nirvana"),
    ("Cleanser Nirvana", "Purificateur du Nirvana"),
    ("Cleanser du Nirvana", "Purificateur du Nirvana"),
    ("Shatterer Nirvana", "Briseur du Nirvana"),
    ("Nettoyeur Nirvana", "Purificateur du Nirvana"),
    ("Nettoyeur de Nirvana", "Purificateur du Nirvana"),
    ("Nettoyeur du Nirvana", "Purificateur du Nirvana"),
    ("stade Nettoyeur de Nirvana", "stade du Purificateur du Nirvana"),
    ("Clairvoyant du Nirvana", "Scruteur du Nirvana"),
    ("Clairvoyant de Nirvana", "Scruteur du Nirvana"),
    ("seuil du Clairvoyant de Nirvana", "seuil du Scruteur du Nirvana"),
    ("stades de Clairvoyant et de Purificateur du Nirvana", "stades du Scruteur et du Purificateur du Nirvana"),
    ("Purificateur de Nirvana", "Purificateur du Nirvana"),
    ("Scruteur de Nirvana", "Scruteur du Nirvana"),
    ("Briseur de Nirvana", "Briseur du Nirvana"),
    # Everlasting leftover
    ("Réprimande au Secte Everlasting", "Réprimande à la Secte Éternelle"),
    ("Secte Everlasting", "Secte Éternelle"),
    ("Maître Everlasting", "Maître Éternel"),
    # Cloud Soul hyphen
    ("Maître Nuage Âme", "Maître Nuage-Âme"),
    ("Nuage Âme", "Nuage-Âme"),
    # Greed character still called Avarice
    ("de l'Avarice", "de Cupidité"),
    ("à l'Avarice", "à Cupidité"),
    ("L'Avarice", "Cupidité"),
    ("l'Avarice", "Cupidité"),
    ("Sort de l'Avarice", "Sort de Cupidité"),
    ("Voyage de l'Avarice", "Voyage de Cupidité"),
    ("Trésor de l'Avarice", "Trésor de Cupidité"),
    # 望月 creature
    ("Serpents Lunaires", "Serpents aux yeux de lune"),
    ("serpents lunaires", "serpents aux yeux de lune"),
    ("Serpent Lunaire", "Serpent aux yeux de lune"),
    ("serpent lunaire", "serpent aux yeux de lune"),
    ("Serpent Clair de Lune", "Serpent aux yeux de lune"),
    ("serpent clair de lune", "serpent aux yeux de lune"),
    ("Serpent lunivore", "Serpent aux yeux de lune"),
    ("serpent lunivore", "serpent aux yeux de lune"),
    ("Serpent aux Yeux de Lune", "Serpent aux yeux de lune"),
    ("Serpents Lunivores", "serpents aux yeux de lune"),
    ("Serpent Lunivore", "Serpent aux yeux de lune"),
    ("Senior Avarice", "Senior Cupidité"),
    ("Seigneur Avarice", "Seigneur Cupidité"),
    ("cette Avarice", "Cupidité"),
    ("Cet Avarice", "Cupidité"),
    ("qu'Avarice", "que Cupidité"),
    ("d'Avarice", "de Cupidité"),
    ("était Avarice", "était Cupidité"),
    ("pas Avarice", "pas Cupidité"),
    ("« Avarice! »", "« Cupidité! »"),
    ("Avarice n'allait", "Cupidité n'allait"),
    ("Avarice le regarda", "Cupidité le regarda"),
    ("Avarice réfléchit", "Cupidité réfléchit"),
    ("Les yeux d'Avarice", "Les yeux de Cupidité"),
]


def apply_subs(s: str) -> str:
    s = s.replace("Mer de l'Avarice", "\x00MER_AVARICE\x00")
    s = s.replace("Avarice, ignorance", "\x00AVARICE_IGNORANCE\x00")
    s = s.replace("Maître Flamesspark", "Maître Flamespark")
    for old, new in SUBS:
        s = s.replace(old, new)
    return (
        s.replace("\x00MER_AVARICE\x00", "Mer de l'Avarice")
        .replace("\x00AVARICE_IGNORANCE\x00", "Avarice, ignorance")
    )


def process(text: str) -> str:
    if not text.startswith("---"):
        return apply_subs(text)
    parts = text.split("---", 2)
    if len(parts) < 3:
        return apply_subs(text)
    fm_lines = []
    for line in parts[1].splitlines(True):
        low = line.lstrip().lower()
        if any(low.startswith(k) for k in SKIP_FM):
            fm_lines.append(line)
        else:
            fm_lines.append(apply_subs(line))
    return "---" + "".join(fm_lines) + "---" + apply_subs(parts[2])


def main() -> None:
    files: list[pathlib.Path] = []
    for d in PATHS:
        files.extend(d.rglob("*.md"))
    changed = 0
    for p in files:
        orig = p.read_text(encoding="utf-8")
        new = process(orig)
        if new != orig:
            p.write_text(new, encoding="utf-8", newline="\n")
            changed += 1
    print(f"Fichiers modifiés: {changed}")


if __name__ == "__main__":
    main()
