import pathlib
import re

target_dir = pathlib.Path(r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\traduction\v4")
files = list(target_dir.rglob("*.txt"))

sect_patterns = []

for f in files:
    txt = f.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"(?:[^\s]+\s+){0,3}\bSect\b(?:\s+[^\s]+){0,3}", txt, re.IGNORECASE)
    # filter out "Secte" or "sectes"
    isolated = [m for m in matches if re.search(r"\bsect\b", m, re.IGNORECASE)]
    if isolated:
        sect_patterns.extend(isolated[:5])

print(f"Sample of isolated 'Sect' matches (total matches seen): {len(sect_patterns)}")
for s in set(sect_patterns[:30]):
    print("  ->", s)
