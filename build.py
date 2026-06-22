#!/usr/bin/env python3
"""
build.py — Génère le site multi-pages Renegade Immortal FR.
Output: _site/ (gitignored) + deployable at root via script.
"""
import os, json, re, shutil, sys, html as htmlmod, urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
PARTS = ROOT / 'build_parts'
TRADUCTION = ROOT / 'traduction'
WIKI = ROOT / 'wiki'
SITE = ROOT / '_site'

CSS = (PARTS / 'style.css').read_text(encoding='utf-8')
JS = (PARTS / 'app.js').read_text(encoding='utf-8')
CHAPTERS = json.loads((PARTS / 'chapters-data.json').read_text(encoding='utf-8'))
WIKI_PAGES = json.loads((PARTS / 'wiki-data.json').read_text(encoding='utf-8'))


def esc(s):
    return htmlmod.escape(str(s or ''), quote=True)


def slugify(s, maxlen=80):
    s = re.sub(r'[^\w\s-]', '', str(s).lower())
    s = re.sub(r'[\s_-]+', '-', s).strip('-')
    if len(s) > maxlen:
        s = s[:maxlen].rsplit('-', 1)[0]
    return s or 'x'


def book_slug(book_n, book_title):
    return f'book{book_n}-{slugify(book_title)}'


def chapter_path(book_n, book_title, n, title):
    return f'livre/{book_slug(book_n, book_title)}/{n:04d}-{slugify(title)}.html'


def page_html(title, body, base='', nav_active='', data_inline='', extra_css='', extra_js=''):
    if data_inline:
        js_init = f"window.__PAGE_DATA__ = {data_inline};"
        page_js = js_init + '\n' + JS.replace(
            "const CHAPTERS_DATA = JSON.parse(document.getElementById(\"chapters-data\").textContent);",
            "const CHAPTERS_DATA = (window.__PAGE_DATA__ && window.__PAGE_DATA__.chapters) || [];"
        ).replace(
            "const WIKI_DATA = JSON.parse(document.getElementById(\"wiki-data\").textContent);",
            "const WIKI_DATA = (window.__PAGE_DATA__ && window.__PAGE_DATA__.wiki) || [];"
        )
    else:
        page_js = JS.replace(
            "const CHAPTERS_DATA = JSON.parse(document.getElementById(\"chapters-data\").textContent);",
            "const CHAPTERS_DATA = (window.__PAGE_DATA__ && window.__PAGE_DATA__.chapters) || [];"
        ).replace(
            "const WIKI_DATA = JSON.parse(document.getElementById(\"wiki-data\").textContent);",
            "const WIKI_DATA = (window.__PAGE_DATA__ && window.__PAGE_DATA__.wiki) || [];"
        )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{esc(title)} — Renegade Immortal FR</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="preconnect" href="https://static.wikia.nocookie.net" />
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Noto+Serif:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet" />
<style>
{CSS}
{extra_css}
</style>
</head>
<body>
<header class="nav" role="banner">
  <div class="nav-inner">
    <a href="{base}index.html" class="brand" aria-label="Renegade Immortal FR — accueil">
      <span class="dot" aria-hidden="true"></span>
      <span>Renegade Immortal FR</span>
      <small>· Xian Ni · 仙逆</small>
    </a>
    <button class="nav-burger" id="nav-burger" aria-label="Ouvrir le menu" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <nav class="nav-tabs" id="nav-tabs" role="navigation" aria-label="Sections principales">
      <a href="{base}index.html" class="nav-tab{' is-active' if nav_active == 'home' else ''}">Accueil</a>
      <a href="{base}livre.html" class="nav-tab{' is-active' if nav_active == 'livre' else ''}">Livre</a>
      <a href="{base}chapitres.html" class="nav-tab{' is-active' if nav_active == 'chapters' else ''}">Chapitres</a>
      <a href="{base}personnages.html" class="nav-tab{' is-active' if nav_active == 'characters' else ''}">Personnages</a>
      <a href="{base}cultivation.html" class="nav-tab{' is-active' if nav_active == 'cultivation' else ''}">Cultivation</a>
      <a href="{base}sectes-clans.html" class="nav-tab{' is-active' if nav_active == 'sectes' else ''}">Sectes & Clans</a>
      <a href="{base}lieux.html" class="nav-tab{' is-active' if nav_active == 'lieux' else ''}">Lieux</a>
      <a href="{base}wiki.html" class="nav-tab{' is-active' if nav_active == 'wiki' else ''}">Wiki</a>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer>
  <div class="seal">Renegade Immortal FR</div>
  <div>Traduction communautaire non-officielle · Contenu via <a class="fandom-link" href="https://xian-ni.fandom.com/wiki/Xian_Ni_Wikia" target="_blank" rel="noopener">Xian Ni Fandom Wiki</a> (CC BY-SA) · <a href="{base}LICENSE.txt" class="fandom-link">MIT/CC0</a></div>
</footer>
<div class="gesture-hint" id="gesture-hint" role="dialog" aria-label="Cliquez pour activer le son">
  <div class="gesture-hint-inner">
    <div class="gesture-hint-glyph">仙</div>
    <div class="gesture-hint-title">Renegade Immortal</div>
    <div class="gesture-hint-text">Cliquez pour entrer dans le monde de Wang Lin — la musique d'ambiance s'activera.</div>
    <div class="gesture-hint-cta">
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
      <span>Entrer</span>
    </div>
  </div>
</div>
<div class="audio-dock" id="audio-dock" role="region" aria-label="Musique d'ambiance">
  <button class="audio-btn" id="audio-btn" aria-label="L'OST Xian Ni démarre automatiquement" aria-pressed="true">
    <svg id="icon-play" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
    <svg id="icon-pause" viewBox="0 0 24 24" fill="currentColor" style="display:none" aria-hidden="true"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>
  </button>
  <div class="audio-meta">
    <div class="title">OST Xian Ni</div>
    <div class="sub">All Instrument · ANimeMuzic</div>
  </div>
  <div class="audio-viz" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
  <input class="audio-vol" id="audio-vol" type="range" min="0" max="100" value="40" aria-label="Volume" />
</div>
<div id="yt-player-host"></div>
{extra_js}
<script>
{page_js}
</script>
</body>
</html>
"""


def write(path, content):
    full = SITE / path
    full.parent.mkdir(parents=True, exist_ok=True)
    path_str = str(full.resolve())
    if os.name == 'nt' and len(path_str) > 240:
        path_str = '\\\\?\\' + path_str
    with open(path_str, 'w', encoding='utf-8') as f:
        f.write(content)


# === DATA HELPERS ===
def categorize_wiki():
    buckets = {'personnages': [], 'cultivation': [], 'sectes': [], 'lieux': []}
    main_persos = {'Wang Lin', 'Situ Nan', 'Li Muwan', 'Li MuWan', 'Tuo Sen', 'All Seer', 'All-Seer',
                   'Sima Mo', 'Master Devil God', 'Zhou Yi', 'Wang Ping', 'Han Pao',
                   'Blood Ancestor', 'Soap', 'Ancient God'}
    for p in WIKI_PAGES:
        name = p['name']
        cats = set(c.lower() for c in p.get('categories', []))
        if name in main_persos or 'characters' in cats:
            buckets['personnages'].append(p)
        if 'cultivation' in cats or 'realms' in cats or 'techniques' in cats or 'spells' in cats:
            buckets['cultivation'].append(p)
        if 'sects' in cats or 'clan' in cats or 'organisations' in cats:
            buckets['sectes'].append(p)
        if 'locations' in cats or 'planets' in cats or 'continents' in cats or 'star system' in cats:
            buckets['lieux'].append(p)
    return buckets


def curate_top(bucket, n=20):
    def score(p):
        s = len(p.get('categories', []))
        for c in p.get('categories', []):
            cl = c.lower()
            if cl in ('characters', 'locations', 'sects'): s += 3
            if cl in ('cultivation', 'realms'): s += 2
        return s
    return sorted(bucket, key=score, reverse=True)[:n]


def find_image_for_page(page):
    img_dir = WIKI / 'images'
    if not img_dir.exists(): return ''
    name_lower = page['name'].lower()
    for f in img_dir.iterdir():
        if f.stem.lower() == name_lower:
            return f'wiki/images/{urllib.parse.quote(f.name)}'
    for f in img_dir.iterdir():
        if name_lower in f.stem.lower() or f.stem.lower() in name_lower:
            return f'wiki/images/{urllib.parse.quote(f.name)}'
    return ''


def load_main_characters():
    data_path = PARTS / 'data.json'
    if data_path.exists():
        return json.loads(data_path.read_text(encoding='utf-8'))
    return None


def parse_wiki_sections(content):
    """Parse Fandom page content into sections."""
    ovs = list(re.finditer(r'(?m)^Overview$', content))
    body_start = ovs[1].start() if len(ovs) >= 2 else (ovs[0].start() if ovs else 0)
    body = content[body_start:].replace(r'[\s*\n\s*]', '')
    blocks = [b.strip() for b in re.split(r'\n\n+', body) if b.strip()]
    KNOWN = {'Overview','Personality','Background','History','Appearance','Manhua','Trivia','Links and References','Cultivation','Techniques','Items','Relationships','Fights','Quotes','Image Gallery','Description','Legacy','Abilities','Powers and Abilities','Equipment','Weaknesses','Gallery','Quote'}
    def is_title(b):
        if b in KNOWN: return True
        if re.match(r'^Book \d+', b): return True
        if re.match(r'^Chapter \d+\b', b): return True
        if len(b) > 80: return False
        if re.search(r'[.!?,;]$', b): return False
        if not b[0].isupper(): return False
        if ':' in b: return False
        if re.match(r'^\d+(\.\d+)*$', b): return False
        if re.match(r'^\[\d+\]$', b): return False
        if re.search(r'[.!?,;]', b): return False
        return True
    sections = []
    current = None
    buf = []
    for b in blocks:
        if b == 'Overview' or is_title(b):
            if current and buf: sections.append((current, buf))
            current = b
            buf = []
        else:
            cleaned = re.sub(r'\[\d+\]', '', b)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if len(cleaned) > 40: buf.append(cleaned)
    if current and buf: sections.append((current, buf))
    return sections


# === PAGES ===
def build_home():
    body = """
  <section class="tab-panel is-active" id="panel-home">
    <canvas id="bg-canvas" aria-hidden="true"></canvas>
    <div class="hero hero--home">
      <div class="hero-text">
        <div class="eyebrow">Web Novel · Traduction française</div>
        <h1>Renegade Immortal</h1>
        <p class="lede">L'odyssée d'un jeune orphelin devenu démon, forgeant son destin entre ciel et terre, là où les mortels défient l'ordre des Immortels.</p>
        <div class="cover" role="img" aria-label="Couverture — Renegade Immortal">
          <div class="cover-frame" aria-hidden="true"></div>
          <span class="cover-corner tl" aria-hidden="true"></span>
          <span class="cover-corner tr" aria-hidden="true"></span>
          <span class="cover-corner bl" aria-hidden="true"></span>
          <span class="cover-corner br" aria-hidden="true"></span>
          <div class="cover-art">
            <div>
              <div class="glyph">逆<br/>天</div>
              <div class="glyph-sub">Renegade Immortal</div>
            </div>
          </div>
        </div>
      </div>
      <div>
        <div class="eyebrow">L'œuvre</div>
        <h2>Le roman</h2>
        <div class="meta-grid" role="list">
          <div class="meta" role="listitem"><div class="k">Auteur</div><div class="v">Er Gen · 耳根</div></div>
          <div class="meta" role="listitem"><div class="k">Statut</div><div class="v is-status">Terminé · 2088 chapitres</div></div>
          <div class="meta" role="listitem"><div class="k">Titres alternatifs</div><div class="v">Xian Ni · 仙逆</div></div>
          <div class="meta" role="listitem"><div class="k">Genres</div><div class="v">Action · Fantaisie · Arts Martiaux · Xianxia</div></div>
        </div>
        <div class="synopsis">
          <h2>Synopsis</h2>
          <p>Wang Lin n'est qu'un jeune garçon lorsque sa vie bascule. Orphelin des montagnes, rejeté par le monde des cultivateurs, il ne possède qu'une seule chose : une obstination tranquille, forgée dans le silence et l'adversité.</p>
          <p>De la Condensation du Qi aux royaumes supérieurs, de la Perle défiant les Cieux aux secrets des anciens, Wang Lin deviendra bien plus qu'un Immortel — il deviendra celui que l'on n'ose pas nommer. Car dans ce monde, <em>le ciel n'est pas une limite, mais un adversaire</em>.</p>
          <a href="livre.html" class="btn-primary">Commencer la lecture →</a>
        </div>
      </div>
    </div>
  </section>
"""
    extra_css = """
  .hero--home { position: relative; z-index: 1; }
  #bg-canvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: 0.5; }
  .btn-primary {
    display: inline-block; margin-top: 14px; padding: 12px 24px;
    border: 1px solid var(--crimson-dim);
    background: linear-gradient(180deg, var(--crimson), var(--crimson-dim));
    color: #fff; font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: .2em; text-transform: uppercase;
    border-radius: var(--r-md);
    box-shadow: 0 0 0 1px rgba(255,255,255,.05) inset, 0 8px 24px -8px rgba(179,38,30,.6);
  }
  .btn-primary:hover { transform: translateY(-1px); }
"""
    extra_js = '<script src="home-bg.js" defer></script>'
    html = page_html('Accueil', body, nav_active='home', extra_css=extra_css, extra_js=extra_js)
    write('index.html', html)
    print('  ✓ index.html (animated bg)')


def build_livre():
    by_book = {}
    for c in CHAPTERS:
        by_book.setdefault(c['book'], []).append(c)
    book_tiles = ''
    for b in sorted(by_book.keys()):
        chs = by_book[b]
        first = chs[0]
        link = chapter_path(b, first['bookTitle'], first['n'], first['title']).rsplit('/', 1)[0] + '.html'
        book_tiles += f"""
        <a class="livre-tile" href="{link}">
          <div class="livre-tile-overlay"></div>
          <div class="livre-tile-content">
            <div class="livre-tile-num">Tome {b}</div>
            <h3>{esc(first['bookTitle'])}</h3>
            <div class="livre-tile-stats">
              <span>{len(chs)} chapitres</span>
              <span>Ch. {first['n']} – {chs[-1]['n']}</span>
            </div>
            <span class="livre-tile-arrow" aria-hidden="true">›</span>
          </div>
        </a>"""
    oeuvre = """
        <h3>L'œuvre</h3>
        <p><strong>Renegade Immortal (Xian Ni)</strong> est un web novel de cultivation xianxia sombre, brutal et profondément psychologique, écrit par <strong>Er Gen</strong> (耳根), également auteur de <em>I Shall Seal the Heavens</em> et <em>A Will Eternal</em>.</p>
        <p>Imaginez un jeune homme talentueux, promis à un grand avenir. Imaginez que tout cela lui soit arraché. Imaginez qu'au lieu de sombrer, il se relève. Non pas par amour, non pas par devoir, mais par une seule chose : la haine.</p>
        <p><em>Bienvenue dans l'univers de Renegade Immortal.</em></p>
    """
    ergen = """
        <h3>À propos de l'auteur — Er Gen (耳根)</h3>
        <p>Er Gen (耳根) est un auteur chinois de web novels célèbre pour ses œuvres de xianxia. Il a commencé à publier sur Qidian en 2009. Son style se caractérise par des héros qui surmontent l'adversité par leur persévérance.</p>
        <ul>
            <li><strong>Renegade Immortal</strong> (仙逆) — 2009-2012, 2088 chapitres, 6,57 M mots</li>
            <li><strong>I Shall Seal the Heavens</strong> (我欲封天) — 2014-2017</li>
            <li><strong>A Will Eternal</strong> (一念永恒) — 2017-2020</li>
        </ul>
    """
    xian_ni = """
        <h3>Renegade Immortal — résumé</h3>
        <p>Wang Lin est un jeune garçon de la campagne, vivant dans la pauvreté avec ses parents dans le Pays de Zhao. Il possède un talent médiocre pour la cultivation, mais une volonté inébranlable. Sa rencontre avec la Perle défiant les Cieux, un artefact ancien aux origines mystérieuses, change le cours de sa destinée.</p>
        <p>Au cours de 2088 chapitres et 13 livres, Wang Lin traverse des épreuves innombrables, trahi par ceux qu'il aimait, perdant et retrouvant ceux qui lui sont chers, pour devenir l'un des cultivateurs les plus puissants de l'univers.</p>
    """
    body = f"""
  <section class="tab-panel is-active">
    <h1>Le Livre</h1>
    <p style="max-width: 60ch;">Présentation de l'œuvre et accès aux 13 tomes de la traduction française.</p>
    <div class="divider"><span>À propos</span></div>
    <div class="livre-prose">{oeuvre}{xian_ni}{ergen}</div>
    <div class="divider"><span>Les 13 Tomes</span></div>
    <div class="livre-grid" role="list">{book_tiles}</div>
  </section>
"""
    extra_css = """
  .livre-prose { max-width: 70ch; line-height: 1.75; }
  .livre-prose h3 { font-size: 1.1rem; color: var(--gold); margin: 22px 0 10px; border-bottom: 0; padding: 0; }
  .livre-prose p { font-size: 15px; }
  .livre-prose ul { margin: 10px 0 14px; padding-left: 20px; }
  .livre-prose li { font-size: 14px; margin-bottom: 4px; }
  .livre-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; margin: 8px 0 32px; }
  .livre-tile { position: relative; display: block; aspect-ratio: 3 / 4; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; color: #fff; text-decoration: none; transition: transform .25s, border-color .25s; }
  .livre-tile:hover { transform: translateY(-4px); border-color: var(--crimson-dim); }
  .livre-tile-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(7,6,10,.2) 30%, rgba(7,6,10,.9) 100%); }
  .livre-tile-content { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 20px; }
  .livre-tile-num { font-family: 'Cinzel', serif; font-size: 10.5px; letter-spacing: .3em; text-transform: uppercase; color: var(--crimson-2); margin-bottom: 6px; }
  .livre-tile-content h3 { font-size: 1.25rem; color: #fff; margin: 0 0 8px; line-height: 1.2; }
  .livre-tile-stats { display: flex; flex-direction: column; gap: 2px; font-size: 12px; color: var(--ink-3); }
  .livre-tile-arrow { position: absolute; right: 18px; bottom: 18px; font-size: 22px; color: var(--crimson-2); }
"""
    html = page_html('Le Livre', body, nav_active='livre', extra_css=extra_css)
    write('livre.html', html)
    print('  ✓ livre.html')


def build_themed_page(category_key, title, intro, top_pages, nav_active):
    tiles = ''
    for p in top_pages:
        slug = slugify(p['name'])
        img = find_image_for_page(p)
        cats = ', '.join(p.get('categories', [])[:3])
        tiles += f"""
        <a class="themed-tile" href="{category_key}/{slug}.html">
          <div class="themed-tile-bg" style="background-image:url('{img}')"></div>
          <div class="themed-tile-overlay"></div>
          <div class="themed-tile-content">
            <h3>{esc(p['title'])}</h3>
            <div class="themed-tile-cats">{esc(cats)}</div>
            <span class="themed-tile-arrow" aria-hidden="true">›</span>
          </div>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <h1>{esc(title)}</h1>
    <p style="max-width: 60ch;">{esc(intro)}</p>
    <div class="divider"><span>{esc(title)} ({len(top_pages)})</span></div>
    <div class="themed-grid" role="list">{tiles}</div>
  </section>
"""
    extra_css = """
  .themed-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
  .themed-tile { position: relative; display: block; aspect-ratio: 4 / 5; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; color: #fff; text-decoration: none; transition: transform .25s, border-color .25s; }
  .themed-tile:hover { transform: translateY(-3px); border-color: var(--crimson-dim); }
  .themed-tile-bg { position: absolute; inset: 0; background-size: cover; background-position: center top; transition: transform .5s; background-color: var(--bg-3); }
  .themed-tile:hover .themed-tile-bg { transform: scale(1.06); }
  .themed-tile-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 40%, rgba(7,6,10,.92) 100%); }
  .themed-tile-content { position: absolute; left: 0; right: 0; bottom: 0; padding: 16px 18px; }
  .themed-tile-content h3 { font-size: 1.05rem; color: #fff; margin: 0 0 4px; line-height: 1.2; text-shadow: 0 2px 8px rgba(0,0,0,.9); }
  .themed-tile-cats { font-family: 'Cinzel', serif; font-size: 9.5px; letter-spacing: .2em; text-transform: uppercase; color: var(--crimson-2); }
  .themed-tile-arrow { position: absolute; right: 16px; bottom: 14px; font-size: 20px; color: var(--crimson-2); }
"""
    html = page_html(title, body, nav_active=nav_active, extra_css=extra_css)
    write(f'{category_key}.html', html)
    print(f'  ✓ {category_key}.html ({len(top_pages)} entries)')


def build_chapitres():
    by_book = {}
    for c in CHAPTERS:
        by_book.setdefault(c['book'], []).append(c)
    book_cards = ''
    for b in sorted(by_book.keys()):
        chs = by_book[b]
        first = chs[0]
        book_link = chapter_path(b, first['bookTitle'], first['n'], first['title']).rsplit('/', 1)[0] + '.html'
        book_cards += f"""
        <a class="book-tile" href="{book_link}" role="listitem">
          <div class="book-tile-num">Tome {b}</div>
          <div class="book-tile-title">{esc(first['bookTitle'])}</div>
          <div class="book-tile-stats">
            <span>{len(chs)} chapitres</span>
            <span>Ch. {first['n']} – {chs[-1]['n']}</span>
          </div>
          <span class="book-tile-arrow" aria-hidden="true">›</span>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <h1>Chapitres</h1>
    <p style="max-width: 60ch;">2088 chapitres répartis sur les 13 livres. Cliquez sur un livre.</p>
    <div class="divider"><span>Les 13 livres</span></div>
    <div class="books-grid" role="list">{book_cards}</div>
  </section>
"""
    extra_css = """
  .books-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
  .book-tile { display: flex; flex-direction: column; gap: 6px; background: var(--bg-1); border: 1px solid var(--line); padding: 20px 22px; color: var(--ink-1); text-decoration: none; transition: background .2s, border-color .2s, transform .15s; position: relative; }
  .book-tile:hover { background: var(--bg-2); border-color: var(--crimson-dim); transform: translateY(-2px); }
  .book-tile-num { font-family: 'Cinzel', serif; font-size: 10.5px; letter-spacing: .3em; text-transform: uppercase; color: var(--crimson-2); }
  .book-tile-title { font-size: 1.15rem; line-height: 1.2; }
  .book-tile-stats { display: flex; flex-direction: column; gap: 2px; font-size: 12px; color: var(--ink-3); }
  .book-tile-arrow { position: absolute; right: 18px; bottom: 18px; font-size: 22px; color: var(--crimson-2); }
"""
    html = page_html('Chapitres', body, nav_active='chapters', extra_css=extra_css)
    write('chapitres.html', html)
    print('  ✓ chapitres.html')


def build_characters():
    data = load_main_characters()
    main_tiles = ''
    if data:
        for key in ['wang', 'situ', 'limuwan']:
            if key not in data['characters']: continue
            c = data['characters'][key]
            slug = slugify(c['title'])
            main_tiles += f"""
        <a class="themed-tile" href="personnages/{slug}.html">
          <div class="themed-tile-bg" style="background-image:url('{data['images'][key]}')"></div>
          <div class="themed-tile-overlay"></div>
          <div class="themed-tile-content">
            <h3>{esc(c['title'])}</h3>
            <div class="themed-tile-cats">Protagoniste</div>
            <span class="themed-tile-arrow" aria-hidden="true">›</span>
          </div>
        </a>"""
    buckets = categorize_wiki()
    curated = curate_top(buckets['personnages'], 18)
    wiki_tiles = ''
    for p in curated:
        if p['name'] in ('Wang Lin', 'Situ Nan', 'Li Muwan', 'Li MuWan'): continue
        slug = slugify(p['name'])
        img = find_image_for_page(p)
        cats = ', '.join(p.get('categories', [])[:3])
        wiki_tiles += f"""
        <a class="themed-tile" href="personnages/{slug}.html">
          <div class="themed-tile-bg" style="background-image:url('{img}')"></div>
          <div class="themed-tile-overlay"></div>
          <div class="themed-tile-content">
            <h3>{esc(p['title'])}</h3>
            <div class="themed-tile-cats">{esc(cats)}</div>
            <span class="themed-tile-arrow" aria-hidden="true">›</span>
          </div>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <h1>Personnages</h1>
    <p style="max-width: 60ch;">Figures emblématiques de l'œuvre — du protagoniste torturé aux immortels qui ont croisé sa route.</p>
    <div class="divider"><span>Figures majeures</span></div>
    <div class="themed-grid" role="list">{main_tiles}</div>
    <div class="divider"><span>Plus de personnages</span></div>
    <div class="themed-grid" role="list">{wiki_tiles}</div>
  </section>
"""
    extra_css = """
  .themed-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
  .themed-tile { position: relative; display: block; aspect-ratio: 4 / 5; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; color: #fff; text-decoration: none; transition: transform .25s, border-color .25s; }
  .themed-tile:hover { transform: translateY(-3px); border-color: var(--crimson-dim); }
  .themed-tile-bg { position: absolute; inset: 0; background-size: cover; background-position: center top; transition: transform .5s; background-color: var(--bg-3); }
  .themed-tile:hover .themed-tile-bg { transform: scale(1.06); }
  .themed-tile-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 40%, rgba(7,6,10,.92) 100%); }
  .themed-tile-content { position: absolute; left: 0; right: 0; bottom: 0; padding: 16px 18px; }
  .themed-tile-content h3 { font-size: 1.05rem; color: #fff; margin: 0 0 4px; line-height: 1.2; }
  .themed-tile-cats { font-family: 'Cinzel', serif; font-size: 9.5px; letter-spacing: .2em; text-transform: uppercase; color: var(--crimson-2); }
  .themed-tile-arrow { position: absolute; right: 16px; bottom: 14px; font-size: 20px; color: var(--crimson-2); }
"""
    html = page_html('Personnages', body, nav_active='characters', extra_css=extra_css)
    write('personnages.html', html)
    n_curated = len(curated)
    print(f'  ✓ personnages.html ({3 + n_curated} entries)')


def build_404():
    body = """
  <section class="tab-panel is-active" style="text-align: center; padding: 80px 24px;">
    <div style="font-size: 4rem; color: var(--crimson); font-family: 'Cinzel', serif;">404</div>
    <h1>Page introuvable</h1>
    <p style="color: var(--ink-3); max-width: 40ch; margin: 16px auto;">La page que vous cherchez n'existe pas.</p>
    <a href="index.html" class="btn-primary">← Retour à l'accueil</a>
  </section>
"""
    html = page_html("Page introuvable", body)
    write('404.html', html)
    print('  ✓ 404.html')


# === ENTRY PAGES ===
ENTRY_CSS = """
  .breadcrumb { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 14px; }
  .breadcrumb a { color: var(--crimson-2); border-bottom: 1px solid var(--crimson-dim); }
  .entry-page { background: var(--bg-1); border: 1px solid var(--line); padding: 32px 36px; }
  .entry-page h1 { font-size: 2rem; margin: 0 0 12px; }
  .wikicats { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 16px; }
  .wikicats .cat { font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: .15em; text-transform: uppercase; padding: 3px 8px; border: 1px solid var(--crimson-dim); color: var(--crimson-2); background: rgba(179,38,30,.06); border-radius: 999px; }
  .entry-hero { margin: 0 0 28px; }
  .entry-hero img { max-width: 100%; max-height: 480px; display: block; border: 1px solid var(--line); }
  .entry-content h2, .entry-content h3 { color: var(--gold); margin: 24px 0 10px; border-bottom: 0; padding: 0; }
  .entry-content p { font-size: 15px; line-height: 1.75; margin: 0 0 14px; }
  .wiki-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; margin: 18px 0 28px; }
  .wiki-gallery-item { position: relative; display: block; aspect-ratio: 1; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; }
  .wiki-gallery-item.is-main { grid-column: span 2; grid-row: span 2; }
  .wiki-gallery-item img { width: 100%; height: 100%; object-fit: cover; }
  .wiki-gallery-label { position: absolute; top: 8px; left: 8px; background: rgba(7,6,10,.85); color: var(--crimson-2); padding: 3px 8px; font-family: 'Cinzel', serif; font-size: 9px; letter-spacing: .2em; text-transform: uppercase; border: 1px solid var(--crimson-dim); }
"""


def build_entry_pages():
    """Build the 2e-page articles for each curated entry."""
    buckets = categorize_wiki()

    # === PERSONNAGES (3 main + curated wiki) ===
    data = load_main_characters()
    if data:
        for key in ['wang', 'situ', 'limuwan']:
            if key not in data['characters']: continue
            c = data['characters'][key]
            slug = slugify(c['title'])
            body = f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb"><a href="../personnages.html">← Personnages</a></nav>
    <div class="entry-page">
      <header>
        <h1>{esc(c['title'])}</h1>
        <div class="wikicats"><span class="cat">Protagoniste</span></div>
        <a class="fandom-link" href="{esc(data['urls'][key])}" target="_blank" rel="noopener">Voir sur Fandom Wiki →</a>
      </header>
      <div class="entry-hero"><img src="../{data['images'][key]}" alt="{esc(c['title'])}" loading="lazy" /></div>
      <article class="entry-content">
        <h3>Présentation</h3>
        <p>{esc(c['overview'])}</p>
        <h3>Personnalité</h3>
        <p>{esc(c['personality'])}</p>
        <h3>Origines</h3>
        <p>{esc(c['background'])}</p>
      </article>
    </div>
  </section>
"""
            html = page_html(c['title'], body, base='../', nav_active='characters', extra_css=ENTRY_CSS)
            write(f'personnages/{slug}.html', html)

    # Curated wiki personnages
    for p in curate_top(buckets['personnages'], 18):
        if p['name'] in ('Wang Lin', 'Situ Nan', 'Li Muwan', 'Li MuWan'): continue
        slug = slugify(p['name'])
        body = build_wiki_entry_body(p, 'personnages.html', 'Personnages')
        if body:
            html = page_html(p['title'], body, base='../', nav_active='characters', extra_css=ENTRY_CSS)
            write(f'personnages/{slug}.html', html)

    # === CULTIVATION ===
    for p in curate_top(buckets['cultivation'], 20):
        slug = slugify(p['name'])
        body = build_wiki_entry_body(p, 'cultivation.html', 'Cultivation')
        if body:
            html = page_html(p['title'], body, base='../', nav_active='cultivation', extra_css=ENTRY_CSS)
            write(f'cultivation/{slug}.html', html)

    # === SECTES & CLANS ===
    for p in curate_top(buckets['sectes'], 20):
        slug = slugify(p['name'])
        body = build_wiki_entry_body(p, 'sectes-clans.html', 'Sectes & Clans')
        if body:
            html = page_html(p['title'], body, base='../', nav_active='sectes', extra_css=ENTRY_CSS)
            write(f'sectes-clans/{slug}.html', html)

    # === LIEUX ===
    for p in curate_top(buckets['lieux'], 20):
        slug = slugify(p['name'])
        body = build_wiki_entry_body(p, 'lieux.html', 'Lieux')
        if body:
            html = page_html(p['title'], body, base='../', nav_active='lieux', extra_css=ENTRY_CSS)
            write(f'lieux/{slug}.html', html)

    # === WIKI (mix) ===
    wiki_mix = curate_top(buckets['personnages'] + buckets['cultivation'] + buckets['sectes'] + buckets['lieux'], 30)
    for p in wiki_mix:
        slug = slugify(p['name'])
        body = build_wiki_entry_body(p, 'wiki.html', 'Wiki')
        if body:
            html = page_html(p['title'], body, base='../', nav_active='wiki', extra_css=ENTRY_CSS)
            write(f'wiki/{slug}.html', html)

    print(f'  ✓ built entry pages (personnages + cultivation + sectes + lieux + wiki)')


def build_wiki_entry_body(p, back_href, back_label):
    """Build the body of a wiki entry article."""
    wp_file = WIKI / (p['name'] + '.json')
    page_data = None
    if wp_file.exists():
        try: page_data = json.loads(wp_file.read_text(encoding='utf-8'))
        except: pass
    if not page_data and p.get('sub'):
        for f in WIKI.iterdir():
            if f.stem == p['name']:
                try: page_data = json.loads(f.read_text(encoding='utf-8'))
                except: pass
    if not page_data:
        return None
    content = page_data.get('content', '')
    sections = parse_wiki_sections(content)
    sect_html = ''
    for j, (title, paras) in enumerate(sections):
        if not paras: continue
        is_first = (j == 0)
        heading = '<h2>' + esc(title) + '</h2>' if is_first else '<h3>' + esc(title) + '</h3>'
        sect_html += heading + ''.join('<p>' + esc(par) + '</p>' for par in paras)
    cats = ''.join('<span class="cat">' + esc(c) + '</span>' for c in p.get('categories', [])[:8])
    return f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb"><a href="../{back_href}">← {esc(back_label)}</a></nav>
    <div class="entry-page">
      <header>
        <h1>{esc(p['title'])}</h1>
        <div class="wikicats">{cats}</div>
        <a class="fandom-link" href="{esc(p.get('url', ''))}" target="_blank" rel="noopener">Voir sur Fandom Wiki →</a>
      </header>
      <article class="entry-content">{sect_html}</article>
    </div>
  </section>
"""


# === BOOKS + CHAPTERS ===
def build_book_page(b, chs):
    first = chs[0]
    cards = ''
    for c in chs:
        clean = re.sub(r'^Chapitre\s+\d+\s*[-—:]\s*', '', c['title']).strip() or c['title']
        link = chapter_path(b, first['bookTitle'], c['n'], c['title'])
        cards += f"""
        <a class="chapter" href="{link}" role="listitem">
          <span class="title">{esc(clean)}</span>
          <span class="arrow" aria-hidden="true">›</span>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb"><a href="../../chapitres.html">← Tous les livres</a></nav>
    <div class="eyebrow">Tome {b}</div>
    <h1>{esc(first['bookTitle'])}</h1>
    <p style="max-width: 60ch;">{len(chs)} chapitres. Cliquez pour lire.</p>
    <div class="divider"><span>Chapitres</span></div>
    <div class="chapters" role="list">{cards}</div>
  </section>
"""
    extra_css = """
  .breadcrumb { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 14px; }
  .breadcrumb a { color: var(--crimson-2); border-bottom: 1px solid var(--crimson-dim); }
  .chapters { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
  .chapter { display: flex; align-items: center; justify-content: space-between; gap: 12px; background: var(--bg-1); border: 1px solid var(--line); padding: 16px 18px; color: var(--ink-1); text-decoration: none; transition: background .2s, border-color .2s, transform .15s; min-height: 58px; }
  .chapter:hover { background: var(--bg-2); border-color: var(--crimson-dim); transform: translateY(-1px); }
  .chapter .title { flex: 1; font-size: 14.5px; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .chapter .arrow { color: var(--ink-4); flex-shrink: 0; font-size: 18px; }
  .chapter:hover .arrow { color: var(--crimson); }
"""
    html = page_html(f"Tome {b} — {first['bookTitle']}", body, base='../../', nav_active='chapters', extra_css=extra_css)
    write(chapter_path(b, first['bookTitle'], first['n'], first['title']).rsplit('/', 1)[0] + '.html', html)


def build_chapter_page(c, prev_c, next_c):
    book_dir = TRADUCTION / f"Book {c['book']} - {c['bookTitle']}"
    chap_file = book_dir / Path(c['file']).name
    text = ''
    if chap_file.exists():
        text = chap_file.read_text(encoding='utf-8', errors='replace')
        text = text.lstrip('\ufeff').lstrip()
        lines = text.split('\n', 1)
        if len(lines) > 1 and not lines[0].rstrip().endswith(('.', '!', '?')):
            text = lines[1].lstrip('\n')
        text = text.strip()
    paras = text.split('\n')
    body_paras = []
    first_p = True
    for p in paras:
        p = p.strip()
        if not p or len(p) < 20: continue
        if first_p:
            body_paras.append(f'<p class="lead-paragraph">{esc(p)}</p>')
            first_p = False
        else:
            body_paras.append(f'<p>{esc(p)}</p>')
    body_html = '\n        '.join(body_paras) if body_paras else '<p class="reader-error">Contenu non disponible.</p>'
    prev_link = ''
    next_link = ''
    if prev_c:
        prev_link = f'<a class="btn" href="../{chapter_path(prev_c["book"], prev_c["bookTitle"], prev_c["n"], prev_c["title"])}">← Chapitre {prev_c["n"]}</a>'
    if next_c:
        next_link = f'<a class="btn" href="../{chapter_path(next_c["book"], next_c["bookTitle"], next_c["n"], next_c["title"])}">Chapitre {next_c["n"]} →</a>'
    body = f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb"><a href="../../../chapitres.html">← Tous les livres</a> / <a href="../{book_slug(c['book'], c['bookTitle'])}.html">Tome {c['book']}</a></nav>
    <div class="reader">
      <div class="reader-bar">
        <div class="meta">
          <div class="num">Tome {c['book']} · Chapitre {c['n']}</div>
          <div class="title">{esc(c['title'])}</div>
        </div>
        <div class="actions">
          {prev_link}
          {next_link}
          <a class="btn" href="../../../chapitres.html">Fermer</a>
        </div>
      </div>
      <div class="reader-body">{body_html}</div>
    </div>
  </section>
"""
    extra_css = """
  .reader { background: var(--bg-1); border: 1px solid var(--line); margin-top: 28px; }
  .reader-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 24px; border-bottom: 1px solid var(--line); background: var(--bg-2); position: sticky; top: 64px; z-index: 10; }
  .reader-bar .meta { display: flex; flex-direction: column; line-height: 1.2; min-width: 0; }
  .reader-bar .meta .num { font-family: 'Cinzel', serif; font-size: 10.5px; letter-spacing: .3em; text-transform: uppercase; color: var(--crimson-2); }
  .reader-bar .meta .title { color: var(--ink-1); font-family: 'Cinzel', serif; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .reader-bar .actions { display: flex; gap: 8px; flex-shrink: 0; }
  .btn { appearance: none; background: transparent; border: 1px solid var(--line); color: var(--ink-2); padding: 8px 14px; font-family: 'Cinzel', serif; font-size: 10.5px; letter-spacing: .15em; text-transform: uppercase; cursor: pointer; border-radius: var(--r-md); transition: all .2s; min-height: 36px; text-decoration: none; }
  .btn:hover { color: var(--ink-1); border-color: var(--crimson-dim); }
  .reader-body { padding: 36px 48px 48px; max-height: 75vh; overflow-y: auto; font-size: 1.05rem; line-height: 1.9; color: var(--ink-2); }
  .reader-body p { margin: 0 0 1.2em; color: var(--ink-2); }
  .reader-body .lead-paragraph::first-letter { font-family: 'Cinzel', serif; font-size: 3.4em; float: left; line-height: .9; margin: 4px 8px 0 0; color: var(--crimson-2); font-weight: 700; }
  .reader-error { padding: 60px 24px; text-align: center; color: var(--ink-3); }
  @media (max-width: 880px) { .reader-body { padding: 24px 24px 36px; } .reader-bar { position: static; flex-wrap: wrap; } .reader-bar .meta { min-width: 100%; } }
"""
    clean = re.sub(r'^Chapitre\s+\d+\s*[-—:]\s*', '', c['title']).strip() or c['title']
    html = page_html(f"Chapitre {c['n']} — {clean}", body, base='../../../', nav_active='chapters', extra_css=extra_css)
    write(chapter_path(c['book'], c['bookTitle'], c['n'], c['title']), html)


# === HOME BG JS ===
HOME_BG_JS = '''// Animated background for the home page
(function() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];
  const COUNT = 60;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  // Init particles
  for (let i = 0; i < COUNT; i++) {
    particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.5 + 0.5,
      hue: Math.random() * 30 + 350  // crimson-ish
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    // Draw particles
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = W;
      if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H;
      if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(214, 58, 46, 0.5)';
      ctx.fill();
    }
    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d = Math.sqrt(dx*dx + dy*dy);
        if (d < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = 'rgba(179, 38, 30, ' + (0.15 - d / 800) + ')';
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();
'''


# === MAIN ===
def main():
    print('=== Building site ===\n')

    # Clean _site
    if SITE.exists():
        shutil.rmtree(SITE, ignore_errors=True)
    SITE.mkdir(parents=True, exist_ok=True)

    # Copy data dirs
    for sub in ['traduction', 'wiki/images']:
        src = ROOT / sub
        dst = SITE / sub
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
            print(f'  copied {sub}/')

    # Write home-bg.js
    (SITE / 'home-bg.js').write_text(HOME_BG_JS, encoding='utf-8')
    print('  copied home-bg.js')

    # Copy top-level static files
    for f in ['LICENSE.txt', 'LICENSE-traduction.txt', '.nojekyll', 'README.md']:
        src = ROOT / f
        if src.exists():
            shutil.copy2(src, SITE / f)

    # Build index pages
    print('\n=== Building index pages ===')
    build_home()
    build_livre()
    build_chapitres()
    build_characters()
    build_404()
    buckets = categorize_wiki()
    build_themed_page('cultivation', 'Cultivation', 'Système de cultivation, royaumes, techniques.', curate_top(buckets['cultivation'], 20), 'cultivation')
    build_themed_page('sectes-clans', 'Sectes & Clans', 'Les grandes organisations du monde de Renegade Immortal.', curate_top(buckets['sectes'], 20), 'sectes')
    build_themed_page('lieux', 'Lieux', 'Planètes, royaumes célestes, continents, dimensions.', curate_top(buckets['lieux'], 20), 'lieux')
    build_themed_page('wiki', 'Wiki', 'Index des pages wiki Fandom.', curate_top(buckets['personnages'] + buckets['cultivation'] + buckets['sectes'] + buckets['lieux'], 30), 'wiki')

    # Build book + chapter pages
    print('\n=== Building books + chapters ===')
    by_book = {}
    for c in CHAPTERS:
        by_book.setdefault(c['book'], []).append(c)
    for b in sorted(by_book.keys()):
        chs = by_book[b]
        build_book_page(b, chs)
        for i, c in enumerate(chs):
            prev_c = chs[i-1] if i > 0 else None
            next_c = chs[i+1] if i < len(chs)-1 else None
            build_chapter_page(c, prev_c, next_c)
        print(f'  ✓ Tome {b} ({len(chs)} chapters)')

    # Build entry pages
    print('\n=== Building entry pages ===')
    build_entry_pages()

    # Final stats
    n_html = sum(1 for _, _, fs in os.walk(SITE) for f in fs if f.endswith('.html'))
    total_size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(SITE) for f in fs)
    print(f'\n=== DONE ===')
    print(f'  HTML pages: {n_html:,}')
    print(f'  Total size: {total_size/1024/1024:.1f} MB')
    print(f'  Output dir: {SITE}')


if __name__ == '__main__':
    main()
