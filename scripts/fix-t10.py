#!/usr/bin/env python3
"""Fix T10: Secte Divin->Secte Divine, All-Seer->Tout-Voyant, body-only"""
import glob, os

T10_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'src', 'content', 'chapters', 'tome-10')

import_count = 0
secte_count = 0
allseer_count = 0

for fpath in sorted(glob.glob(os.path.join(T10_DIR, '*.md'))):
    fname = os.path.basename(fpath)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        continue

    body = parts[2]
    changed = False

    # Count "Secte Divin" in body
    n = body.count('Secte Divin')
    if n > 0:
        body = body.replace('Secte Divin', 'Secte Divine')
        changed = True
        secte_count += n

    # Fix "All-Seer" in body
    n2 = body.count('All-Seer')
    if n2 > 0:
        body = body.replace('All-Seer', 'Tout-Voyant')
        changed = True
        allseer_count += n2

    if changed:
        parts[2] = body
        new_content = '---'.join(parts)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'FIXED {fname} ({n} Secte, {n2} All-Seer)')
        import_count += 1

print(f'\nFiles modified: {import_count}')
print(f'Secte Divin replacements: {secte_count}')
print(f'All-Seer replacements: {allseer_count}')
