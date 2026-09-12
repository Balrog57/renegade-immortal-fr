import json
from collections import Counter

data = json.load(open('rapport-mqm-src.json', encoding='utf-8'))
b = [r for r in data if r['rank'] == 'B']
c = Counter([e.split(':')[0] for r in b for e in r['errors']])
print('Rang B error types:', c)
for r in b:
    print(f"Ch. {r['chapter']:4d} [{r['score']}]: {r['errors']}")
