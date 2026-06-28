#!/usr/bin/env python3
"""
Phases B+C: Correction batch automatique des termes xianxia.
Lit les chapitres YELLOW du triage Phase A, vérifie chaque terme manquant
contre les 3 sources (EN, FR, NF), et applique des corrections conservatrices.

Types de corrections appliquées :
  1. Fautes d'accord genre/nombre (ex: "Secte Originel" -> "Secte Originelle")
  2. Normalisation de la capitalisation (ex: "purificateur du nirvana" -> "Purificateur du Nirvana")
  3. Remplacement de fautes de frappe évidentes (ex: "Purificateur Nirvana" -> "Purificateur du Nirvana")
  4. Correction "X Nirvana" incomplet → "X du Nirvana" (le "du" manquant)
  5. Remplacement des termes EN non traduits (Phase C: "Nirvana Scryer" → "Scruteur du Nirvana")

Usage: python scripts/fix-xianxia-terms.py [--dry-run] [--chapter N]

Output: reports/phase-c-corrections.json
"""

import io, json, os, re, sys, unicodedata
from collections import Counter
from pathlib import Path

# Ensure stdout supports Unicode on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")
NF_DIR = PROJECT_ROOT / "novelfrance"
GLOSSARY_PATH = PROJECT_ROOT / "scripts" / "glossary.json"
TRIAGE_PATH = PROJECT_ROOT / "reports" / "semantic-review-full.json"

# --- Gender agreement: (feminine_noun, wrong_masc_adj, correct_fem_adj) ---
# Applied when the masculine form follows a feminine noun
GENDER_FIXES = [
    ('secte', 'originel', 'originelle'),
    ('secte', 'ancien', 'ancienne'),
    ('secte', 'céleste', 'céleste'),  # already correct, no-op
    ('énergie', 'originel', 'originelle'),
    ('énergie', 'spirituel', 'spirituelle'),
    ('énergie', 'ancien', 'ancienne'),
    ('énergie', 'céleste', 'céleste'),
    ('mer', 'ancien', 'ancienne'),
    ('mer', 'entier', 'entière'),
    ('âme', 'originel', 'originelle'),
    ('âme', 'ancien', 'ancienne'),
    ('âme', 'spirituel', 'spirituelle'),
    ('planète', 'entier', 'entière'),
    ('flamme', 'ancien', 'ancienne'),
    ('bête', 'ancien', 'ancienne'),
    ('lignée', 'ancien', 'ancienne'),
    ('faille', 'spatial', 'spatiale'),
    ('pilule', 'ancien', 'ancienne'),
    ('technique', 'divin', 'divine'),
    ('aptitude', 'divin', 'divine'),
    ('porte', 'ancien', 'ancienne'),
    ('tribu', 'ancien', 'ancienne'),
    ('loi', 'ancien', 'ancienne'),
    ('loi', 'céleste', 'céleste'),
]

# --- "X Nirvana" incomplete → "X du Nirvana" patterns ---
# Matches: "Purificateur Nirvana" → "Purificateur du Nirvana", etc.
NIRVANA_MISSING_DU = [
    ('Purificateur Nirvana', 'Purificateur du Nirvana'),
    ('purificateur Nirvana', 'purificateur du Nirvana'),
    ('Scruteur Nirvana', 'Scruteur du Nirvana'),
    ('scruteur Nirvana', 'scruteur du Nirvana'),
    ('Briseur Nirvana', 'Briseur du Nirvana'),
    ('briseur Nirvana', 'briseur du Nirvana'),
]

# --- Phase C: Untranslated English terms left in FR body text ---
# These are xianxia terms that appear verbatim in English within the FR
# translation. Replace with the glossary-approved French equivalent.
# Format: (en_term, fr_replacement)
# Applied ONLY in body text (after frontmatter is stripped), case-insensitive,
# with word-boundary matching to avoid substring corruption.
UNTRANSLATED_EN_TERMS = [
    # Nirvana cultivation stages (highest-impact — 75 chapters total)
    ('Nirvana Scryer', 'Scruteur du Nirvana'),
    ('Nirvana Shatterer', 'Briseur du Nirvana'),
    ('Nirvana Cleanser', 'Purificateur du Nirvana'),
    # Empyrean cultivation stages
    ('Grand Empyrean', 'Grand Empyrée'),
    ('Empyrean Exalt', 'Exaltation Empyréenne'),
    ('Ascendant Empyrean', 'Empyrée Ascendant'),
    ('Golden Exalt', 'Exaltation Dorée'),
    # Yin/Yang stages
    ('Corporeal Yang', 'Yang Corporel'),
    ('Illusory Yin', 'Yin Illusoire'),
    # Void stages
    ('Arcane Void', 'Vide Arcanique'),
    ('Void Tribulant', 'Tribulation du Vide'),
    # Sects and concepts
    ('Origin Sect', 'Secte Originelle'),
    ('Immortal Astral Continent', 'Continent Astral Immortel'),
    ('Scatter Thunder Clan', 'Clan de la Foudre Dispersée'),
    ('Heavenly Fate Sect', 'Secte du Destin Céleste'),
    ('Fighting Evil Sect', 'Secte de la Lutte contre le Mal'),
    ('Soul Refining Sect', 'Secte de Raffinage des Âmes'),
    ('God Sect', 'Secte Divine'),
    ('Cloud Sky Sect', 'Secte du Ciel des Nuages'),
    # People — use common FR rendering rather than literal glossary
    ('Celestial Emperor', 'Empereur Céleste'),
    # Concepts
    ('spiritual energy', 'énergie spirituelle'),
    ('divine sense', 'sens divin'),
    ('joss flame', 'flamme joss'),
    ('celestial jade', 'jade céleste'),
    ('origin energy', 'énergie originelle'),
    ('star system', 'système stellaire'),
    ('spatial rift', 'faille spatiale'),
    ('divine retribution', 'châtiment divin'),
    ('Heaven Trampling', 'Foulée Céleste'),
    ('Soul Formation', "Formation de l'Âme"),
    ('Core Formation', 'Formation du Noyau'),
    ('Spirit Severing', "Séparation de l'Âme"),
    ('Nascent Soul', 'Âme Naissante'),
    ('Qi Condensation', 'Condensation du Qi'),
    ('heavenly tribulation', 'tribulation céleste'),
    ('celestial realm', 'royaume céleste'),
    ('mortal world', 'monde mortel'),
    ('immortal world', 'monde immortel'),
    # Single-word concepts (use \b boundary carefully)
    ('void', 'vide'),
    ('essence', 'essence'),
    ('cultivation', 'cultivation'),
    ('cultivator', 'cultivateur'),
    ('immortal', 'immortel'),
    ('mortal', 'mortel'),
    ('sect', 'secte'),
    ('clan', 'clan'),
    ('tribe', 'tribu'),
    ('realm', 'royaume'),
    ('domain', 'domaine'),
    ('continent', 'continent'),
    ('planet', 'planète'),
    ('jade', 'jade'),
    ('pill', 'pilule'),
    ('alchemy', 'alchimie'),
    ('karma', 'karma'),
    ('samsara', 'samsara'),
    ('fate', 'destin'),
    ('destiny', 'destinée'),
    ('beast', 'bête'),
    ('soul', 'âme'),
    ('dao', 'Dao'),
    ('celestial', 'céleste'),
    ('ancient', 'ancien'),
    ('formation', 'formation'),
    ('bloodline', 'lignée'),
    ('seal', 'sceau'),
    ('array', 'matrice'),
    ('demon', 'démon'),
    ('devil', 'diable'),
    ('law', 'loi'),
]

# Single-word terms that should NOT be auto-replaced because they would
# produce too many false positives (common English words that happen to
# also be xianxia glossary terms)
SKIP_SINGLE_WORD_REPLACE = {
    'void',      # "void" appears in English code contexts, not just as concept
    'soul',      # "soul" sometimes used in English names, not just as term
    'dao',       # "dao" the name, not just concept
    'fate',      # common English word
    'ancient',   # adjective, too broad
    'formation', # common English word
    'seal',      # common English word
    'array',     # common English word
    'law',       # common English word
    'jade',      # common in names
    'celestial', # adjective, too broad
    'sect',      # FR uses "Sect" as proper noun (e.g. "Sect d'Origine")
    'immortal',  # FR uses "Immortel" naturally, not as borrowed term
    'mortal',    # FR uses "mortel" naturally
    'demon',     # FR uses "démon" naturally
    'devil',     # FR uses "diable"/"démon" naturally
    'clan',      # FR uses "Clan" as proper noun
    'tribe',     # FR uses "tribu" naturally
    'realm',     # FR uses "royaume" naturally
    'domain',    # FR uses "domaine" naturally
    'continent', # FR uses "continent" naturally
    'planet',    # FR uses "planète" naturally
    'pill',      # FR uses "pilule" naturally
    'alchemy',   # FR uses "alchimie" naturally
    'karma',     # same word in both languages
    'samsara',   # same word in both languages
    'destiny',   # common English word, FR uses "destinée"
    'beast',     # FR uses "bête" naturally
    'bloodline', # FR uses "lignée" naturally
    'cultivation', # FR uses "cultivation" naturally (same word)
    'cultivator',  # FR uses "cultivateur" naturally
    'essence',     # same word in both languages
}

# --- Spelling/Capitalization fixes for glossary terms ---
SPELLING_FIXES = [
    # Nirvana capitalization
    ('Purificateur du nirvana', 'Purificateur du Nirvana'),
    ('purificateur du nirvana', 'purificateur du Nirvana'),
    ('Scruteur du nirvana', 'Scruteur du Nirvana'),
    ('scruteur du nirvana', 'scruteur du Nirvana'),
    ('Briseur du nirvana', 'Briseur du Nirvana'),
    ('briseur du nirvana', 'briseur du Nirvana'),
    # Accent on Âme
    ('Ame Naissante', 'Âme Naissante'),
    ('ame naissante', 'âme naissante'),
    ('Ame naissante', 'Âme naissante'),
    ('Ame Naissante', 'Âme Naissante'),
    ('l\'Ame Naissante', 'l\'Âme Naissante'),
    # Nirvana Scryer alternatives
    ('Nettoyage du Nirvana', 'Purificateur du Nirvana'),
    ('Nettoyage du nirvana', 'Purificateur du Nirvana'),
    ('nettoyage du nirvana', 'purificateur du Nirvana'),
    # Secte Originel → Secte Originelle (covered by gender_agreement instead)
    # Formation de l'Ame → Formation de l'Âme
    ('Formation de l\'Ame', 'Formation de l\'Âme'),
    ('formation de l\'ame', 'formation de l\'âme'),
    ('Transformation de l\'Ame', 'Transformation de l\'Âme'),
    ('transformation de l\'ame', 'transformation de l\'âme'),
    ('Séparation de l\'Ame', 'Séparation de l\'Âme'),
    ('séparation de l\'ame', 'séparation de l\'âme'),
    ('séparation de l\'âme', 'séparation de l\'âme'),  # already correct
    # Fléau Celeste → Fléau Céleste
    ('Fléau Celeste', 'Fléau Céleste'),
    ('fléau celeste', 'fléau céleste'),
    # Tribulation Celeste → Tribulation Céleste
    ('Tribulation Celeste', 'Tribulation Céleste'),
    ('tribulation celeste', 'tribulation céleste'),
    # Mer des Demons → Mer des Démons (missing accent)
    ('Mer des Demons', 'Mer des Démons'),
    ('mer des demons', 'mer des démons'),
    ('Mer des démons', 'Mer des Démons'),
]

# --- Terms where FR uses a close variant that should be accepted ---
# These are terms where the deep-review detects them as "missing" but the FR
# actually uses a perfectly valid alternative translation.
# Format: (en_term, fr_acceptable_alternatives)
VALID_FR_ALTERNATIVES = {
    # FR uses "Mer des Diables" instead of "Mer des Démons" (devil→diable is valid)
    'Sea of Devils': ['mer des diables'],
    # FR often uses "cultivateur" where EN says "immortal"
    'immortal': ['cultivateur', 'pratiquant', 'cultivant'],
    # FR often uses "mortel" but also "simple mortel", "être humain"
    'mortal': ['mortel', 'mortelle', 'être humain', 'humain'],
    # FR uses "réseau", "formation" instead of "matrice" for array
    'array': ['réseau', 'formation', 'cercle'],
    # FR uses verb "sceller" instead of noun "sceau"
    'seal': ['sceller', 'scelle', 'scellé', 'scellée', 'scellés', 'scellées', 'scellement'],
    # FR uses "esprit", "conscience" instead of "âme"
    'soul': ['esprit', 'conscience', 'âmes'],
    # FR uses various terms for "beast"
    'beast': ['bêtes', 'bête', 'créature', 'créatures', 'animal', 'animaux'],
    # FR uses "royaume" but also "domaine" for "domain"
    'domain': ['domaine', 'région', 'territoire'],
    # FR uses "énergie d'origine" for "origin energy"
    'origin energy': ['énergie d\'origine', 'énergie originelle', 'énergie primordiale'],
    # FR uses "trésor" or "artefact" for magic treasure
    'magic treasure': ['trésor', 'artefact', 'objet magique', 'trésors'],
    # FR uses "technique" or "aptitude" for divine ability
    'divine ability': ['technique divine', 'aptitude', 'capacité', 'pouvoir'],
    # FR uses "cultivateur corporel" for body cultivator
    'body cultivator': ['cultivateur corporel', 'cultivateur de corps'],
    # FR uses "voie" for dao
    'dao': ['voie', 'dao', 'principe'],
    # FR uses "loi" for "law" but also "principe"
    'law': ['loi', 'principe', 'règle', 'lois'],
    # FR uses "démon" for devil (glossary alias already in V6)
    'devil': ['démon', 'démons', 'diables', 'démoniaque'],
    # FR uses "bête spirituelle" and variants
    'spirit beast': ['bête spirituelle', 'bêtes spirituelles', 'animal spirituel', 'créature spirituelle',
                     'bête spirituel', 'bête spirituels'],
    # FR uses "condensation du qi" - check for just "condensation" + context
    'Qi Condensation': ['condensation du qi', 'condensation du Qi'],
    # FR often uses partial translations for cultivation stages
    'ancient god': ['dieu ancien', 'ancien dieu', 'dieux anciens', 'anciens dieux'],
    'ancient devil': ['diable ancien', 'ancien diable', 'diables anciens', 'anciens diables'],
    'ancient demon': ['démon ancien', 'ancien démon', 'démons anciens', 'anciens démons'],
    # FR uses "néant" for "void" in some contexts
    'void': ['vide', 'néant', 'néant absolu', 'vide absolu'],
    # FR uses alternate terms for various concepts
    'celestial jade': ['jade céleste', 'pierre céleste', 'jade spirituel'],
    'star system': ['système stellaire', 'système d\'étoiles', 'système solaire'],
    'spatial rift': ['faille spatiale', 'déchirure spatiale', 'fissure spatiale'],
    'divine retribution': ['châtiment divin', 'punition divine', 'rétribution divine'],
    'magic treasure': ['trésor magique', 'trésor', 'artefact', 'objet magique', 'trésors'],
    'divine ability': ['aptitude divine', 'capacité divine', 'pouvoir divin', 'technique divine'],
    # FR uses "énergie d'origine" more often than "énergie originelle"
    'origin energy': ['énergie d\'origine', 'énergie originelle', 'énergie primordiale',
                      'énergie d\'origine du monde'],
    # FR uses "Sect d'Origine" instead of "Secte Originelle"
    'Origin Sect': ['secte originelle', 'sect d\'origine', 'secte de l\'origine'],
    # FR uses "l'All-Seer", "Tian Yun Zi" interchangeably
    'All-Seer': ['tian yun zi', 'l\'all-seer', 'le devin'],
}


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_body(path):
    """Read chapter body text, stripping YAML frontmatter."""
    if not path or not os.path.exists(str(path)):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if str(path).endswith('.md') and content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]
    return content.strip()


def read_full_file(path):
    """Read entire file including frontmatter."""
    if not path or not os.path.exists(str(path)):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_full_file(path, content):
    """Write entire file."""
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def build_en_map():
    """Map chapter number → EN .txt path."""
    en_map = {}
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})', f)
                if m:
                    en_map[int(m.group(1))] = Path(root) / f
    return en_map


def build_fr_map():
    """Map chapter number → FR .md path."""
    fr_map = {}
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    fr_map[int(m.group(1))] = Path(root) / f
    return fr_map


def build_nf_map():
    """Map chapter number → NF .md path."""
    nf_map = {}
    if NF_DIR.exists():
        for f in os.listdir(NF_DIR):
            if f.endswith('.md'):
                m = re.match(r'ch(\d{4})', f)
                if m:
                    nf_map[int(m.group(1))] = NF_DIR / f
    return nf_map


def accent_normalize(text):
    """Remove accents for lenient comparison."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def word_boundary_match(text, term):
    """Check if term appears as a whole word/phrase in text. Case-insensitive."""
    term_lower = term.lower()
    text_lower = text.lower()
    if len(term_lower) <= 5:
        return bool(re.search(r'\b' + re.escape(term_lower) + r'\b', text_lower))
    else:
        return term_lower in text_lower


def search_lenient(fr_text, search_terms):
    """
    Search for any search_term in fr_text with multi-level leniency.
    Returns (found, matched_term, match_type, context) or (False, None, None, None).
    
    Levels:
      1. Exact lowercase substring
      2. Word-boundary match
      3. Accent-insensitive
      4. Variants from VALID_FR_ALTERNATIVES
    """
    fr_lower = fr_text.lower()
    
    for term in search_terms:
        term_lower = term.lower()
        
        # Level 1: exact substring
        if term_lower in fr_lower:
            idx = fr_lower.index(term_lower)
            ctx = fr_lower[max(0, idx-30):idx+len(term_lower)+30]
            return True, term, 'exact', ctx
        
        # Level 2: word boundary (for short terms)
        if len(term_lower) <= 6:
            m = re.search(r'\b' + re.escape(term_lower) + r'\b', fr_lower)
            if m:
                ctx = fr_lower[max(0, m.start()-30):m.end()+30]
                return True, term, 'word_boundary', ctx
    
    # Level 3: accent-insensitive
    fr_norm = accent_normalize(fr_text).lower()
    for term in search_terms:
        term_norm = accent_normalize(term).lower()
        if len(term_norm) <= 5:
            if re.search(r'\b' + re.escape(term_norm) + r'\b', fr_norm):
                return True, term, 'accent_insensitive', '[accent-insensitive]'
        else:
            if term_norm in fr_norm:
                return True, term, 'accent_insensitive', '[accent-insensitive]'
    
    return False, None, None, None


def verify_term_in_en(en_text, en_term):
    """Check that en_term actually appears in EN source."""
    return word_boundary_match(en_text, en_term)


def get_glossary_aliases(entry):
    """Get all FR equivalents for a glossary entry, including aliases."""
    equivs = [entry['fr']]
    if 'aliases' in entry:
        equivs.extend(entry['aliases'])
    return list(dict.fromkeys(equivs))  # dedup, preserve order


def find_gender_fixes(fr_text):
    """Find gender agreement errors using GENDER_FIXES patterns.
    Returns list of (wrong_phrase, correct_phrase)."""
    results = []
    for noun, masc_end, fem_end in GENDER_FIXES:
        if masc_end == fem_end:
            continue
        pattern = re.compile(
            r'\b(' + re.escape(noun) + r')\s+(' + re.escape(masc_end) + r')\b',
            re.IGNORECASE
        )
        for m in pattern.finditer(fr_text):
            wrong = m.group(0)
            # Preserve capitalization of the first word
            correct_first = m.group(1)[0].upper() + m.group(1)[1:] if m.group(1)[0].isupper() else m.group(1)
            correct = correct_first + ' ' + fem_end
            # Preserve capitalization of the second word if it was capitalized
            if m.group(2)[0].isupper() and fem_end[0].islower():
                correct = correct_first + ' ' + fem_end[0].upper() + fem_end[1:]
            if wrong != correct:
                results.append((wrong, correct))
    return results


def find_nirvana_fixes(fr_text):
    """Find "X Nirvana" → "X du Nirvana" fixes."""
    results = []
    # General pattern: any French word followed by "Nirvana" should have "du"
    pattern = re.compile(r'(purificateur|scruteur|briseur)\s+nirvana', re.IGNORECASE)
    for m in pattern.finditer(fr_text):
        wrong = m.group(0)
        prefix = m.group(1)
        # Preserve capitalization
        if prefix[0].isupper():
            correct = prefix.capitalize() + ' du Nirvana'
        else:
            correct = prefix + ' du Nirvana'
        if wrong != correct:
            results.append((wrong, correct))
    return results


def find_spelling_fixes(fr_text):
    """Find common spelling/capitalization issues."""
    results = []
    for wrong, correct in SPELLING_FIXES:
        if wrong in fr_text:
            results.append((wrong, correct))
    return results


def find_what_fr_uses(fr_text, en_term):
    """
    For a genuinely missing term, try to determine what the FR text uses instead.
    Returns list of candidate replacements found.
    """
    fr_lower = fr_text.lower()
    candidates = []
    
    # Check VALID_FR_ALTERNATIVES for known alternatives
    if en_term in VALID_FR_ALTERNATIVES:
        for alt in VALID_FR_ALTERNATIVES[en_term]:
            if word_boundary_match(fr_text, alt):
                candidates.append({'found': alt, 'type': 'known_alternative'})
    
    # For compound terms, check if parts appear individually
    en_words = en_term.lower().split()
    if len(en_words) >= 2:
        parts_found = []
        for w in en_words:
            if len(w) > 3 and word_boundary_match(fr_text, w):
                parts_found.append(w)
        if parts_found and len(parts_found) >= len(en_words) * 0.5:
            candidates.append({
                'found': ', '.join(parts_found),
                'type': 'partial_words',
                'note': f'Mots individuels trouvés: {parts_found}'
            })
    
    return candidates


def process_chapter(ch_num, fr_path, en_path, nf_path, glossary, triage_entry, dry_run):
    """
    Process a single YELLOW chapter.
    Returns (applied_fixes, manual_review, skipped, false_positives_glossary).
    """
    en_text = read_body(en_path) if en_path else ""
    fr_full = read_full_file(fr_path)
    fr_body = read_body(fr_path)
    nf_text = read_body(nf_path) if nf_path else ""
    
    applied = []
    manual = []
    skipped = []
    glossary_additions = []  # Suggested alias additions for false positives
    
    # Collect all missing terms from xianxia_terms_missing issues
    missing_issues = [
        i for i in triage_entry['issues']
        if i['type'] == 'xianxia_terms_missing' and 'missing_terms' in i
    ]
    
    if not missing_issues:
        return applied, manual, skipped, glossary_additions
    
    all_missing = []
    seen = set()
    for issue in missing_issues:
        for t in issue['missing_terms']:
            if t['en_term'] not in seen:
                seen.add(t['en_term'])
                all_missing.append(t)
    
    # === PHASE 1: Re-verify each missing term ===
    for term_info in all_missing:
        en_term = term_info['en_term']
        gl_entry = glossary.get(en_term, {})
        expected_fr = gl_entry.get('fr', term_info.get('expected_fr', '?'))
        category = gl_entry.get('category', term_info.get('category', 'unknown'))
        
        if not gl_entry:
            skipped.append({
                'en_term': en_term, 'expected_fr': expected_fr,
                'reason': 'Terme absent du glossaire', 'verdict': 'skip'
            })
            continue
        
        # Step 1: Re-verify EN presence
        if not verify_term_in_en(en_text, en_term):
            skipped.append({
                'en_term': en_term, 'expected_fr': expected_fr,
                'reason': 'Terme non trouvé dans EN (faux positif deep-review)',
                'verdict': 'skip'
            })
            continue
        
        # Step 2: Re-verify FR absence with lenient matching
        equivs = get_glossary_aliases(gl_entry)
        found, matched, match_type, ctx = search_lenient(fr_body, equivs)
        
        if found:
            skipped.append({
                'en_term': en_term, 'expected_fr': expected_fr,
                'found_in_fr': matched, 'match_type': match_type,
                'context': ctx,
                'reason': f'Terme présent en FR ({match_type}: "{matched}") — faux positif deep-review',
                'verdict': 'false_positive',
                'suggested_alias': matched if matched.lower() not in [e.lower() for e in equivs] else None,
            })
            continue
        
        # Step 3: Check NF for reference (T1-T6 only)
        nf_ref = None
        if nf_text and triage_entry.get('nf_reliable', False):
            nf_found, nf_matched, _, nf_ctx = search_lenient(nf_text, equivs)
            if nf_found:
                nf_ref = {'term': nf_matched, 'context': nf_ctx}
        
        # Step 4: Try to find what FR uses instead
        fr_alternatives = find_what_fr_uses(fr_body, en_term)
        
        verdict = 'genuinely_missing'
        if fr_alternatives:
            # Check if any alternative is a VALID alternative
            has_valid = any(
                alt['type'] == 'known_alternative' for alt in fr_alternatives
            )
            verdict = 'terminology_variant' if has_valid else 'genuinely_missing'
        
        manual.append({
            'en_term': en_term,
            'expected_fr': expected_fr,
            'category': category,
            'verdict': verdict,
            'fr_alternatives': fr_alternatives,
            'nf_reference': nf_ref,
            'suggestion': (
                f'FR utilise déjà: {fr_alternatives[0]["found"]}'
                if fr_alternatives else
                f'Terme "{en_term}" ({expected_fr}) absent du FR — à traduire manuellement'
            ),
        })
    
    # === PHASE 2: Apply conservative auto-fixes ===
    fr_working = fr_full
    applied_raw = []  # Collect all fixes, dedup at the end
    seen_fix_keys = set()  # Global dedup key: (type, before, after)
    
    def record_fix(ftype, before, after):
        key = (ftype, before, after)
        if key not in seen_fix_keys and before != after and before in fr_working:
            seen_fix_keys.add(key)
            applied_raw.append((ftype, before, after))
            return True
        return False
    
    # 2a: Nirvana "X Nirvana" → "X du Nirvana" (generalized, handles hyphens too)
    # Patterns: "Purificateur Nirvana", "Briseur Nirvana", "Brise-Nirvana" etc.
    nirvana_patterns = [
        (r'(purificateur|scruteur|briseur)[\s-]+nirvana', r'\1 du Nirvana'),
        (r'(Purificateur|Scruteur|Briseur)[\s-]+Nirvana', r'\1 du Nirvana'),
    ]
    for pattern_str, replacement in nirvana_patterns:
        for m in re.finditer(pattern_str, fr_working, re.IGNORECASE):
            wrong = m.group(0)
            # Build the correct form preserving capitalization
            prefix = m.group(1)
            correct = replacement.replace(r'\1', prefix)
            # Capitalize first letter if original was capitalized
            if wrong[0].isupper() and correct[0].islower():
                correct = correct[0].upper() + correct[1:]
            if record_fix('nirvana_missing_du', wrong, correct):
                fr_working = fr_working.replace(wrong, correct, 1)
    
    # 2b: Gender agreement errors
    gender_fixes = find_gender_fixes(fr_working)
    for wrong, correct in gender_fixes:
        if record_fix('gender_agreement', wrong, correct):
            fr_working = fr_working.replace(wrong, correct)
    
    # 2c: Spelling/capitalization fixes
    typo_fixes = find_spelling_fixes(fr_working)
    for wrong, correct in typo_fixes:
        if record_fix('spelling', wrong, correct):
            fr_working = fr_working.replace(wrong, correct)
    
    # 2d: Untranslated English terms → French glossary equivalent (Phase C)
    # Only apply to body text (after frontmatter) to avoid corrupting
    # the 'en:' metadata field which references the original English title.
    if '---' in fr_working:
        fm_parts = fr_working.split('---', 2)
        if len(fm_parts) >= 3:
            frontmatter = fm_parts[1]
            body = fm_parts[2]
        else:
            frontmatter = ''
            body = fr_working
    else:
        frontmatter = ''
        body = fr_working
    
    body_modified = body
    untranslated_fixes_applied = 0
    for en_term, fr_term in UNTRANSLATED_EN_TERMS:
        # Skip single-word terms that are too risky
        if ' ' not in en_term and en_term.lower() in SKIP_SINGLE_WORD_REPLACE:
            continue
        
        # Build word-boundary regex for case-insensitive replacement
        # Use \b for whole-word matching on single-word terms,
        # but not for multi-word (to allow "du Nirvana Scryer" match)
        if ' ' not in en_term:
            pattern = re.compile(r'\b' + re.escape(en_term) + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(en_term), re.IGNORECASE)
        
        # Only replace if the EN term actually appears in body
        if not pattern.search(body_modified):
            continue
        
        # Count occurrences for reporting
        matches = list(pattern.finditer(body_modified))
        if not matches:
            continue
        
        # Replace all occurrences, preserving case of first letter
        for m in reversed(matches):  # Reverse to preserve positions
            original = m.group(0)
            # Preserve first-letter capitalization
            if original[0].isupper():
                replacement = fr_term[0].upper() + fr_term[1:]
            else:
                replacement = fr_term[0].lower() + fr_term[1:]
            
            # Don't replace if identical
            if original == replacement:
                continue
            
            fix_key = ('untranslated_en', original, replacement)
            if fix_key not in seen_fix_keys:
                seen_fix_keys.add(fix_key)
                applied_raw.append(('untranslated_en', original, replacement))
        
        # Apply replacements
        body_modified = pattern.sub(
            lambda m: (fr_term[0].upper() + fr_term[1:]
                       if m.group(0)[0].isupper()
                       else fr_term[0].lower() + fr_term[1:]),
            body_modified
        )
    
    # Reassemble if body changed
    if body_modified != body:
        if frontmatter:
            fr_working = '---' + frontmatter + '---' + body_modified
        else:
            fr_working = body_modified
    
    # Build final applied list from deduped fixes
    applied = [{'type': t, 'before': b, 'after': a} for t, b, a in applied_raw]
    
    # Write if not dry-run and fixes applied
    if applied and not dry_run:
        write_full_file(fr_path, fr_working)
    
    return applied, manual, skipped, glossary_additions


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Phase B: Fix xianxia terms in YELLOW chapters')
    parser.add_argument('--dry-run', action='store_true', help='Ne pas modifier les fichiers')
    parser.add_argument('--chapter', type=int, help='Traiter un seul chapitre (debug)')
    parser.add_argument('--limit', type=int, default=0, help='Limiter le nombre de chapitres (0=tous)')
    parser.add_argument('--output', type=str, default='reports/phase-c-corrections.json', help='Rapport')
    args = parser.parse_args()
    
    print("=" * 70)
    print("Phases B+C: Correction batch des termes xianxia (YELLOW chapters)")
    print("=" * 70)
    
    # Load data
    print("\n[1/6] Chargement des données...")
    glossary = load_json(GLOSSARY_PATH)
    triage_data = load_json(TRIAGE_PATH)
    print(f"  Glossaire: {len(glossary)} termes")
    print(f"  Triage: {triage_data['total_reviewed']} chapitres")
    ts = triage_data.get('triage_summary', {})
    print(f"  Résumé triage: RED={ts.get('RED',0)} YELLOW={ts.get('YELLOW',0)} GREEN={ts.get('GREEN',0)}")
    
    en_map = build_en_map()
    fr_map = build_fr_map()
    nf_map = build_nf_map()
    print(f"  Sources: EN={len(en_map)} FR={len(fr_map)} NF={len(nf_map)}")
    
    # Filter YELLOW chapters
    cr = triage_data['chapter_results']
    yellow_chapters = sorted(
        int(k) for k, v in cr.items()
        if isinstance(v, dict) and v.get('triage') == 'YELLOW'
    )
    
    if args.chapter:
        yellow_chapters = [args.chapter]
    if args.limit > 0:
        yellow_chapters = yellow_chapters[:args.limit]
    
    n_yellow = len(yellow_chapters)
    print(f"  Chapitres YELLOW à traiter: {n_yellow}")
    
    # Process
    print(f"\n[2/6] Analyse et correction de {n_yellow} chapitres...")
    
    report = {
        'phase': 'C',
        'description': 'Correction batch xianxia pour chapitres YELLOW + untranslated EN replacements',
        'dry_run': args.dry_run,
        'total_yellow': n_yellow,
        'chapters_processed': 0,
        'chapters_with_fixes': 0,
        'total_fixes': 0,
        'total_manual': 0,
        'total_skipped': 0,
        'fixes_by_type': {},
        'per_chapter': {},
    }
    
    fixes_counter = Counter()
    
    for idx, ch_num in enumerate(yellow_chapters):
        if (idx + 1) % 50 == 0 or idx == 0:
            pct = (idx + 1) / n_yellow * 100 if n_yellow > 0 else 0
            print(f"  [{idx+1}/{n_yellow}] {pct:.0f}% - ch{ch_num}...")
        
        fr_path = fr_map.get(ch_num)
        en_path = en_map.get(ch_num)
        nf_path = nf_map.get(ch_num)
        
        triage_entry = cr.get(str(ch_num)) or cr.get(ch_num, {})
        if not isinstance(triage_entry, dict):
            continue
        
        applied, manual, skipped, glossary_adds = process_chapter(
            ch_num, fr_path, en_path, nf_path, glossary, triage_entry, args.dry_run
        )
        
        report['chapters_processed'] += 1
        report['total_manual'] += len(manual)
        report['total_skipped'] += len(skipped)
        
        ch_report = {
            'tome': triage_entry.get('tome'),
            'fixes': len(applied),
            'manual_review': len(manual),
            'skipped': len(skipped),
        }
        
        if applied:
            report['chapters_with_fixes'] += 1
            report['total_fixes'] += len(applied)
            ch_report['fixes_detail'] = [
                {'type': f['type'], 'before': f['before'], 'after': f['after']}
                for f in applied
            ]
            for f in applied:
                fixes_counter[f['type']] += 1
        
        if manual:
            ch_report['manual_review_detail'] = manual
        if skipped:
            ch_report['skipped_detail'] = skipped
        
        report['per_chapter'][str(ch_num)] = ch_report
    
    # Tome breakdown
    print(f"\n[3/6] Calcul des statistiques par tome...")
    tome_stats = defaultdict(lambda: {'chapters': 0, 'fixed': 0, 'manual': 0, 'skipped': 0})
    for ch_str, ch_r in report['per_chapter'].items():
        t = ch_r.get('tome', '?')
        tome_stats[t]['chapters'] += 1
        if ch_r['fixes'] > 0:
            tome_stats[t]['fixed'] += 1
        tome_stats[t]['manual'] += ch_r['manual_review']
        tome_stats[t]['skipped'] += ch_r['skipped']
    
    report['tome_breakdown'] = {str(k): dict(v) for k, v in sorted(tome_stats.items())}
    
    # Summary
    print(f"\n[4/6] Résumé:")
    print(f"  Chapitres traités:        {report['chapters_processed']}")
    print(f"  Chapitres avec correctifs: {report['chapters_with_fixes']}")
    print(f"  Corrections appliquées:   {report['total_fixes']}")
    print(f"  Termes à revoir:          {report['total_manual']}")
    print(f"  Faux positifs ignorés:    {report['total_skipped']}")
    
    if fixes_counter:
        print(f"\n  Corrections par type:")
        for ftype, count in fixes_counter.most_common():
            print(f"    - {ftype}: {count}")
    
    report['fixes_by_type'] = dict(fixes_counter)
    
    # Save report
    output_path = PROJECT_ROOT / args.output
    print(f"\n[5/6] Sauvegarde du rapport: {output_path}")
    save_json(report, output_path)
    
    # Next steps
    print(f"\n[6/6] ")
    if args.dry_run:
        print("  ⚠️  MODE DRY-RUN — aucune modification écrite.")
        print("  Relancez sans --dry-run pour appliquer les corrections.")
    else:
        print("  ✅ Corrections appliquées.")
        print("  Pour vérifier l'impact, relancez:")
        print("    python scripts/deep-review.py --full --output reports/semantic-review-full.json")
    
    print(f"\n  Rapport complet: {output_path}")
    
    return report


if __name__ == '__main__':
    from collections import defaultdict
    main()
