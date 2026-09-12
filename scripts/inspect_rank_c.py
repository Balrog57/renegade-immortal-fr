import json
import re
import pathlib

data = json.load(open('rapport-renegade-v4.json', encoding='utf-8'))
c_list = [r for r in data if r['rank'] == 'C']

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

target_dir = pathlib.Path(r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\traduction\v4")

for r in c_list:
    p = target_dir / r['path']
    txt = p.read_text(encoding='utf-8', errors='replace')
    paras = [para.strip() for para in txt.split('\n\n') if para.strip() and not para.startswith('#')]
    print(f"\n==========================================")
    print(f"=== Ch. {r['chapter']} : {r['path']} ===")
    print(f"==========================================")
    for i, para in enumerate(paras):
        strong = RESIDUAL_ENGLISH_STRONG.findall(para)
        common = RESIDUAL_ENGLISH_COMMON.findall(para)
        disciple_count = len(re.findall(r'\bdisciple\b', para, re.I))
        words = para.split()
        if len(strong) >= 2 or (len(common) >= 5 and len(common) / max(1, len(words)) > 0.20):
            print(f"  [Para {i}] Strong: {strong} (disciple={disciple_count}), Common: {common}")
            print(f"    Text: {para[:180]}...")
