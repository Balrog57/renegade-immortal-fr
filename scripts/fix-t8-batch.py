"""Phase C.6 — Batch fix T8: EN terms + Secte Divin + All-Seer.
Body-only replacement to protect frontmatter.
"""
import os, re, json, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
T8_DIR = PROJECT_ROOT / 'src' / 'content' / 'chapters' / 'tome-8'
DRY_RUN = False  # Set to True for preview

REPLACEMENTS = [
    # Nirvana cultivation stages (EN in body -> FR)
    (r'\bNirvana Scryer\b', 'Scruteur du Nirvana'),
    (r'\bNirvana Cleanser\b', 'Purificateur du Nirvana'),
    (r'\bNirvana Shatterer\b', 'Briseur du Nirvana'),

    # Illusory Yin / Corporeal Yang (less common but present)
    (r'\bIllusory Yin\b', 'Yin Illusoire'),
    (r'\bCorporeal Yang\b', 'Yang Corporel'),

    # All-Seer -> Tout-Voyant (if in body, not in frontmatter)
    (r'\bAll-Seer\b', 'Tout-Voyant'),
]

GENDER_FIX = ('Secte Divin', 'Secte Divine')  # Note: only match whole word to avoid "Divine"->"Divinee"

def process_chapter(path):
    """Read, fix body, write back."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f'  WARN: {path.name} - no frontmatter detected')
        return 0

    frontmatter = parts[1]
    body = parts[2]
    body_original = body

    fixes = 0
    for pattern, replacement in REPLACEMENTS:
        fixed, n = re.subn(pattern, replacement, body)
        if n > 0:
            body = fixed
            fixes += n

    # Gender fix: Secte Divin -> Secte Divine (must not match "Divine" already)
    # Use \bDivin\b to avoid matching "Divine"
    fixed, n = re.subn(r'Secte Divin\b', 'Secte Divine', body)
    if n > 0:
        body = fixed
        fixes += n

    if body != body_original:
        new_content = f'---{frontmatter}---{body}'
        if not DRY_RUN:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        return fixes
    return 0

def main():
    print(f'Phase C.6 — T8 Batch Fix {"(DRY RUN)" if DRY_RUN else "(LIVE)"}')
    print(f'Directory: {T8_DIR}')
    print()

    total_fixes = 0
    fixed_files = []
    for fpath in sorted(T8_DIR.glob('*.md')):
        n = process_chapter(fpath)
        if n > 0:
            total_fixes += n
            fixed_files.append((fpath.name, n))
            print(f'  {fpath.name}: {n} fixes')

    print(f'\n=== SUMMARY ===')
    print(f'Files modified: {len(fixed_files)}')
    print(f'Total fixes: {total_fixes}')

    # Report per-replacement type
    print(f'\nFix patterns:')
    print(f'  EN terms (Nirvana/Illusory/Corporeal): {len(REPLACEMENTS)} patterns')
    print(f'  Secte Divin -> Secte Divine: gender agreement')
    print(f'  All-Seer -> Tout-Voyant: EN->FR name')

if __name__ == '__main__':
    main()
