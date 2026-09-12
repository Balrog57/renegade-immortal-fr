import json
import re
import pathlib

data = json.load(open('rapport-renegade-v4.json', encoding='utf-8'))
b_and_c = [r for r in data if r['rank'] in ('B', 'C')]

RESIDUAL_ENGLISH_STRONG = re.compile(
    r"\b(had|was|were|said|asked|thought|looked|smiled|nodded|could|would|"
    r"cultivation|disciple|elder|sect|immortal|flying sword|spiritual energy|"
    r"suddenly|however|meanwhile|stared|frowned|murmured)\b",
    re.I,
)
RESIDUAL_ENGLISH_COMMON = re.compile(
    r"\b(the|this|that|these|those|and|but|with|from|into|about|after|before|"
    r"his|her|their|our|my|your|him|them|you|they|she|he|it|is|are|been|have|has)\b",
    re.I,
)

target_dir = pathlib.Path(r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\traduction\v4")

print(f"Total flagged files: {len(b_and_c)}")
for r in b_and_c[:15]:
    p = target_dir / r['path']
    txt = p.read_text(encoding='utf-8', errors='replace')
    paras = [para.strip() for para in txt.split('\n\n') if para.strip() and not para.startswith('#')]
    print(f"\n=== Ch. {r['chapter']} ({r['rank']}) : {r['path']} ===")
    for i, para in enumerate(paras):
        strong = RESIDUAL_ENGLISH_STRONG.findall(para)
        common = RESIDUAL_ENGLISH_COMMON.findall(para)
        words = para.split()
        if len(strong) >= 2 or (len(common) >= 5 and len(common) / max(1, len(words)) > 0.20):
            print(f"  [Para {i}] (Strong: {strong}, Common: {common})\n    Text: {para[:200]}")
