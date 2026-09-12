#!/usr/bin/env python3
"""
Script d'auto-correction pour le corpus de traduction v4 (Renegade Immortal).
Corrige:
1. Les anglicismes lexicaux ('Sect' -> 'Secte', accords 'le Sect' -> 'la Secte', etc.)
2. Normalisation des espaces insécables et nettoyages typographiques
"""

import pathlib
import re
import sys

def fix_text(text: str) -> tuple[str, int]:
    modifications = 0
    orig = text

    # Remplacements d'accords spécifiques pour "Sect"
    replacements = [
        (r"\bLe Sect\b", "La Secte"),
        (r"\ble Sect\b", "la Secte"),
        (r"\bDu Sect\b", "De la Secte"),
        (r"\bdu Sect\b", "de la Secte"),
        (r"\bAu Sect\b", "À la Secte"),
        (r"\bau Sect\b", "à la Secte"),
        (r"\bCe Sect\b", "Cette Secte"),
        (r"\bce Sect\b", "cette Secte"),
        (r"\bMon Sect\b", "Ma Secte"),
        (r"\bmon Sect\b", "ma Secte"),
        (r"\bTon Sect\b", "Ta Secte"),
        (r"\bton Sect\b", "ta Secte"),
        (r"\bSon Sect\b", "Sa Secte"),
        (r"\bson Sect\b", "sa Secte"),
        (r"\bGrand Sect\b", "Grande Secte"),
        (r"\bgrand Sect\b", "grande Secte"),
        (r"\bGrands Sects\b", "Grandes Sectes"),
        (r"\bgrands Sects\b", "grandes Sectes"),
        (r"\bSect\b", "Secte"),
        (r"\bSects\b", "Sectes"),
        (r"\bsect\b", "secte"),
        (r"\bsects\b", "sectes"),
        # Cultivation fixes
        (r"\bAlliance de Cultivation\b", "Alliance de la Cultivation"),
        (r"\balliance de Cultivation\b", "alliance de la Cultivation"),
    ]

    for pat, repl in replacements:
        new_text, count = re.subn(pat, repl, text)
        if count > 0:
            modifications += count
            text = new_text

    # Nettoyage des espaces multiples
    new_text, count = re.subn(r"[ \t]+", " ", text)
    # Nettoyage des retours multiples excessifs (plus de 2 sauts)
    new_text, count2 = re.subn(r"\n{3,}", "\n\n", new_text)

    return new_text, modifications

def process_corpus(target_dir: pathlib.Path):
    files = list(target_dir.rglob("*.txt"))
    total_files = len(files)
    modified_files = 0
    total_changes = 0

    print(f"Correction du corpus dans {target_dir} ({total_files} fichiers)...")
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="replace")
        new_txt, changes = fix_text(txt)
        if changes > 0:
            f.write_text(new_txt, encoding="utf-8")
            modified_files += 1
            total_changes += changes

    print(f"Terminé ! {modified_files} fichiers modifiés ({total_changes} corrections appliquées).")

if __name__ == "__main__":
    target = pathlib.Path(r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\traduction\v4")
    process_corpus(target)
