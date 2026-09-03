#!/usr/bin/env python3
"""Second pass: French grammar after leftover-English replacements."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "src" / "content" / "chapters",
    ROOT / "src" / "content" / "wiki",
]

SUBS = [
    ("Scryer du Nirvana", "Scruteur du Nirvana"),
    ("stade de Scruteur du Nirvana", "stade du Scruteur du Nirvana"),
    ("Nettoyage du Nirvana", "Purificateur du Nirvana"),
    ("Nettoyant du Nirvana", "Purificateur du Nirvana"),
    ("All-Seers", "Omniscients"),
    ("de l'Vide", "du Vide"),
    ("à l'Vide", "au Vide"),
    ("une puissante Sens Divin", "un puissant Sens Divin"),
    ("De quelle Sens Divin", "De quel Sens Divin"),
    ("de quelle Sens Divin", "de quel Sens Divin"),
    ("de la Sens Divin", "du Sens Divin"),
    ("à la Sens Divin", "au Sens Divin"),
    ("saisir la Sens Divin", "saisir le Sens Divin"),
    ("Cette Sens Divin", "Ce Sens Divin"),
    ("cette Sens Divin", "ce Sens Divin"),
    ("Lorsque la Sens Divin", "Lorsque le Sens Divin"),
    ("lorsque la Sens Divin", "lorsque le Sens Divin"),
    ("La Sens Divin", "Le Sens Divin"),
    ("la Sens Divin", "le Sens Divin"),
    ("ancêtres Âme Naissante", "ancêtres de l'Âme Naissante"),
    ("cultivateur Âme Naissante", "cultivateur de l'Âme Naissante"),
    ("cultivateurs Âme Naissante", "cultivateurs de l'Âme Naissante"),
    ("Grand Ancien Âme Naissante", "Grand Ancien de l'Âme Naissante"),
    ("du serpent aux yeux de lune", "du Serpent aux yeux de lune"),
    ("Du serpent aux yeux de lune", "Du Serpent aux yeux de lune"),
]


SKIP_FM = ("en:", "booktitle:", "slug:", "url:")


def apply_subs(s: str) -> str:
    for old, repl in SUBS:
        s = s.replace(old, repl)
    return s


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
