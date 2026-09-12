#!/usr/bin/env python3
"""
Synchronise et injecte les textes v4 corrigés et nettoyés dans src/content/chapters/.
Préserve scrupuleusement les frontmatters existants (slugs, métadonnées, etc.) et applique les polissages typographiques et lexicaux.
"""

import os
import pathlib
import re

def clean_french_text(text: str) -> str:
    # Retirer le BOM
    text = text.replace('\ufeff', '')

    # Retirer un titre éventuel en première ligne s'il ne se termine pas par de la ponctuation
    lines = text.splitlines()
    if lines:
        first = lines[0].strip()
        if first and not re.search(r'[.!?»"]$', first) and re.search(r'(?:chapitre|chapter|\b\d+\b)', first, re.I):
            text = '\n'.join(lines[1:]).strip()

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
        (r"\bdu Secte\b", "de la Secte"),
        (r"\bau Secte\b", "à la Secte"),
        (r"\ble Secte\b", "la Secte"),
        (r"\bSect\b", "Secte"),
        (r"\bSects\b", "Sectes"),
        (r"\bsect\b", "secte"),
        (r"\bsects\b", "sectes"),
        # Cultivation fixes
        (r"\bAlliance de Cultivation\b", "Alliance des Cultivateurs"),
        (r"\bAlliance de la Cultivation\b", "Alliance des Cultivateurs"),
        (r"\balliance de Cultivation\b", "alliance des Cultivateurs"),
        (r"\balliance de la Cultivation\b", "alliance des Cultivateurs"),
    ]

    for pat, repl in replacements:
        text = re.sub(pat, repl, text)

    # Nettoyage des espaces multiples horizontaux
    text = re.sub(r"[ \t]+", " ", text)
    # Nettoyage des paragraphes : normaliser en double sauts de ligne
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return '\n\n'.join(paras)

def extract_chapter_num(filename: str) -> int:
    m = re.search(r'(?:chapter|chapitre|de-|fr-|^|\b)(\d+)\b', filename, re.I)
    return int(m.group(1)) if m else 0

def sync_corpus():
    v4_dir = pathlib.Path(r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\traduction\v4")
    src_dir = pathlib.Path("src/content/chapters")

    # Index v4 files by chapter number
    v4_by_num: dict[int, list[pathlib.Path]] = {}
    for f in v4_dir.rglob("*.txt"):
        n = extract_chapter_num(f.name)
        if n > 0:
            v4_by_num.setdefault(n, []).append(f)

    # Index existing src markdown files
    src_by_num: dict[int, pathlib.Path] = {}
    for f in src_dir.rglob("*.md"):
        m = re.match(r"^(\d+)", f.name)
        if m:
            src_by_num[int(m.group(1))] = f

    print(f"Indexation: {len(v4_by_num)} numeros v4, {len(src_by_num)} fichiers markdown dans src.")

    updated_count = 0
    for num, src_path in sorted(src_by_num.items()):
        v4_files = v4_by_num.get(num)
        if not v4_files:
            print(f"  ! Manquant dans v4: ch. {num}")
            continue

        # Sort if multiple subparts (e.g. 717a, 717b)
        v4_files.sort(key=lambda p: p.name)
        combined_text = ""
        for vf in v4_files:
            t = vf.read_text(encoding="utf-8", errors="replace")
            combined_text += ("\n\n" if combined_text else "") + t

        cleaned_body = clean_french_text(combined_text)

        # Read existing frontmatter
        src_raw = src_path.read_text(encoding="utf-8", errors="replace").replace('\ufeff', '')
        fm_match = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)$", src_raw, re.DOTALL)
        if not fm_match:
            print(f"  ! Frontmatter introuvable pour ch. {num} ({src_path})")
            continue

        fm = fm_match.group(1)
        new_content = fm + cleaned_body + "\n"
        src_path.write_text(new_content, encoding="utf-8")
        updated_count += 1

    print(f"Synchronisation terminee : {updated_count} chapitres mis a jour dans {src_dir}.")

if __name__ == "__main__":
    sync_corpus()
