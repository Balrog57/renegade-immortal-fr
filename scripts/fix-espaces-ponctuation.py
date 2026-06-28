#!/usr/bin/env python3
"""Corrige les espaces manquants avant la ponctuation française (! ? ; :) dans les chapitres."""
import re, os, glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS_DIR = os.path.join(PROJECT_ROOT, "src", "content", "chapters")

# Chapitres avec >= 5 occurrences d'espace manquant avant !
chapters = [1219, 1280, 1288, 1289, 1309, 1312, 1313, 1340, 1346, 1351, 1352, 1358, 1362, 1386, 1395, 1398]

total_fixed = 0

for ch in chapters:
    # Trouver le fichier
    pattern = os.path.join(CHAPTERS_DIR, "**", f"{ch:04d}-*.md")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        print(f"ch{ch:04d}: fichier non trouvé")
        continue
    
    path = matches[0]
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Compter les occurrences avant correction
    before = len(re.findall(r'[^\s]!', content))
    
    NBSP = '\u00A0'
    # Corriger: ajouter un espace insécable avant ! ? ; :
    new_content = re.sub(r'([^\s])!', lambda m: m.group(1) + NBSP + '!', content)
    new_content = re.sub(r'([^\s])\?', lambda m: m.group(1) + NBSP + '?', new_content)
    new_content = re.sub(r'([^\s]);', lambda m: m.group(1) + NBSP + ';', new_content)
    new_content = re.sub(r'([^\s]):', lambda m: m.group(1) + NBSP + ':', new_content)
    
    after = len(re.findall(r'[^\s]!', new_content))
    fixed = before - after
    
    if fixed > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"ch{ch:04d}: {fixed} corrections (espaces avant ponctuation)")
        total_fixed += fixed
    else:
        print(f"ch{ch:04d}: déjà corrigé (0 corrections)")

print(f"\nTotal: {total_fixed} corrections dans {len(chapters)} chapitres")
