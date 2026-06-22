#!/usr/bin/env python3
"""
build.py — Génère le site multi-pages Renegade Immortal FR.

Génère (dans ./site/) :
  - index.html                  (page d'accueil)
  - chapitres.html              (index des 13 Books)
  - chapitres/bookN-*.html      (page Book, tuiles chapitres)
  - chapitres/bookN/chN-*.html  (page chapitre)
  - personnages.html             (index persos)
  - personnages/<slug>.html      (fiche perso)
  - univers.html                (page univers)
  - wiki.html                   (index wiki)
  - wiki/<slug>.html            (page wiki)

Usage : python build.py [--clean]
"""
import os
import json
import re
import shutil
import sys
import html as htmlmod
from pathlib import Path

ROOT = Path(__file__).parent
PARTS = ROOT / 'build_parts'
ASSETS = ROOT / 'assets'
TRADUCTION = ROOT / 'traduction'
WIKI = ROOT / 'wiki'
SITE = ROOT / 'site'

# Load reusable parts
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
        s = s[:maxlen].rsplit('-', 1)[0]  # coupe au dernier tiret
    return s or 'x'


def book_slug(book_n, book_title):
    """e.g. 'book1-the-mediocre-youth' from Book 1 + 'The Mediocre Youth'."""
    return f'book{book_n}-{slugify(book_title)}'


def page_html(title, body, base='', nav_active='', data_inline='', extra_css=''):
    """Build a full HTML page with shared head/nav/audio dock."""
    # Adapt paths to base depth
    audio_visibility = 'block' if base else 'block'  # always
    # Replace the JS data init for this page (use inline data if provided, else global)
    if data_inline:
        # Provide data only to this page via a global
        js_init = f"window.__PAGE_DATA__ = {data_inline};"
        page_js = JS.replace(
            "const CHAPTERS_DATA = JSON.parse(document.getElementById(\"chapters-data\").textContent);",
            "const CHAPTERS_DATA = (window.__PAGE_DATA__ && window.__PAGE_DATA__.chapters) || [];"
        ).replace(
            "const WIKI_DATA = JSON.parse(document.getElementById(\"wiki-data\").textContent);",
            "const WIKI_DATA = (window.__PAGE_DATA__ && window.__PAGE_DATA__.wiki) || [];"
        )
        # Wrap the data init at the start
        page_js = js_init + "\n" + page_js
    else:
        # Try to fetch chapters/wiki from the same dir
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
      <a href="{base}chapitres.html" class="nav-tab{' is-active' if nav_active == 'chapters' else ''}">Chapitres</a>
      <a href="{base}personnages.html" class="nav-tab{' is-active' if nav_active == 'characters' else ''}">Personnages</a>
      <a href="{base}univers.html" class="nav-tab{' is-active' if nav_active == 'lore' else ''}">Univers</a>
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
<script>
{page_js}
</script>
</body>
</html>
"""


def write(path, content):
    full = SITE / path
    full.parent.mkdir(parents=True, exist_ok=True)
    # Use \\?\ prefix on Windows for long paths
    path_str = str(full.resolve())
    if os.name == 'nt' and len(path_str) > 240:
        path_str = r'\\\\?\\' + path_str
    with open(path_str, 'w', encoding='utf-8') as f:
        f.write(content)


# === PAGES ===

def build_home():
    body = """
  <section class="tab-panel is-active" id="panel-home">
    <div class="hero">
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
          <p>Wang Lin n'est qu'un jeune garçon lorsque sa vie bascule. Orphelin des montagnes, rejeté par le monde des cultivateurs, il ne possède qu'une seule chose : une obstination tranquille, forgée dans le silence et l'adversité. Au fil des années, il gravit les échelons d'un univers impitoyable où la cultivation n'est ni don ni privilège, mais un chemin de sang, de patience et de choix.</p>
          <p>De la Condensation du Qi aux royaumes supérieurs, de la Perle défiant les Cieux aux secrets des anciens, Wang Lin deviendra bien plus qu'un Immortel — il deviendra celui que l'on n'ose pas nommer. Car dans ce monde, <em>le ciel n'est pas une limite, mais un adversaire</em>.</p>
          <a href="chapitres.html" class="btn" style="display:inline-block;margin-top:14px;padding:10px 20px;border:1px solid var(--crimson-dim);background:linear-gradient(180deg,var(--crimson),var(--crimson-dim));color:#fff;font-family:'Cinzel',serif;font-size:11px;letter-spacing:.2em;text-transform:uppercase;border-radius:var(--r-md);">Commencer la lecture →</a>
        </div>
      </div>
    </div>
  </section>
"""
    html = page_html("Accueil", body, nav_active='home')
    write('index.html', html)
    print('  ✓ index.html')


def build_chapters_index():
    # Group by book
    by_book = {}
    for c in CHAPTERS:
        by_book.setdefault(c['book'], []).append(c)

    book_cards = ''
    for b in sorted(by_book.keys()):
        chs = by_book[b]
        first = chs[0]
        last = chs[-1]
        book_link = f'chapitres/{book_slug(b, first["bookTitle"])}.html'
        book_cards += f"""
        <a class="book-tile" href="{book_link}" role="listitem">
          <div class="book-tile-num">Tome {b}</div>
          <div class="book-tile-title">{esc(first['bookTitle'])}</div>
          <div class="book-tile-stats">
            <span>{len(chs)} chapitres</span>
            <span>Ch. {first['n']} – {last['n']}</span>
          </div>
          <span class="book-tile-arrow" aria-hidden="true">›</span>
        </a>"""

    body = f"""
  <section class="tab-panel is-active">
    <h1>Chapitres</h1>
    <p style="max-width: 60ch;">2088 chapitres répartis sur les 13 livres de l'œuvre. Cliquez sur un livre pour accéder à ses chapitres.</p>
    <div class="divider"><span>Les 13 livres</span></div>
    <div class="books-grid" role="list">
{book_cards}
    </div>
  </section>
"""
    html = page_html("Chapitres", body, nav_active='chapters')
    write('chapitres.html', html)
    print('  ✓ chapitres.html')


def build_book_page(b, chs):
    """Build a page for one Book with chapter tiles."""
    first = chs[0]
    chapter_cards = ''
    for c in chs:
        chap_link = f'{book_slug(b, first["bookTitle"])}/{c["n"]:04d}-{slugify(c["title"])}.html'
        # Strip leading "Chapitre N - " from the title for cleaner display
        clean_title = re.sub(r'^Chapitre\s+\d+\s*[-—:]\s*', '', c['title']).strip()
        if not clean_title:
            clean_title = c['title']
        chapter_cards += f"""
        <a class="chapter" href="{chap_link}" role="listitem">
          <span class="title">{esc(clean_title)}</span>
          <span class="arrow" aria-hidden="true">›</span>
        </a>"""

    body = f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb">
      <a href="../chapitres.html">← Tous les livres</a>
    </nav>
    <div class="eyebrow">Tome {b}</div>
    <h1>{esc(first['bookTitle'])}</h1>
    <p style="max-width: 60ch;">Chapitres {first['n']} à {chs[-1]['n']} ({len(chs)} chapitres). Cliquez sur un chapitre pour le lire.</p>
    <div class="divider"><span>Chapitres</span></div>
    <div class="chapters" role="list">
{chapter_cards}
    </div>
  </section>
"""
    html = page_html(f"Tome {b} — {first['bookTitle']}", body, base='../', nav_active='chapters')
    write(f'chapitres/{book_slug(b, first["bookTitle"])}.html', html)


def build_chapter_page(c, prev_c, next_c):
    """Build a page for one chapter."""
    # Get chapter text from file
    book_dir = TRADUCTION / f"Book {c['book']} - {c['bookTitle']}"
    chap_file = book_dir / Path(c['file']).name
    text = ''
    if chap_file.exists():
        text = chap_file.read_text(encoding='utf-8', errors='replace')
        # Strip BOM and first line (title)
        text = text.lstrip('﻿').lstrip()
        # Remove first line if it's a title
        lines = text.split('\n', 1)
        if len(lines) > 1 and lines[0].strip():
            # Check if first line is a title (no period)
            if not lines[0].rstrip().endswith(('.', '!', '?')):
                text = lines[1].lstrip('\n')
        text = text.strip()

    # Build paragraphs HTML
    paras = text.split('\n')
    body_paras = []
    first_p = True
    for p in paras:
        p = p.strip()
        if not p or len(p) < 20:
            continue
        if first_p:
            body_paras.append(f'<p class="lead-paragraph">{esc(p)}</p>')
            first_p = False
        else:
            body_paras.append(f'<p>{esc(p)}</p>')
    body_html = '\n        '.join(body_paras) if body_paras else '<p class="reader-error">Contenu non disponible.</p>'

    # Prev/next
    prev_link = ''
    next_link = ''
    if prev_c:
        prev_path = f'../{prev_c["n"]:04d}-{slugify(prev_c["title"])}.html'
        prev_link = f'<a class="btn" href="{prev_path}">← Chapitre {prev_c["n"]}</a>'
    if next_c:
        next_path = f'../{next_c["n"]:04d}-{slugify(next_c["title"])}.html'
        next_link = f'<a class="btn" href="{next_path}">Chapitre {next_c["n"]} →</a>'

    body = f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb">
      <a href="../../chapitres.html">← Tous les livres</a> /
      <a href="../{book_slug(c['book'], c['bookTitle'])}.html">Tome {c['book']}</a>
    </nav>
    <div class="reader">
      <div class="reader-bar">
        <div class="meta">
          <div class="num">Tome {c['book']} · Chapitre {c['n']}</div>
          <div class="title">{esc(c['title'])}</div>
        </div>
        <div class="actions">
          {prev_link}
          {next_link}
          <a class="btn" href="../../chapitres.html">Fermer</a>
        </div>
      </div>
      <div class="reader-body">
        {body_html}
      </div>
    </div>
  </section>
"""
    clean_title = re.sub(r'^Chapitre\s+\d+\s*[-—:]\s*', '', c['title']).strip() or c['title']
    html = page_html(f"Chapitre {c['n']} — {clean_title}", body, base='../../', nav_active='chapters')
    chap_slug = f'{c["n"]:04d}-{slugify(c["title"])}'
    write(f'chapitres/{book_slug(c["book"], c["bookTitle"])}/{chap_slug}.html', html)


def build_characters_index():
    # Load data
    data = json.loads((ASSETS / 'data.json').read_text(encoding='utf-8'))
    chars = data['characters']
    imgs = data['images']
    urls = data['urls']

    cards = ''
    for key in ['wang', 'situ', 'limuwan']:
        c = chars[key]
        slug = slugify(c['title'])
        cards += f"""
        <article class="character-tile" onclick="location.href='personnages/{slug}.html'" role="listitem">
          <div class="character-tile-portrait">
            <img src="../../{imgs[key]}" alt="{esc(c['title'])}" loading="lazy" />
          </div>
          <div class="character-tile-body">
            <div class="role">Protagoniste</div>
            <h3>{esc(c['title'])}</h3>
            <div class="subtitle">{esc(c['title'])} — personnage majeur</div>
          </div>
        </article>"""

    body = f"""
  <section class="tab-panel is-active">
    <h1>Personnages</h1>
    <p style="max-width: 60ch;">Figures emblématiques de l'œuvre — descriptions extraites du wiki officiel Fandom.</p>
    <div class="divider"><span>Figures majeures</span></div>
    <div class="characters-grid" role="list">
{cards}
    </div>
  </section>
"""
    html = page_html("Personnages", body, nav_active='characters')
    write('personnages.html', html)
    print('  ✓ personnages.html')


def build_character_page(key, c, imgs, urls):
    slug = slugify(c['title'])
    body = f"""
  <section class="tab-panel is-active">
    <nav class="breadcrumb">
      <a href="../personnages.html">← Personnages</a>
    </nav>
    <div class="card is-featured">
      <div class="card-portrait" role="img" aria-label="Portrait — {esc(c['title'])}">
        <img src="../../{imgs[key]}" alt="{esc(c['title'])}" loading="lazy" />
      </div>
      <div class="card-body">
        <div class="role">Protagoniste</div>
        <h3>{esc(c['title'])}</h3>
        <div class="subtitle">{esc(c['title'])}</div>
        <p>{esc(c['overview'])}</p>
        <div class="sec-label">Personnalité</div>
        <p class="sec-text">{esc(c['personality'])}</p>
        <div class="sec-label">Origines</div>
        <p class="sec-text">{esc(c['background'])}</p>
        <p style="margin-top:14px;font-size:12.5px;color:var(--ink-3);">
          Source : <a class="fandom-link" href="{urls[key]}" target="_blank" rel="noopener">xian-ni.fandom.com</a>
        </p>
      </div>
    </div>
  </section>
"""
    html = page_html(c['title'], body, base='../', nav_active='characters')
    write(f'personnages/{slug}.html', html)


def build_univers():
    body = """
  <section class="tab-panel is-active">
    <div class="eyebrow">Le monde · Le lore</div>
    <h1>Univers</h1>
    <p style="max-width: 60ch;">Plongez dans les rouages du monde de Renegade Immortal — sa hiérarchie de cultivation, ses royaumes, ses artefacts.</p>
    <div class="divider"><span>Système de Cultivation</span></div>
    <div class="lore-section">
      <p class="lead">Le chemin de la cultivation est une ascension longue et impitoyable, où chaque royaume sépare le faible du puissant par un gouffre que peu franchissent vivants. Voici les premiers paliers du système.</p>
      <div class="realm-list">
        <div class="realm"><div class="stage">Royaume 1</div><h3>Condensation du Qi</h3><p>Le premier souffle. Le cultivateur apprend à percevoir et condenser l'énergie spirituelle environnante.</p><div class="pinyin">凝气 · Ning Qi</div></div>
        <div class="realm"><div class="stage">Royaume 2</div><h3>Établissement des Fondations</h3><p>Le Qi se solidifie. Les fondations déterminent la qualité de toute la cultivation future.</p><div class="pinyin">筑基 · Zhu Ji</div></div>
        <div class="realm"><div class="stage">Royaume 3</div><h3>Formation du Noyau</h3><p>Un noyau d'énergie se forme au cœur du cultivateur — marque des véritables élites.</p><div class="pinyin">结丹 · Jie Dan</div></div>
        <div class="realm"><div class="stage">Royaume 4</div><h3>Âme Naissante</h3><p>L'âme s'éveille. Le cultivateur transcende la mortalité ordinaire et touche au domaine des Immortels.</p><div class="pinyin">元婴 · Yuan Ying</div></div>
        <div class="realm"><div class="stage">Royaume 5</div><h3>Séparation du Spirituel</h3><p>Le corps et l'âme se distinguent. Le voyage entre les mondes devient possible.</p><div class="pinyin">化神 · Hua Shen</div></div>
        <div class="realm"><div class="stage">Royaume 6</div><h3>Royaume de la Tribulation</h3><p>Le cultivateur défie le Ciel lui-même. Chaque pas est une épreuve — et un pari sur sa propre existence.</p><div class="pinyin">渡劫 · Du Jie</div></div>
      </div>
    </div>
    <div class="divider"><span>Géographie & Artefacts</span></div>
    <div class="lore-section">
      <div class="geography">
        <div>
          <h2>Le Monde</h2>
          <p>Le récit s'étend sur quatre royaumes principaux, chacun avec ses sectes, ses lois et ses hiérarchies : le <em>Royaume des Morts</em>, le <em>Royaume des Cieux</em>, le <em>Royaume des Étoiles</em> et le <em>Royaume Ji</em>. Tous gravitent autour de l'Immortel de la planète Tianyuan, dont la chute entraîne la ruine de l'ordre ancien.</p>
          <p>Des continents flottants aux planètes désolées, chaque lieu reflète la philosophie d'Er Gen : un univers vaste, cruel, mais où la persévérance peut encore tout changer.</p>
        </div>
        <div class="geography">
          <div class="map-placeholder" role="img" aria-label="Carte stylisée des royaumes">
            <svg class="map-svg" viewBox="0 0 400 300" aria-hidden="true">
              <defs>
                <radialGradient id="g1" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="rgba(74,110,216,.35)"/><stop offset="100%" stop-color="rgba(74,110,216,0)"/></radialGradient>
                <radialGradient id="g2" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="rgba(179,38,30,.3)"/><stop offset="100%" stop-color="rgba(179,38,30,0)"/></radialGradient>
              </defs>
              <circle cx="120" cy="130" r="80" fill="url(#g1)"/>
              <circle cx="280" cy="180" r="90" fill="url(#g2)"/>
              <g stroke="rgba(200,164,74,.4)" stroke-width="1" fill="none">
                <circle cx="120" cy="130" r="60"/>
                <circle cx="280" cy="180" r="70"/>
              </g>
              <g fill="rgba(236,230,216,.7)" font-family="Cinzel, serif" font-size="8" letter-spacing="2">
                <text x="95" y="105">ROYAUME</text><text x="100" y="118">DES MORTS</text>
                <text x="245" y="160">ROYAUME</text><text x="260" y="173">DES CIEUX</text>
              </g>
              <line x1="180" y1="135" x2="240" y2="170" stroke="rgba(200,164,74,.25)" stroke-dasharray="2 3"/>
            </svg>
          </div>
        </div>
      </div>
      <div style="margin-top: 32px;">
        <div class="artifact">
          <h3>La Perle défiant les Cieux <span style="color:var(--ink-3);font-weight:400;font-style:italic">— Heaven-Defying Bead</span></h3>
          <div class="pinyin">逆天珠 · Ni Tian Zhu</div>
          <p>Héritage du plus ancien des Immortels, la Perle défiant les Cieux est l'artefact central de l'œuvre. Liée au destin de Wang Lin depuis sa rencontre dans les ruines antiques, elle possède sa propre conscience et dicte, plus qu'elle n'aide, la voie du protagoniste. Une relique que le Ciel lui-même aurait voulu détruire.</p>
        </div>
      </div>
    </div>
  </section>
"""
    html = page_html("Univers", body, nav_active='lore')
    write('univers.html', html)
    print('  ✓ univers.html')


def build_wiki_index():
    # Group by categories
    from collections import Counter
    cat_count = Counter()
    for w in WIKI_PAGES:
        for c in w.get('categories', []):
            cat_count[c] += 1
    top_cats = cat_count.most_common(20)

    # Inline only minimal data: name, slug, url, categories, preview
    # (no need to inline full wiki data; we link to individual pages)
    slim_wiki = []
    for w in WIKI_PAGES:
        slim_wiki.append({
            'name': w['name'],
            'slug': slugify(w['name']) or 'x',
            'title': w.get('title', w['name']),
            'url': w.get('url', ''),
            'categories': w.get('categories', []),
            'preview': w.get('preview', ''),
        })

    body = """
  <section class="tab-panel is-active">
    <div class="eyebrow">Wiki · Fandom FR · """ + str(len(WIKI_PAGES)) + """ pages</div>
    <h1>Wiki Renegade Immortal</h1>
    <p style="max-width: 60ch;">Encyclopédie complète issue du wiki Fandom officiel — personnages, lieux, royaumes de cultivation, techniques, objets, sectes, artefacts, etc. Cliquez sur une tuile pour ouvrir la page dédiée.</p>
    <div class="divider"><span>Recherche</span></div>
    <div class="toolbar">
      <div class="search" style="flex: 2;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><line x1="20" y1="20" x2="16.65" y2="16.65"></line></svg>
        <input id="wiki-search" type="search" placeholder="Chercher dans le wiki (persos, lieux, techniques, objets...)" autocomplete="off" />
      </div>
      <div class="filter wiki-cat-filter">
        <span>Catégorie</span>
        <select id="wiki-cat-filter" aria-label="Filtrer par catégorie">
          <option value="all">Toutes les catégories</option>
        </select>
      </div>
      <div class="wiki-stats" id="wiki-stats"></div>
    </div>
    <div class="wiki-grid" id="wiki-grid"></div>
    <div class="empty" id="wiki-empty" hidden>Aucune page ne correspond à votre recherche.</div>
  </section>
"""
    # Inline only the slim wiki data
    data_inline = json.dumps({'chapters': [], 'wiki': slim_wiki}, ensure_ascii=False)
    html = page_html("Wiki", body, nav_active='wiki', data_inline=data_inline)
    write('wiki.html', html)
    print('  ✓ wiki.html (with slim wiki data)')


def build_404():
    body = """
  <section class="tab-panel is-active" style="text-align: center; padding: 80px 24px;">
    <div style="font-size: 4rem; color: var(--crimson); font-family: 'Cinzel', serif;">404</div>
    <h1>Page introuvable</h1>
    <p style="color: var(--ink-3); max-width: 40ch; margin: 16px auto;">La page que vous cherchez n'existe pas ou a été déplacée.</p>
    <a href="index.html" class="btn" style="display:inline-block;margin-top:14px;padding:10px 20px;border:1px solid var(--crimson-dim);background:linear-gradient(180deg,var(--crimson),var(--crimson-dim));color:#fff;font-family:'Cinzel',serif;font-size:11px;letter-spacing:.2em;text-transform:uppercase;border-radius:var(--r-md);">← Retour à l'accueil</a>
  </section>
"""
    html = page_html("Page introuvable", body)
    write('404.html', html)
    print('  ✓ 404.html')


def main():
    if '--clean' in sys.argv and SITE.exists():
        shutil.rmtree(SITE)
        print(f'Cleaned {SITE}')

    SITE.mkdir(parents=True, exist_ok=True)
    # Copy static assets
    for sub in ['assets', 'wiki', 'traduction']:
        src = ROOT / sub
        dst = SITE / sub
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f'  copied {sub}/')

    # Copy root files
    for f in ['LICENSE.txt', 'LICENSE-traduction.txt', '.nojekyll', 'README.md']:
        src = ROOT / f
        if src.exists():
            shutil.copy2(src, SITE / f)
            print(f'  copied {f}')

    print('\n=== Building pages ===')
    build_home()
    build_chapters_index()
    build_univers()
    build_characters_index()
    build_wiki_index()
    build_404()

    # Books and chapters
    print('\n=== Building books + chapters ===')
    by_book = {}
    for c in CHAPTERS:
        by_book.setdefault(c['book'], []).append(c)
    for b in sorted(by_book.keys()):
        chs = by_book[b]
        build_book_page(b, chs)
        # Build each chapter page
        for i, c in enumerate(chs):
            prev_c = chs[i-1] if i > 0 else None
            next_c = chs[i+1] if i < len(chs)-1 else None
            build_chapter_page(c, prev_c, next_c)
        print(f'  ✓ Tome {b} ({len(chs)} chapters)')

    # Characters
    print('\n=== Building characters ===')
    data = json.loads((ASSETS / 'data.json').read_text(encoding='utf-8'))
    for key in ['wang', 'situ', 'limuwan']:
        build_character_page(key, data['characters'][key], data['images'], data['urls'])
        print(f'  ✓ {key}')

    # Wiki pages (2285)
    build_wiki_pages()

    print('\n=== DONE ===')
    total_files = sum(1 for _ in SITE.rglob('*') if _.is_file())
    print(f'  Total files: {total_files:,}')
    total_size = sum(f.stat().st_size for f in SITE.rglob('*') if f.is_file())
    print(f'  Total size : {total_size/1024/1024:.1f} MB')



def build_wiki_pages():
    """Generate one page per wiki entry."""
    out_dir = SITE / 'wiki'
    out_dir.mkdir(parents=True, exist_ok=True)
    print('\n=== Building wiki pages (' + str(len(WIKI_PAGES)) + ' pages) ===')
    errors = 0
    for i, meta in enumerate(WIKI_PAGES):
        slug = slugify(meta['name'])
        if not slug:
            slug = 'page-' + meta['name'][:20]
        # Read the page JSON
        page_data = None
        wp_file = WIKI / (meta['name'] + '.json')
        if wp_file.exists():
            try:
                page_data = json.loads(wp_file.read_text(encoding='utf-8'))
            except: pass
        if not page_data and meta.get('sub'):
            for f in WIKI.iterdir():
                if f.stem == meta['name']:
                    try:
                        page_data = json.loads(f.read_text(encoding='utf-8'))
                        break
                    except: pass
        if page_data:
            html_body = build_wiki_page_html(page_data, meta)
        else:
            html_body = '<p>Page non disponible.</p>'
        full_html = page_html(meta['name'], html_body, base='../', nav_active='wiki')
        out_path = 'wiki/' + slug + '.html'
        try:
            write(out_path, full_html)
        except OSError as e:
            errors += 1
            if errors < 5:
                print('  ! ' + meta['name'] + ': ' + str(e))
            continue
        if (i + 1) % 500 == 0:
            print('  ' + str(i + 1) + '/' + str(len(WIKI_PAGES)) + ' wiki pages...')
    if errors > 0:
        print('  total errors: ' + str(errors))


def build_wiki_page_html(data, meta):
    """Render a wiki page from its JSON data."""
    content = data.get('content', '')
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

    # Image gallery
    gallery_html = ''
    images = meta.get('images', [])
    if images:
        real = [im for im in images if 'no-image' not in im['name'].lower() and 'no_image' not in im['name'].lower()]
        if real:
            shown = real[:6]
            more = len(real) - len(shown)
            parts = []
            for i, im in enumerate(shown):
                cls = ' is-main' if i == 0 else ''
                label = '<span class="wiki-gallery-label">Image principale</span>' if i == 0 else ''
                parts.append('<a href="../' + im['path'] + '" target="_blank" rel="noopener" class="wiki-gallery-item' + cls + '"><img src="../' + im['path'] + '" alt="' + esc(im['name']) + '" loading="lazy" onerror="this.parentNode.style.display=' + "'none'" + '"/>' + label + '</a>')
            gallery_html = '<div class="wiki-gallery">' + ''.join(parts)
            if more > 0:
                gallery_html += '<div class="wiki-gallery-more">+' + str(more) + ' autres</div>'
            gallery_html += '</div>'

    # Sections
    sect_html = ''
    for j, (title, paras) in enumerate(sections):
        if not paras: continue
        is_first = (j == 0)
        heading = '<h2>' + esc(title) + '</h2>' if is_first else '<h3>' + esc(title) + '</h3>'
        sect_html += heading + ''.join('<p>' + esc(p) + '</p>' for p in paras)

    cats = ''.join('<span class="cat">' + esc(c) + '</span>' for c in meta.get('categories', [])[:8])

    extra = ''
    if data.get('title') in ('Xian Ni', 'Xian Ni Wikia', 'Renegade Immortal'):
        extra = '<div class="wiki-external-sources"><h3>Sources complémentaires (FR)</h3><p>Pour aller plus loin :</p><ul><li><a class="fandom-link" href="https://baike.baidu.com/fr/item/Immortel%20Ren%C3%A9gat/1295062" target="_blank" rel="noopener">Baidu Encyclopédie</a></li><li><a class="fandom-link" href="https://cultivationfr.com/2026/01/renegade-immortal/" target="_blank" rel="noopener">CultivationFR</a></li></ul></div>'

    return '\n  <section class="tab-panel is-active">\n    <nav class="breadcrumb"><a href="../wiki.html">← Wiki</a></nav>\n    <div class="wiki-reader-section">\n      <h2>' + esc(data.get("title", meta["name"])) + '</h2>\n      <div class="wikicats">' + cats + '</div>\n      <a class="fandom-link" href="' + esc(meta.get("url", "")) + '" target="_blank" rel="noopener" style="font-size:13px;">Voir sur Fandom Wiki →</a>\n      ' + gallery_html + '\n      ' + sect_html + '\n      ' + extra + '\n    </div>\n  </section>\n'


if __name__ == '__main__':
    main()
