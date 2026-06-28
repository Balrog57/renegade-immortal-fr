"""Fix untranslated English 'Scryer' -> 'Scruteur' in T7 chapter body text."""
import os, re

CHAPTERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'content', 'chapters', 'tome-7')
PATTERN = re.compile(r'\bScryer du Nirvana\b')
REPLACEMENT = 'Scruteur du Nirvana'

count = 0
files_modified = []

for filename in sorted(os.listdir(CHAPTERS_DIR)):
    if not filename.endswith('.md'):
        continue
    filepath = os.path.join(CHAPTERS_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split frontmatter from body
    parts = content.split('---', 2)
    if len(parts) < 3:
        continue
    
    frontmatter = parts[1]
    body = parts[2]
    
    # Only fix in body, not frontmatter
    new_body, n = PATTERN.subn(REPLACEMENT, body)
    if n > 0:
        new_content = f'---{frontmatter}---{new_body}'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        count += n
        files_modified.append((filename, n))
        print(f'{filename}: {n} fixes')

print(f'\nTotal: {count} fixes in {len(files_modified)} files')
