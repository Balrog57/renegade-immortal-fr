"""Fix T13 terminology: Grand Empereur → Grand Empyrée, Empereur Exalté → Exalt Empyréen, etc.

APPLIES ONLY TO T13 (tome-13) chapters. Body-only replacement (preserves frontmatter).
"""
import os, re

CHAPTERS_DIR = 'src/content/chapters/tome-13'
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
    # General Grand Empereur → Grand Empyrée
    ("Grand Empereur", "Grand Empyrée"),
    ("grand empereur", "grand empyrée"),
    
    # Empyrean Exalt → Exaltation Empyréenne / Exalt Empyréen
    ("Empereurs Exaltés", "Exaltations Empyréennes"),
    ("empereurs exaltés", "exaltations empyréennes"),
    ("Empereur Exalté", "Exaltation Empyréenne"),
    ("empereur exalté", "exaltation empyréenne"),
    
    # Ascendant Empyrean → Empyrée Ascendant
    ("Empereurs Ascendants", "Empyrées Ascendants"),
    ("empereurs ascendants", "empyrées ascendants"),
    ("Empereur Ascendant", "Empyrée Ascendant"),
    ("empereur ascendant", "empyrée ascendant"),
]

# Also fix specific compound patterns (must be done AFTER general fixes)
COMPOUND_FIXES = [
    # Fix cases where general replacement creates "Grand Empyrée Xuan Luo" (correct - already good)
    # No additional fixes needed
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
            # Show first few changes
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
