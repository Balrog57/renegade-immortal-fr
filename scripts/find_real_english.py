import pathlib
import re

target_dir = pathlib.Path(r"\\100.116.197.25\Media\Livres\EBOOK\Renegade Immortal\traduction\v4")

# Real English indicators without French false friends
REAL_ENGLISH = re.compile(
    r"\b(had|was|were|said|asked|thought|looked|smiled|nodded|could|would|"
    r"flying sword|spiritual energy|"
    r"suddenly|however|meanwhile|stared|frowned|murmured)\b",
    re.I,
)

# Common english grammar words that are not French words
REAL_ENGLISH_GRAMMAR = re.compile(
    r"\b(the|this|that|these|those|with|from|into|about|after|before|"
    r"his|her|their|our|my|your|him|them|they|she|he|been|have)\b",
    re.I,
)

files = list(target_dir.rglob("*.txt"))
print(f"Total files in v4: {len(files)}")

real_untranslated = []

for f in files:
    txt = f.read_text(encoding="utf-8", errors="replace")
    paras = [p.strip() for p in txt.split("\n\n") if p.strip() and not p.startswith("#")]
    flagged_paras = []
    for i, p in enumerate(paras):
        strong = REAL_ENGLISH.findall(p)
        grammar = REAL_ENGLISH_GRAMMAR.findall(p)
        words = p.split()
        if len(strong) >= 2 or (len(grammar) >= 4 and len(grammar) / max(1, len(words)) > 0.15):
            flagged_paras.append((i, p, strong, grammar))
    if flagged_paras:
        real_untranslated.append((f, flagged_paras))

print(f"Files with real untranslated paragraphs: {len(real_untranslated)}")
for f, fps in real_untranslated:
    print(f"\nFile: {f.name}")
    for i, p, s, g in fps:
        print(f"  Para {i} (strong={s}, grammar={g}): {p[:120]}...")
