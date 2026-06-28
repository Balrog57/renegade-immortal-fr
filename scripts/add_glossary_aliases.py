"""Add missing glossary aliases for T1-T7 variant translations."""
import json

with open('scripts/glossary.json', encoding='utf-8') as f:
    g = json.load(f)

additions = {
    'Qi Condensation': ['condensation de qi', 'Condensation de Qi'],
    'Sea of Devils': ['mer des diables', 'Mer des Diables'],
    'Spirit Severing': [
        "separation spirituelle", "Separation Spirituelle",
        "separation d'ame", "Separation d'Ame"
    ],
    'Cloud Sky Sect': [
        'secte ciel nuageux', 'Secte Ciel Nuageux'
    ],
    'Ji Realm': [
        'domaine ji', 'Domaine Ji', 'domaine de ji', 'Domaine de Ji'
    ],
    'Forsaken Immortal Clan': [
        'clan des immortels abandonnes', 'Clan des Immortels Abandonnes',
        'immortels abandonnes', 'Immortels Abandonnes'
    ],
    'divine retribution': [
        'tribulation divine', 'Tribulation Divine'
    ],
    'Fighting Evil Sect': [
        'secte du combat contre le mal', 'Secte du Combat contre le Mal',
        'combat contre le mal', 'Combat contre le Mal'
    ],
    'Nirvana Scryer': [
        'scryer du nirvana', 'Scryer du Nirvana'  # EN word left in FR - detect it as rendered
    ],
}

total_added = 0
for term, new_aliases in additions.items():
    if term in g:
        if 'aliases' not in g[term]:
            g[term]['aliases'] = []
        existing = set(g[term]['aliases'])
        added = 0
        for a in new_aliases:
            if a not in existing:
                g[term]['aliases'].append(a)
                added += 1
        if added > 0:
            print(f'{term}: +{added} aliases')
            total_added += added
    else:
        print(f'WARNING: {term} NOT IN GLOSSARY')

with open('scripts/glossary.json', 'w', encoding='utf-8') as f:
    json.dump(g, f, ensure_ascii=False, indent=2)

print(f'\nTotal: {total_added} aliases added')
