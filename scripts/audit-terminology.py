#!/usr/bin/env python3
"""
Audit terminologique INTELLIGENT — ne signale que les VRAIS écarts.
Règles :
- Ignore les différences de casse pour les noms propres (majuscule = nom propre)
- Ne remplace pas les termes dans des noms composés connus
- Utilise des word boundaries pour éviter les faux positifs

Usage: python scripts/audit-terminology.py [--sample N] [--output reports/terminology-issues.json]
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
GLOSSARY_PATH = PROJECT_ROOT / "scripts" / "glossary.json"
OUTPUT_DIR = PROJECT_ROOT / "reports"

# Noms propres composés connus — ne pas toucher
KNOWN_COMPOUNDS = [
    # Lieux
    "Mer des Esprits Démoniaques", "Mer des Esprits Démoniaques de l'Est",
    "Ancien Système Stellaire", "Ancien Royaume Céleste",
    "Continent Astral Immortel", "Continent du Taureau Céleste",
    "Système Stellaire Primordial Ancien",
    "Pays du Démon de Feu", "Pays du Démon du Vent",
    "Royaume du Dieu Ancien", "Royaume Céleste",
    "Monde des Immortels", "Monde Mortel",
    # Organisations
    "Secte du Destin Céleste", "Secte Divine",
    "Palais de la Punition Céleste", "Conseil Souverain",
    "Clan de l'Immortel Banni", "Clan du Moineau de Feu",
    "Secte de Raffinage des Âmes", "Secte de la Lutte contre le Mal",
    "Secte du Ciel des Nuages", "Secte Originelle",
    "Clan Dévoreur de Lune", "Clan de la Foudre Dispersée",
    # Techniques/Concepts
    "Formation des Sept Méridiens", "Messagers du Destin",
    "Flamme Joss", "Flammes Joss",
    "Tribulation Céleste", "Châtiment Divin",
    "Dao Céleste", "Dao du Destin",
    # Personnages/Titres
    "Empereur Céleste", "Roi Céleste", "Seigneur Céleste",
    "Dieu Ancien", "Démon Ancien", "Diable Ancien",
    "Grand Empyrée", "Exaltation Empyréenne",
    # Stades
    "Âme Naissante", "Formation du Noyau", "Noyau d'Or",
    "Établissement des Fondations", "Condensation du Qi",
    "Formation de l'Âme", "Transformation de l'Âme",
    "Séparation de l'Âme", "Yin Illusoire", "Yang Corporel",
    "Fléau Céleste", "Scruteur du Nirvana", "Purificateur du Nirvana",
    "Briseur du Nirvana", "Tribulation du Vide", "Vide Arcanique",
    "Tribulation Arcanique", "Demi-Foulée Céleste", "Foulée Céleste",
    "Exaltation Dorée", "Corps Céleste",
    "Grand Accomplissement des 5 Essences", "Grande Porte du Vide",
    "Déclin Céleste", "Royaume Ji",
]

# Build a set of protected phrases (case-insensitive matching)
PROTECTED_PHRASES = set()
for phrase in KNOWN_COMPOUNDS:
    PROTECTED_PHRASES.add(phrase.lower())


def load_glossary():
    with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_chapter_body(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[2]
    return content


def find_chapter_files():
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in sorted(files):
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    yield int(m.group(1)), Path(root) / f


def is_protected(text, start, end):
    """Check if the match at [start:end] is inside a known compound name."""
    # Expand context to find the full phrase
    context_start = max(0, start - 60)
    context_end = min(len(text), end + 60)
    context = text[context_start:context_end].lower()

    # Check if any protected phrase contains this match
    match_text = text[start:end].lower()
    for phrase in PROTECTED_PHRASES:
        if match_text in phrase and phrase in context:
            return True
    return False


def is_name_proper(text, start, end):
    """Check if the match is a proper noun (starts with uppercase in French context)."""
    match = text[start:end]
    # If it starts with uppercase and is not at sentence start, it's likely a proper noun
    if match[0].isupper():
        # Check if it's at the start of a sentence
        before = text[max(0, start-2):start].strip()
        if before and before[-1] not in '.!?':
            return True
    return False


def audit_chapter(chapter_num, file_path, glossary):
    """
    Audit a single chapter. Only reports REAL issues:
    - Different translation choices (not just case)
    - Not inside known compound names
    """
    text = read_chapter_body(file_path)
    issues = []

    # Only check terms that have actual alternative translations (not just case variants)
    real_check_terms = {
        # EN term -> (canonical FR, [wrong alternatives])
        'soul': ('âme', ['esprit']),  # "esprit" used where "âme" should be
        'ancient': ('ancien', ['antique']),  # "Antique" used where "ancien" should be
        'demon': ('démon', ['démoniaque']),  # "Démoniaque" used where "démon" should be
        'devil': ('diable', ['démon']),  # "démon" used where "diable" should be
        'immortal': ('immortel', ['immortelle']),  # gender mismatch
        'spiritual energy': ('énergie spirituelle', ['force spirituelle', 'qi spirituel']),
        'divine sense': ('sens divin', ['conscience divine', 'perception divine']),
        'magic treasure': ('trésor magique', ['objet magique', 'artefact magique']),
        'spatial rift': ('faille spatiale', ['déchirure spatiale', 'fissure spatiale']),
        'heavenly tribulation': ('tribulation céleste', ['tribulation du ciel', 'épreuve céleste']),
        'divine retribution': ('châtiment divin', ['punition divine', 'rétribution divine']),
        'bloodline': ('lignée', ['lignage']),
        'storage bag': ('sac de stockage', ['sacoche de stockage', 'bourse de stockage']),
        'spiritual jade': ('jade spirituel', ['pierre spirituelle', 'pierre d\'esprit']),
        'spirit beast': ('bête spirituelle', ['animal spirituel', 'créature spirituelle']),
        'divine ability': ('aptitude divine', ['capacité divine', 'pouvoir divin', 'technique divine']),
        'body cultivator': ('cultivateur corporel', ['cultivateur de corps']),
        'joss flame': ('flamme joss', ['flamme de joss']),
        'origin soul': ('âme originelle', ['âme d\'origine', 'âme primordiale']),
        'pill': ('pilule', ['pillule']),
        'mortal world': ('monde mortel', ['monde des mortels']),
        'immortal world': ('monde immortel', ['monde des immortels']),
        'celestial realm': ('royaume céleste', ['domaine céleste']),
        'star system': ('système stellaire', ['système d\'étoiles']),
        'cultivator': ('cultivateur', ['pratiquant', 'cultivant']),
    }

    for term_en, (canonical, wrong_terms) in real_check_terms.items():
        for wrong in wrong_terms:
            # Use word boundary matching
            pattern = re.compile(r'\b' + re.escape(wrong) + r'\b', re.IGNORECASE)
            for m in pattern.finditer(text):
                start, end = m.start(), m.end()

                # Skip if inside a protected compound name
                if is_protected(text, start, end):
                    continue

                # Skip if it's a proper noun (uppercase in non-sentence-start position)
                if is_name_proper(text, start, end):
                    continue

                # Skip if the canonical form is already used here
                if text[start:end].lower() == canonical.lower():
                    continue

                issues.append({
                    'term_en': term_en,
                    'canonical': canonical,
                    'found': text[start:end],
                    'position': start,
                    'context': text[max(0, start-40):end+40].replace('\n', ' ')
                })

    return {
        'chapter': chapter_num,
        'file': str(file_path.relative_to(PROJECT_ROOT)),
        'issue_count': len(issues),
        'issues': issues
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Audit terminologique intelligent')
    parser.add_argument('--sample', type=int, default=0, help='Auditer N chapitres (0 = tous)')
    parser.add_argument('--output', type=str, default=None, help='Fichier JSON de sortie')
    parser.add_argument('--summary-only', action='store_true')
    args = parser.parse_args()

    glossary = load_glossary()
    print(f"Glossaire chargé: {len(glossary)} entrées")
    print(f"Phrases protégées: {len(PROTECTED_PHRASES)}")

    chapters = list(find_chapter_files())
    print(f"Chapitres trouvés: {len(chapters)}")

    if args.sample > 0:
        import random
        random.seed(42)
        chapters = random.sample(chapters, min(args.sample, len(chapters)))
        print(f"Échantillon: {len(chapters)} chapitres")

    results = []
    total_issues = 0
    issue_by_term = Counter()
    chapters_with_issues = 0

    for i, (ch_num, file_path) in enumerate(chapters):
        if (i + 1) % 200 == 0:
            print(f"  Progression: {i+1}/{len(chapters)}...")

        result = audit_chapter(ch_num, file_path, glossary)
        if result['issue_count'] > 0:
            chapters_with_issues += 1
            total_issues += result['issue_count']
            for issue in result['issues']:
                issue_by_term[issue['term_en']] += 1

        if not args.summary_only:
            results.append(result)

    summary = {
        'total_chapters_audited': len(chapters),
        'chapters_with_issues': chapters_with_issues,
        'total_issues': total_issues,
        'issues_by_term': dict(issue_by_term.most_common()),
    }

    if not args.summary_only:
        summary['details'] = [r for r in results if r['issue_count'] > 0]

    output_path = args.output or str(OUTPUT_DIR / 'terminology-issues.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n=== RÉSULTATS ===")
    print(f"Chapitres audités: {len(chapters)}")
    print(f"Chapitres avec vrais problèmes: {chapters_with_issues} ({chapters_with_issues/len(chapters)*100:.1f}%)")
    print(f"Total vrais problèmes: {total_issues}")
    if total_issues > 0:
        print(f"\nPar terme:")
        for term, count in issue_by_term.most_common(20):
            print(f"  {term}: {count}")
    print(f"\nRapport: {output_path}")


if __name__ == '__main__':
    main()
