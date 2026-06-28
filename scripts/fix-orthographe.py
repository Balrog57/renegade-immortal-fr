#!/usr/bin/env python3
"""
Correction orthographique automatique — fautes d'accent courantes.
Applique des corrections sûres (sans faux positifs) sur tous les chapitres.

Usage: python scripts/fix-orthographe.py [--dry-run] [--chapter N]
"""

import os, re, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"

# Corrections sûres : le motif ne peut pas être un mot correct dans un autre contexte
CORRECTIONS = [
    # Accents manquants sur mots très fréquents
    (r'\btres\b', 'très'),        # "tres" → "très" (jamais un mot FR correct)
    (r'\bapres\b', 'après'),      # "apres" → "après"
    (r'\betre\b', 'être'),        # "etre" → "être"
    (r'\bmeme\b', 'même'),        # "meme" → "même"
    (r'\bgrece\b', 'grâce'),      # "grece" → "grâce"
    (r'\bgrace\b', 'grâce'),      # "grace" → "grâce" (le mot anglais n'apparaît pas en FR)
    (r'\bmalgres\b', 'malgré'),   # "malgres" → "malgré"
    (r'\bmalgre\b', 'malgré'),    # "malgre" → "malgré"
    (r'\bparmis\b', 'parmi'),     # "parmis" → "parmi"
    (r'\bpeutetre\b', 'peut-être'),  # "peutetre" → "peut-être"
    (r'\bentrain\b', 'en train'), # "entrain" → "en train"
    (r'\bforet\b', 'forêt'),      # "foret" → "forêt"
    (r'\bfete\b', 'fête'),        # "fete" → "fête"
    (r'\btete\b', 'tête'),        # "tete" → "tête"
    (r'\barrete\b', 'arrête'),    # "arrete" → "arrête"
    (r'\bdeja\b', 'déjà'),        # "deja" → "déjà"
    (r'\bdegat\b', 'dégât'),      # "degat" → "dégât"
    (r'\bdegats\b', 'dégâts'),    # "degats" → "dégâts"
    (r'\binteret\b', 'intérêt'),  # "interet" → "intérêt"
    (r'\binterets\b', 'intérêts'),# "interets" → "intérêts"
    (r'\bpret\b', 'prêt'),        # "pret" → "prêt" (contexte xianxia: toujours "prêt")
    (r'\bprets\b', 'prêts'),      # "prets" → "prêts"
    (r'\bapret\b', 'après'),      # "apret" → "après" (faute de frappe)
    (r'\bapres\b', 'après'),      # déjà couvert, redondance safe
    (r'\bveritable\b', 'véritable'),
    (r'\bveritables\b', 'véritables'),
    (r'\bverite\b', 'vérité'),
    (r'\bverites\b', 'vérités'),
    (r'\bevenement\b', 'événement'),
    (r'\bevenements\b', 'événements'),
    (r'\bdeuxiemme\b', 'deuxième'),  # faute de frappe
    (r'\bpremiere\b', 'première'),   # "premiere" → "première"
    (r'\bderniere\b', 'dernière'),   # "derniere" → "dernière"
    (r'\bentier\b', 'entier'),       # déjà correct
    (r'\bentieres\b', 'entières'),
    (r'\bcolere\b', 'colère'),
    (r'\bmystere\b', 'mystère'),
    (r'\bmysterieux\b', 'mystérieux'),
    (r'\bmysterieuse\b', 'mystérieuse'),
    # Ponctuation française : espace avant ; : ! ?
    # (trop risqué en automatique, à vérifier manuellement)
]

def find_chapter_files():
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in sorted(files):
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    yield int(m.group(1)), Path(root) / f

def fix_chapter(path, dry_run=False):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    for pattern, replacement in CORRECTIONS:
        # Only replace if the pattern exists
        matches = list(re.finditer(pattern, content))
        if matches:
            # For each match, preserve case of first letter
            for m in matches:
                old = m.group(0)
                if old[0].isupper():
                    new = replacement[0].upper() + replacement[1:]
                else:
                    new = replacement
                if old != new:
                    changes.append((old, new, m.start()))
            
            # Apply replacement (case-insensitive but preserving case)
            content = re.sub(pattern, lambda m: replacement[0].upper() + replacement[1:] if m.group(0)[0].isupper() else replacement, content)
    
    if not changes:
        return 0, []
    
    if not dry_run:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return len(changes), changes

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--chapter', type=int, default=0)
    args = parser.parse_args()
    
    if args.chapter > 0:
        for ch_num, path in find_chapter_files():
            if ch_num == args.chapter:
                count, changes = fix_chapter(path, args.dry_run)
                print(f"Chapitre {ch_num}: {count} corrections")
                for old, new, pos in changes[:20]:
                    print(f"  « {old} » → « {new} »")
                return
        print(f"Chapitre {args.chapter} non trouvé")
        return
    
    # All chapters
    total_changes = 0
    chapters_fixed = 0
    
    for ch_num, path in find_chapter_files():
        count, changes = fix_chapter(path, args.dry_run)
        if count > 0:
            chapters_fixed += 1
            total_changes += count
            if chapters_fixed <= 20 or chapters_fixed % 100 == 0:
                print(f"  ch{ch_num:04d}: {count} corrections")
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Chapitres corrigés: {chapters_fixed}")
    print(f"Total corrections: {total_changes}")
    if args.dry_run:
        print("(Mode simulation)")

if __name__ == '__main__':
    main()
