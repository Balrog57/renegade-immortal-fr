"""Fix T11 terminology: Grand Empereur → Grand Empyrée, Secte Divin → Secte Divine,
All-Seer → Tout-Voyant (body), Daoïste Water → Daoïste de l'Eau.

APPLIES ONLY TO T11 (tome-11) chapters. Body-only replacement (preserves frontmatter).
"""
import os, re

CHAPTERS_DIR = 'src/content/chapters/tome-11'
DRY_RUN = False  # Set to True to preview without writing

# Fix patterns (ordered from longest to shortest to prevent partial matches)
FIXES = [
    # Plural
    ("Grands Empereurs Célestes", "Grands Empyrées"),
    ("grands empereurs célestes", "grands empyrées"),
    ("Grands Empereurs", "Grands Empyrées"),
    ("grands empereurs", "grands empyrées"),
    # Singular with qualifier
    ("Grand Empereur Céleste", "Grand Empyrée"),
    ("grand empereur céleste", "grand empyrée"),
    ("Grand Empereur Dao Yi", "Grand Empyrée Dao Yi"),
    ("grand empereur Dao Yi", "grand empyrée Dao Yi"),
    ("Grand Empereur Dao Antique", "Grand Empyrée Dao Antique"),
    ("grand empereur Dao Antique", "grand empyrée Dao Antique"),
    # General Grand Empereur → Grand Empyrée
    ("Grand Empereur", "Grand Empyrée"),
    ("grand empereur", "grand empyrée"),
    
    # Secte Divin → Secte Divine (gender agreement)
    ("Secte Divin", "Secte Divine"),
    
    # Daoïste Water → Daoïste de l'Eau (EN residual)
    ("Daoïste Water", "Daoïste de l'Eau"),
]

def fix_allseer_body(body):
    """Replace 'All-Seer' with 'Tout-Voyant' in body text, handling French article contractions.
    Must process in order: longest patterns first, then article cleanup."""
    seer_changes = 0
    
    # Phase 1: Replace specific article+All-Seer patterns (longest first)
    phase1 = [
        ("de l'All-Seer", "du Tout-Voyant"),
        ("d'All-Seer", "de Tout-Voyant"),
        ("L'All-Seer", "Le Tout-Voyant"),
        ("l'All-Seer", "le Tout-Voyant"),
    ]
    for old, new in phase1:
        c = body.count(old)
        if c > 0:
            body = body.replace(old, new)
            seer_changes += c
    
    # Phase 2: Replace bare "All-Seer" (remaining)
    c = body.count("All-Seer")
    if c > 0:
        body = body.replace("All-Seer", "Tout-Voyant")
        seer_changes += c
    
    # Phase 3: Fix French article contractions created by Phase 2
    # "de le Tout-Voyant" → "du Tout-Voyant"
    c = body.count(" de le Tout-Voyant")
    if c > 0:
        body = body.replace(" de le Tout-Voyant", " du Tout-Voyant")
    # "de Le Tout-Voyant" → "du Tout-Voyant" (sentence-start case)
    c = body.count(" de Le Tout-Voyant")
    if c > 0:
        body = body.replace(" de Le Tout-Voyant", " du Tout-Voyant")
    
    return body, seer_changes

def fix_chapter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split frontmatter from body
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f'  WARNING: No frontmatter found in {filepath}')
        return 0
    
    frontmatter = parts[1]
    body = parts[2]
    
    changes = 0
    original_body = body
    
    # 1. Apply word-replacement fixes (Grand Empereur→Grand Empyrée, Secte Divin→Secte Divine, Daoïste Water→Daoïste de l'Eau)
    for old, new in FIXES:
        count = body.count(old)
        if count > 0:
            body = body.replace(old, new)
            changes += count
    
    # 2. All-Seer → Tout-Voyant (in body only, handling article contractions)
    body, seer_changes = fix_allseer_body(body)
    changes += seer_changes
    
    if changes > 0:
        new_content = f'---{frontmatter}---{body}'
        
        if DRY_RUN:
            print(f'  Would apply {changes} changes to {os.path.basename(filepath)}')
            for old, new in FIXES:
                c = original_body.count(old)
                if c > 0:
                    print(f'    {old} -> {new} ({c}x)')
            if seer_changes > 0:
                print(f'    All-Seer -> Tout-Voyant ({seer_changes}x)')
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'  Fixed {changes} occurrences in {os.path.basename(filepath)}')
    else:
        pass  # No changes
    
    return changes

def main():
    files = sorted(os.listdir(CHAPTERS_DIR))
    total_changes = 0
    files_changed = 0
    
    for f in files:
        if f.startswith('.'): continue
        filepath = os.path.join(CHAPTERS_DIR, f)
        changes = fix_chapter(filepath)
        if changes > 0:
            total_changes += changes
            files_changed += 1
    
    print(f'\nTotal: {total_changes} changes in {files_changed}/{len(files)} files')

if __name__ == '__main__':
    main()
