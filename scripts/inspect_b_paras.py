import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESIDUAL_ENGLISH_STRONG = re.compile(
    r"\b(had|was|were|said|asked|thought|looked|smiled|nodded|could|would|"
    r"cultivation|elder|sect|immortal|flying sword|spiritual energy|"
    r"suddenly|however|meanwhile|stared|frowned|murmured)\b",
    re.I,
)
RESIDUAL_ENGLISH_COMMON = re.compile(
    r"\b(the|this|that|these|those|and|but|with|from|into|about|after|before|"
    r"his|her|their|our|my|your|him|them|you|they|she|he|it|is|are|been|have|has)\b",
    re.I,
)

data = json.load(open('rapport-mqm-src.json', encoding='utf-8'))
b = [r for r in data if r['rank'] == 'B']
target_dir = pathlib.Path('src/content/chapters')

print(f"Inspection des {len(b)} chapitres...")
for r in b[:15]:
    p = target_dir / r['path']
    txt = p.read_text(encoding='utf-8', errors='replace')
    paras = [para.strip() for para in txt.split('\n\n') if para.strip() and not para.startswith('#')]
    for i, para in enumerate(paras):
        strong = RESIDUAL_ENGLISH_STRONG.findall(para)
        common = RESIDUAL_ENGLISH_COMMON.findall(para)
        words = para.split()
        if len(strong) >= 2 or (len(common) >= 5 and len(common) / max(1, len(words)) > 0.20):
            print(f"Ch. {r['chapter']} [p.{i}]: strong={strong} common={common}")
            print(f"   {para[:180]}")
