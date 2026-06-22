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


def page_html(title, body, base='', nav_active='', data_inline='', extra_css='', extra_js='', home_only=False):
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
<body class="is-home">
<header class="nav"
  <div class="nav-inner">
    <a href="{base}index.html" class="brand" aria-label="Renegade Immortal FR — accueil">
      <span class="dot" aria-hidden="true"></span>
      <span>Renegade Immortal</span>
      <small>· Xian Ni · 仙逆</small>
    </a>
    <button class="nav-burger" id="nav-burger" aria-label="Ouvrir le menu" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <nav class="nav-tabs" id="nav-tabs" role="navigation" aria-label="Sections principales">
      <a href="{base}index.html" class="nav-tab{' is-active' if nav_active == 'home' else ''}">Accueil</a>
      <a href="{base}chapitres.html" class="nav-tab{' is-active' if nav_active == 'chapters' else ''}">Chapitres</a>
      <a href="{base}personnages.html" class="nav-tab{' is-active' if nav_active == 'characters' else ''}">Personnages</a>
      <a href="{base}cultivation.html" class="nav-tab{' is-active' if nav_active == 'cultivation' else ''}">Cultivation</a>
      <a href="{base}sectes-clans.html" class="nav-tab{' is-active' if nav_active == 'sectes' else ''}">Sectes &amp; Clans</a>
      <a href="{base}lieux.html" class="nav-tab{' is-active' if nav_active == 'lieux' else ''}">Lieux</a>
      <a href="{base}livre.html" class="nav-tab{' is-active' if nav_active == 'livre' else ''}">Livre</a>
      
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
<!-- Gesture hint: only show on home -->
<div class="gesture-hint" id="gesture-hint" data-home-only="true" role="dialog" aria-label="Entrer">
  <div class="gesture-hint-inner">
    <div class="gesture-hint-glyph">仙</div>
    <div class="gesture-hint-cta">
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
      <span>Entrer</span>
    </div>
  </div>
</div>
<button class="theme-toggle" id="theme-toggle" aria-label="Basculer thème clair/sombre" title="Thème clair/sombre">☀</button>
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
    """Find a local image for a wiki page, preferring WebP for size."""
    img_dir = WIKI / 'images'
    if not img_dir.exists(): return ''
    name_lower = page['name'].lower()
    # First pass: exact match, prefer .webp
    candidates = [f for f in img_dir.iterdir() if f.stem.lower() == name_lower]
    webp = [c for c in candidates if c.suffix.lower() == '.webp']
    if webp: return f'wiki/images/{urllib.parse.quote(webp[0].name)}'
    if candidates: return f'wiki/images/{urllib.parse.quote(candidates[0].name)}'
    # Second pass: partial match
    candidates = [f for f in img_dir.iterdir() if name_lower in f.stem.lower() or f.stem.lower() in name_lower]
    webp = [c for c in candidates if c.suffix.lower() == '.webp']
    if webp: return f'wiki/images/{urllib.parse.quote(webp[0].name)}'
    if candidates: return f'wiki/images/{urllib.parse.quote(candidates[0].name)}'
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
    """Home: animated Yin-Yang + River + Ash + 6 tile cards for onglets."""
    body = """
  <canvas id="bg-canvas" aria-hidden="true"></canvas>
  <svg class="yinyang" viewBox="-100 -100 200 200" aria-hidden="true">
    <defs>
      <clipPath id="yin-clip"><circle cx="0" cy="0" r="100"/></clipPath>
    </defs>
    <g clip-path="url(#yin-clip)">
      <circle cx="0" cy="0" r="100" fill="var(--mystic)"/>
      <path d="M 0 -100 A 50 50 0 0 0 0 0 A 50 50 0 0 0 0 100 A 100 100 0 0 1 0 -100" fill="var(--crimson)"/>
      <circle cx="0" cy="-50" r="14" fill="var(--mystic)"/>
      <circle cx="0" cy="50" r="14" fill="var(--crimson)"/>
      <circle cx="0" cy="-50" r="5" fill="var(--crimson)"/>
      <circle cx="0" cy="50" r="5" fill="var(--mystic)"/>
    </g>
  </svg>
  <svg class="river" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <path d="M -100 600 Q 200 500 400 550 T 800 450 T 1300 500" fill="none" stroke="var(--mystic-2)" stroke-width="2" opacity="0.3"/>
    <path d="M -100 650 Q 200 580 400 600 T 800 530 T 1300 560" fill="none" stroke="var(--crimson-2)" stroke-width="1.5" opacity="0.2"/>
  </svg>

  <div class="home-content">
    <header class="home-hero">
      <div class="home-hero-cover">
        <div class="home-hero-cover-frame">
          <img src="wiki/images/Wang Lin Manhua Nascent Soul.webp" alt="Wang Lin, protagoniste de Xian Ni / Renegade Immortal" loading="eager" />
          <div class="home-hero-cover-glow" aria-hidden="true"></div>
        </div>
        <div class="home-hero-cover-caption">
          <span class="cap-name">Wang Lin</span>
          <span class="cap-role">Protagoniste · Cultivateur</span>
        </div>
      </div>

      <div class="home-hero-text">
        <div class="home-eyebrow">仙逆 Xian Ni · Web Novel · Traduction française</div>
        <h1 class="home-title">Immortel</h1>
        <p class="home-tagline">L'odyssée d'un jeune orphelin devenu démon, forgeant son destin entre ciel et terre, là où les mortels défient l'ordre des Immortels.</p>

        <div class="home-synopsis">
          <p>Sorti de son village avec rien d'autre qu'un héritage brisé et une volonté de fer, <strong>Wang Lin</strong> s'élève à travers les royaumes de cultivation — disciple méprisé, traître présumé, vagabond solitaire — jusqu'à devenir l'une des figures les plus redoutables du cosmos.</p>
          <p>Parmi les sectes qui s'effondrent, les clans ancestraux et les guerres entre Immortels, sa route n'est jamais droite. Il tue pour protéger ce qu'il aime. Il trahit pour survivre. Il attend, pendant des siècles, ce que d'autres ont oublié.</p>
          <p><em>Renegade Immortal</em> (仙逆) est l'un des monuments du xianxia moderne : une fresque de 2 088 chapitres où chaque transgression a un prix, et où la vraie immortalité n'est jamais celle qu'on croit.</p>
        </div>

        <div class="home-stats">
          <div class="stat">
            <div class="stat-num">2 088</div>
            <div class="stat-label">Chapitres</div>
          </div>
          <div class="stat-sep" aria-hidden="true"></div>
          <div class="stat">
            <div class="stat-num">13</div>
            <div class="stat-label">Tomes</div>
          </div>
          <div class="stat-sep" aria-hidden="true"></div>
          <div class="stat">
            <div class="stat-num">80+</div>
            <div class="stat-label">Personnages</div>
          </div>
          <div class="stat-sep" aria-hidden="true"></div>
          <div class="stat">
            <div class="stat-num">9</div>
            <div class="stat-label">Royaumes</div>
          </div>
        </div>

        <div class="home-hero-cta">
          <a href="livre.html" class="hero-cta">Commencer la lecture →</a>
          <a href="personnages.html" class="hero-cta hero-cta-ghost">Découvrir les personnages</a>
        </div>
      </div>
    </header>

    <div class="home-grid">
      <a class="home-tile" href="livre.html" data-href="livre.html">
        <div class="home-tile-bg" style="background-image:url('wiki/images/Disciple Wang.webp')"></div>
        <div class="home-tile-overlay"></div>
        <div class="home-tile-content">
          <div class="home-tile-num">I</div>
          <h2>Livre</h2>
          <div class="home-tile-sub">13 tomes · 2,088 chapitres</div>
        </div>
      </a>
      <a class="home-tile" href="chapitres.html" data-href="chapitres.html">
        <div class="home-tile-bg" style="background-image:url('wiki/images/0owanga1.webp')"></div>
        <div class="home-tile-overlay"></div>
        <div class="home-tile-content">
          <div class="home-tile-num">II</div>
          <h2>Chapitres</h2>
          <div class="home-tile-sub">Lecture · 13 livres</div>
        </div>
      </a>
      <a class="home-tile" href="personnages.html" data-href="personnages.html">
        <div class="home-tile-bg" style="background-image:url('wiki/images/Situ Nan Game.webp')"></div>
        <div class="home-tile-overlay"></div>
        <div class="home-tile-content">
          <div class="home-tile-num">III</div>
          <h2>Personnages</h2>
          <div class="home-tile-sub">Wang Lin · Situ Nan · Li Muwan</div>
        </div>
      </a>
      <a class="home-tile" href="cultivation.html" data-href="cultivation.html">
        <div class="home-tile-bg" style="background-image:url('wiki/images/Ascendant.webp')"></div>
        <div class="home-tile-overlay"></div>
        <div class="home-tile-content">
          <div class="home-tile-num">IV</div>
          <h2>Cultivation</h2>
          <div class="home-tile-sub">Royaumes · Techniques</div>
        </div>
      </a>
      <a class="home-tile" href="sectes-clans.html" data-href="sectes-clans.html">
        <div class="home-tile-bg" style="background-image:url('wiki/images/Heng Yue Sect.webp')"></div>
        <div class="home-tile-overlay"></div>
        <div class="home-tile-content">
          <div class="home-tile-num">V</div>
          <h2>Sectes &amp; Clans</h2>
          <div class="home-tile-sub">Heng Yue · Cloud Sky · …</div>
        </div>
      </a>
      <a class="home-tile" href="lieux.html" data-href="lieux.html">
        <div class="home-tile-bg" style="background-image:url('wiki/images/Planet Suzaku.webp')"></div>
        <div class="home-tile-overlay"></div>
        <div class="home-tile-content">
          <div class="home-tile-num">VI</div>
          <h2>Lieux</h2>
          <div class="home-tile-sub">Planètes · Royaumes</div>
        </div>
      </a>
    </div>
  </div>
"""
    extra_css = """
  /* HOME: animated background + tile grid */
  #bg-canvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: 0.7; }

  .yinyang {
    position: fixed;
    top: 50%; right: 8%;
    width: 520px; height: 520px;
    transform: translateY(-50%);
    z-index: 0; opacity: 0.18;
    animation: yinyang-rotate 60s linear infinite;
    filter: drop-shadow(0 0 30px rgba(74,110,216,.4));
  }
  @keyframes yinyang-rotate {
    from { transform: translateY(-50%) rotate(0deg); }
    to { transform: translateY(-50%) rotate(360deg); }
  }

  .river {
    position: fixed; inset: 0;
    width: 100%; height: 100%;
    z-index: 0; opacity: 0.5;
    animation: river-flow 30s ease-in-out infinite;
  }
  .river path:nth-child(1) { animation: river-dash-1 8s linear infinite; }
  .river path:nth-child(2) { animation: river-dash-2 12s linear infinite; }
  @keyframes river-dash-1 { to { stroke-dashoffset: -200; } }
  @keyframes river-dash-2 { to { stroke-dashoffset: 200; } }
  @keyframes river-flow { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-30px); } }

  .home-content {
    position: relative; z-index: 2;
    min-height: 100vh;
    display: flex; flex-direction: column;
    padding: 60px 24px 80px;
    max-width: 1280px; margin: 0 auto;
  }

  /* HOME — Hero (2 cols: cover + text) */
  .home-hero {
    display: grid;
    grid-template-columns: minmax(260px, 360px) 1fr;
    gap: 56px;
    align-items: center;
    margin-bottom: 64px;
    padding: 32px 0 8px;
  }

  .home-hero-cover { position: relative; }
  .home-hero-cover-frame {
    position: relative;
    aspect-ratio: 3 / 4;
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--bg-2);
    box-shadow:
      0 24px 60px -20px rgba(0,0,0,.8),
      0 0 0 1px rgba(200,164,74,.15);
  }
  .home-hero-cover-frame img {
    width: 100%; height: 100%;
    object-fit: cover; object-position: center top;
    display: block;
    transition: transform .8s var(--ease);
  }
  .home-hero-cover-frame:hover img { transform: scale(1.04); }
  .home-hero-cover-glow {
    position: absolute; inset: -20px;
    background: radial-gradient(ellipse at center, rgba(200,164,74,.18) 0%, transparent 60%);
    z-index: -1;
    pointer-events: none;
    animation: cover-glow-pulse 4s ease-in-out infinite;
  }
  @keyframes cover-glow-pulse {
    0%, 100% { opacity: .7; }
    50% { opacity: 1; }
  }
  .home-hero-cover-caption {
    margin-top: 14px;
    text-align: center;
    font-family: 'Cinzel', serif;
  }
  .home-hero-cover-caption .cap-name {
    display: block;
    font-size: 14px;
    letter-spacing: .25em;
    color: var(--crimson-2);
    text-transform: uppercase;
  }
  .home-hero-cover-caption .cap-role {
    display: block;
    margin-top: 4px;
    font-size: 10px;
    letter-spacing: .35em;
    color: var(--ink-2);
    text-transform: uppercase;
    opacity: .7;
  }

  .home-hero-text { min-width: 0; }
  .home-eyebrow {
    font-family: 'Cinzel', serif; font-size: 11px;
    letter-spacing: .4em; text-transform: uppercase;
    color: var(--crimson-2);
    margin-bottom: 16px;
  }
  .home-title {
    font-size: clamp(2.6rem, 7vw, 4.5rem);
    line-height: 1; margin: 0 0 18px;
    background: linear-gradient(180deg, #f3e7c8 0%, #c8a44a 50%, #7a6326 100%);
    -webkit-background-clip: text; background-clip: text;
    color: transparent;
    text-shadow: 0 0 30px rgba(200,164,74,.2);
    letter-spacing: .04em;
  }
  .home-tagline {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic; font-size: clamp(1.05rem, 2vw, 1.3rem);
    color: var(--ink-2);
    max-width: 56ch; margin: 0 0 28px;
    line-height: 1.45;
  }

  .home-synopsis {
    color: var(--ink-2);
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 28px;
  }
  .home-synopsis p { margin: 0 0 14px; }
  .home-synopsis p:last-child { margin-bottom: 0; }
  .home-synopsis strong { color: var(--ink); font-weight: 600; }
  .home-synopsis em { color: var(--crimson-2); font-style: italic; }

  .home-stats {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 18px 22px;
    margin-bottom: 28px;
    background: linear-gradient(180deg, rgba(200,164,74,.05) 0%, rgba(200,164,74,.02) 100%);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
  }
  .home-stats .stat { flex: 1; text-align: center; }
  .home-stats .stat-num {
    font-family: 'Cinzel', serif;
    font-size: clamp(1.3rem, 2.4vw, 1.7rem);
    font-weight: 600;
    color: var(--crimson-2);
    line-height: 1;
  }
  .home-stats .stat-label {
    font-family: 'Cinzel', serif;
    font-size: 9.5px;
    letter-spacing: .25em;
    text-transform: uppercase;
    color: var(--ink-2);
    margin-top: 6px;
    opacity: .8;
  }
  .home-stats .stat-sep {
    width: 1px; height: 32px;
    background: var(--line);
    opacity: .5;
  }

  .home-hero-cta {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
  }
  .home-hero-cta .hero-cta { margin-top: 0; }

  @media (max-width: 880px) {
    .home-hero {
      grid-template-columns: 1fr;
      gap: 32px;
      text-align: center;
    }
    .home-hero-cover { max-width: 280px; margin: 0 auto; }
    .home-hero-text { text-align: left; }
    .home-tagline { margin-left: auto; margin-right: auto; }
    .home-stats { flex-wrap: wrap; }
    .home-stats .stat { min-width: 80px; }
    .home-stats .stat-sep:nth-of-type(2n) { display: none; }
  }

  .home-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    flex: 1;
  }
  .home-tile {
    position: relative; display: block;
    aspect-ratio: 4 / 5;
    background: var(--bg-2);
    border: 1px solid var(--line);
    overflow: hidden;
    color: #fff; text-decoration: none;
    transition: transform .35s var(--ease), border-color .3s, box-shadow .3s;
    cursor: pointer;
  }
  .home-tile:hover {
    transform: translateY(-6px) scale(1.02);
    border-color: var(--crimson-dim);
    box-shadow: 0 16px 40px -8px rgba(179,38,30,.5), 0 0 0 1px var(--crimson-dim);
  }
  .home-tile-bg {
    position: absolute; inset: 0;
    background-size: cover; background-position: center;
    transition: transform .8s var(--ease);
  }
  .home-tile:hover .home-tile-bg { transform: scale(1.1); }
  .home-tile-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(7,6,10,.3) 0%, rgba(7,6,10,.4) 40%, rgba(7,6,10,.95) 100%);
  }
  .home-tile-content {
    position: absolute; left: 0; right: 0; bottom: 0;
    padding: 22px 24px;
  }
  .home-tile-num {
    font-family: 'Cinzel', serif; font-size: 10.5px;
    letter-spacing: .3em; text-transform: uppercase;
    color: var(--crimson-2);
    margin-bottom: 8px;
    text-shadow: 0 0 8px rgba(0,0,0,.8);
  }
  .home-tile-content h2 {
    font-size: clamp(1.3rem, 3vw, 1.8rem);
    color: #fff; margin: 0 0 6px;
    line-height: 1.1;
    text-shadow: 0 2px 12px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.7);
    letter-spacing: .04em;
  }
  .home-tile-sub {
    font-family: 'Cinzel', serif; font-size: 10px;
    letter-spacing: .15em; text-transform: uppercase;
    color: var(--ink-2);
    text-shadow: 0 1px 4px rgba(0,0,0,.8);
  }

  @media (max-width: 880px) {
    .yinyang { width: 280px; height: 280px; right: -100px; opacity: 0.12; }
    .home-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .home-content { padding: 40px 16px 60px; }
  }
  @media (max-width: 540px) {
    .yinyang { display: none; }
    .home-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    .home-tile { aspect-ratio: 1; }
  }
  /* Gesture hint only on home */
  body:not(.is-home) .gesture-hint { display: none !important; }
  /* Hero CTA */
  .hero-cta { display: inline-block; padding: 12px 28px; border: 1px solid var(--crimson-dim); background: linear-gradient(180deg, var(--crimson), var(--crimson-dim)); color: #fff; font-family: 'Cinzel', serif; font-size: 12px; letter-spacing: .25em; text-transform: uppercase; border-radius: var(--r-md); transition: transform .2s, box-shadow .2s, background .2s, color .2s; text-decoration: none; }
  .hero-cta:hover { transform: translateY(-1px); box-shadow: 0 8px 24px -8px rgba(179,38,30,.7); }
  .hero-cta-ghost { background: transparent; color: var(--ink); border-color: var(--line); }
  .hero-cta-ghost:hover { background: rgba(200,164,74,.08); border-color: var(--crimson-dim); color: var(--crimson-2); box-shadow: none; }

"""
    extra_js = '<script src="home-bg.js" defer></script>'
    html = page_html('Accueil', body, nav_active='home', extra_css=extra_css, extra_js=extra_js, home_only=True)
    write('index.html', html)
    print('  ✓ index.html (Yin-Yang + River + Ash + 6 tile cards)')


def build_livre():
    """Livre onglet: 13 tome tiles with local book cover images."""
    by_book = {}
    for c in CHAPTERS:
        by_book.setdefault(c['book'], []).append(c)
    book_tiles = ''
    for b in sorted(by_book.keys()):
        chs = by_book[b]
        first = chs[0]
        link = chapter_path(b, first['bookTitle'], first['n'], first['title']).rsplit('/', 1)[0] + '.html'
        cover = f'wiki/images/Book {b}.webp'
        book_tiles += f"""
        <a class="livre-tile" href="{link}">
          <div class="livre-tile-bg" style="background-image:url('{cover}')"></div>
          <div class="livre-tile-overlay"></div>
          <div class="livre-tile-content">
            <div class="livre-tile-num">Tome {b}</div>
            <h3>{esc(first['bookTitle'])}</h3>
            <div class="livre-tile-stats">{len(chs)} chapitres</div>
          </div>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <div class="themed-header"><h1>Livre</h1></div>
    <div class="livre-grid" role="list">{book_tiles}</div>
  </section>
"""
    extra_css = """
  .themed-header { margin: 12px 0 24px; text-align: center; }
  .themed-header h1 { font-size: clamp(1.6rem, 4vw, 2.2rem); margin: 0 auto; max-width: 32ch; }
  .livre-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
  .livre-tile { position: relative; display: block; aspect-ratio: 3 / 4; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; color: #fff; text-decoration: none; transition: transform .3s var(--ease), border-color .3s, box-shadow .3s; }
  .livre-tile:hover { transform: translateY(-4px); border-color: var(--crimson-dim); box-shadow: 0 12px 28px -8px rgba(0,0,0,.6); }
  .livre-tile-bg { position: absolute; inset: 0; background-size: cover; background-position: center; transition: transform .6s var(--ease); background-color: var(--bg-3); }
  .livre-tile:hover .livre-tile-bg { transform: scale(1.08); }
  .livre-tile-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 30%, rgba(7,6,10,.9) 100%); }
  .livre-tile-content { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 20px; }
  .livre-tile-num { font-family: 'Cinzel', serif; font-size: 10.5px; letter-spacing: .3em; text-transform: uppercase; color: var(--crimson-2); margin-bottom: 6px; text-shadow: 0 1px 4px rgba(0,0,0,.8); }
  .livre-tile-content h3 { font-size: 1.1rem; color: #fff; margin: 0 0 6px; line-height: 1.2; text-shadow: 0 2px 8px rgba(0,0,0,.9); }
  .livre-tile-stats { font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-2); text-shadow: 0 1px 4px rgba(0,0,0,.8); }
  @media (max-width: 540px) { .livre-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; } }
"""
    html = page_html('Le Livre', body, nav_active='livre', extra_css=extra_css)
    write('livre.html', html)
    print('  ✓ livre.html (13 tome tiles, no prose)')


def build_themed_page(category_key, title, top_pages, nav_active):
    """Onglet page: only tiles (image background + title). No text intro."""
    tiles = ''
    for p in top_pages:
        slug = slugify(p['name'])
        img = find_image_for_page(p)
        tiles += f"""
        <a class="themed-tile" href="{category_key}/{slug}.html">
          <div class="themed-tile-bg" style="background-image:url('{img}')"></div>
          <div class="themed-tile-overlay"></div>
          <div class="themed-tile-content">
            <h3>{esc(p['title'])}</h3>
          </div>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <div class="themed-header">
      <h1>{esc(title)}</h1>
    </div>
    <div class="themed-grid" role="list">{tiles}</div>
  </section>
"""
    extra_css = """
  .themed-header { margin: 12px 0 24px; }
  .themed-header h1 { font-size: clamp(1.6rem, 4vw, 2.2rem); margin: 0; }
  .themed-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
  .themed-tile { position: relative; display: block; aspect-ratio: 4 / 5; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; color: #fff; text-decoration: none; transition: transform .3s var(--ease), border-color .3s, box-shadow .3s; }
  .themed-tile:hover { transform: translateY(-4px); border-color: var(--crimson-dim); box-shadow: 0 12px 28px -8px rgba(0,0,0,.6); }
  .themed-tile-bg { position: absolute; inset: 0; background-size: cover; background-position: center top; transition: transform .6s var(--ease); background-color: var(--bg-3); }
  .themed-tile:hover .themed-tile-bg { transform: scale(1.08); }
  .themed-tile-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 30%, rgba(7,6,10,.88) 100%); }
  .themed-tile-content { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 20px; }
  .themed-tile-content h3 { font-size: 1.1rem; color: #fff; margin: 0; line-height: 1.2; text-shadow: 0 2px 8px rgba(0,0,0,.9); }
  @media (max-width: 540px) {
    .themed-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .themed-tile { aspect-ratio: 1; }
  }
"""
    html = page_html(title, body, nav_active=nav_active, extra_css=extra_css)
    write(f'{category_key}.html', html)
    print(f'  ✓ {category_key}.html ({len(top_pages)} tiles)')


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
    """Personnages onglet: only tiles (3 main + 12 curated = 15 total)."""
    data = load_main_characters()
    buckets = categorize_wiki()
    all_chars = []
    # 3 main first
    if data:
        for key in ['wang', 'situ', 'limuwan']:
            if key not in data['characters']: continue
            c = data['characters'][key]
            all_chars.append({
                'name': c['title'],
                'slug': slugify(c['title']),
                'image': data['images'][key],
                'is_main': True,
            })
    # Then curated wiki
    for p in curate_top(buckets['personnages'], 12):
        if p['name'] in ('Wang Lin', 'Situ Nan', 'Li Muwan', 'Li MuWan'): continue
        all_chars.append({
            'name': p['title'],
            'slug': slugify(p['name']),
            'image': find_image_for_page(p),
            'is_main': False,
        })

    tiles = ''
    for c in all_chars:
        tiles += f"""
        <a class="themed-tile" href="personnages/{c['slug']}.html">
          <div class="themed-tile-bg" style="background-image:url('{c['image']}')"></div>
          <div class="themed-tile-overlay"></div>
          <div class="themed-tile-content">
            <h3>{esc(c['name'])}</h3>
          </div>
        </a>"""
    body = f"""
  <section class="tab-panel is-active">
    <div class="themed-header"><h1>Personnages</h1></div>
    <div class="themed-grid" role="list">{tiles}</div>
  </section>
"""
    extra_css = """
  .themed-header { margin: 12px 0 24px; }
  .themed-header h1 { font-size: clamp(1.6rem, 4vw, 2.2rem); margin: 0; }
  .themed-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
  .themed-tile { position: relative; display: block; aspect-ratio: 4 / 5; background: var(--bg-2); border: 1px solid var(--line); overflow: hidden; color: #fff; text-decoration: none; transition: transform .3s var(--ease), border-color .3s, box-shadow .3s; }
  .themed-tile:hover { transform: translateY(-4px); border-color: var(--crimson-dim); box-shadow: 0 12px 28px -8px rgba(0,0,0,.6); }
  .themed-tile-bg { position: absolute; inset: 0; background-size: cover; background-position: center top; transition: transform .6s var(--ease); background-color: var(--bg-3); }
  .themed-tile:hover .themed-tile-bg { transform: scale(1.08); }
  .themed-tile-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 30%, rgba(7,6,10,.9) 100%); }
  .themed-tile-content { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 20px; }
  .themed-tile-content h3 { font-size: 1.1rem; color: #fff; margin: 0; line-height: 1.2; text-shadow: 0 2px 8px rgba(0,0,0,.9); }
  @media (max-width: 540px) { .themed-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; } .themed-tile { aspect-ratio: 1; } }
"""
    html = page_html('Personnages', body, nav_active='characters', extra_css=extra_css)
    write('personnages.html', html)
    print(f'  ✓ personnages.html ({len(all_chars)} tiles)')


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
HOME_BG_JS = r'''// home-bg.js — Animated background for the home page
(function() {
  const canvas = document.getElementById('bg-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let W, H;
    const ASH_COUNT = 80;
    const ashes = [];
    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);
    for (let i = 0; i < ASH_COUNT; i++) {
      ashes.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.15,
        vy: -Math.random() * 0.5 - 0.1,
        r: Math.random() * 1.4 + 0.4,
        opacity: Math.random() * 0.4 + 0.1,
        isGold: Math.random() < 0.3,
        phase: Math.random() * Math.PI * 2
      });
    }
    function drawAsh() {
      ctx.clearRect(0, 0, W, H);
      for (const a of ashes) {
        a.x += a.vx + Math.sin(a.phase + performance.now() / 2000) * 0.3;
        a.y += a.vy;
        if (a.y < -10) { a.y = H + 10; a.x = Math.random() * W; }
        if (a.x < -10) a.x = W + 10;
        if (a.x > W + 10) a.x = -10;
        const color = a.isGold
          ? 'rgba(200, 164, 74, ' + a.opacity + ')'
          : 'rgba(214, 58, 46, ' + a.opacity + ')';
        ctx.beginPath();
        ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        const grad = ctx.createRadialGradient(a.x, a.y, 0, a.x, a.y, a.r * 2.5);
        grad.addColorStop(0, color);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fill();
      }
      requestAnimationFrame(drawAsh);
    }
    drawAsh();
  }
  document.querySelectorAll('.home-tile').forEach(function(card) {
    card.addEventListener('click', function() {
      var href = card.getAttribute('href');
      if (href && href !== '#') window.location.href = href;
    });
  });
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
    # Curated tiles per category (max 15 per category for the home)
    # Plus separately, the entry pages cover more (up to 30)
    build_themed_page('cultivation', 'Cultivation', curate_top(buckets['cultivation'], 15), 'cultivation')
    build_themed_page('sectes-clans', 'Sectes & Clans', curate_top(buckets['sectes'], 15), 'sectes')
    build_themed_page('lieux', 'Lieux', curate_top(buckets['lieux'], 15), 'lieux')
    build_themed_page('wiki', 'Wiki', curate_top(buckets['personnages'] + buckets['cultivation'] + buckets['sectes'] + buckets['lieux'], 20), 'wiki')

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
