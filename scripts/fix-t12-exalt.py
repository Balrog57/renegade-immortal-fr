"""Fix T12 terminology: Part 2 — Exalt Céleste → Exaltation Empyrénée, etc.

Handles chapters that use "Exalt" instead of "Empereur" for the Empyrean stage.
APPLIES ONLY TO T12 (tome-12) chapters. Body-only replacement (preserves frontmatter).
"""
import os, re

CHAPTERS_DIR = 'src/content/chapters/tome-12'
DRY_RUN = False  # Set to True to preview without writing

# Fix patterns (ordered longest first)
FIXES = [
    # Plural forms
    ("Exalts Célestes", "Exaltations Empyréennes"),
    ("exalts célestes", "exaltations empyréennes"),
    ("Grands Exalts Célestes", "Grands Empyrées"),
    ("grands exalts célestes", "grands empyrées"),
    
    # Singular - "Grand Exalt Céleste" → "Grand Empyrée"
    ("Grand Exalt Céleste", "Grand Empyrée"),
    ("grand exalt céleste", "grand empyrée"),
    
    # "Exalt Céleste" → "Exaltation Empyréenne" 
    ("Exalt Céleste", "Exaltation Empyréenne"),
    ("exalt céleste", "exaltation empyréenne"),
]

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
    
    for old, new in FIXES:
        count = body.count(old)
        if count > 0:
            body = body.replace(old, new)
            changes += count
    
    if changes > 0:
        new_content = f'---{frontmatter}---{body}'
        
        if DRY_RUN:
            print(f'  Would apply {changes} changes to {os.path.basename(filepath)}')
            for old, new in FIXES:
                c = original_body.count(old)
                if c > 0:
                    print(f'    {old} -> {new} ({c}x)')
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
