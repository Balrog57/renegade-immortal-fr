
  const CHAPTERS_DATA = JSON.parse(document.getElementById("chapters-data").textContent);
  const WIKI_DATA = JSON.parse(document.getElementById("wiki-data").textContent);
(function () {
  'use strict';

  // ============================================
  // BURGER MENU (mobile)
  // ============================================
  const burger = document.getElementById('nav-burger');
  const navTabs = document.getElementById('nav-tabs');
  if (burger && navTabs) {
    burger.addEventListener('click', () => {
      const open = navTabs.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', String(open));
    });
  }
  // Close mobile menu on link click
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.addEventListener('click', () => {
      if (navTabs) navTabs.classList.remove('is-open');
      if (burger) burger.setAttribute('aria-expanded', 'false');
    });
  });

  // ============================================
  // CHAPTERS — v4 complète, fetch à la demande
  // ============================================
  const CHAPTERS = CHAPTERS_DATA;  // injecté en <script type="application/json">
  const grid      = document.getElementById('chapters-grid');
  const empty     = document.getElementById('chapters-empty');
  const search    = document.getElementById('chapter-search');
  const tomeSel   = document.getElementById('tome-filter');
  const statsEl   = document.getElementById('chapters-stats');
  const reader    = document.getElementById('chapter-reader');
  const readerNum = document.getElementById('reader-chap-num');
  const readerTitle = document.getElementById('reader-chap-title');
  const readerBody  = document.getElementById('reader-body');
  const readerPrev  = document.getElementById('reader-prev');
  const readerNext  = document.getElementById('reader-next');
  const readerClose = document.getElementById('reader-close');
  const MAX_VISIBLE = 250;
  let currentChapIdx = -1;
  let filteredChaps = CHAPTERS.slice();
  // CHAPITRES only on chapitres.html
  if (grid) {

  // populate tome selector
  const bookTitles = {};
  CHAPTERS.forEach(c => { bookTitles[c.book] = c.bookTitle; });
  Object.keys(bookTitles).sort((a, b) => +a - +b).forEach(b => {
    const opt = document.createElement('option');
    opt.value = b;
    opt.textContent = 'Tome ' + b + ' — ' + bookTitles[b] + ' (' + CHAPTERS.filter(c => c.book == b).length + ')';
    tomeSel.appendChild(opt);
  });

  function renderChapters() {
    const q = (search.value || '').toLowerCase().trim();
    const tome = tomeSel.value;
    filteredChaps = CHAPTERS.filter(c => {
      const matchT = tome === 'all' || String(c.book) === tome;
      if (!matchT) return false;
      if (!q) return true;
      const hay = (c.n + ' ' + c.title + ' ' + c.en + ' ' + c.preview).toLowerCase();
      return hay.includes(q);
    });
    statsEl.textContent = filteredChaps.length + ' / ' + CHAPTERS.length + ' chapitres';
    grid.innerHTML = '';
    if (filteredChaps.length === 0) { empty.hidden = false; return; }
    empty.hidden = true;
    const limit = Math.min(filteredChaps.length, MAX_VISIBLE);
    const frag = document.createDocumentFragment();
    for (let i = 0; i < limit; i++) {
      const c = filteredChaps[i];
      const a = document.createElement('a');
      a.className = 'chapter';
      a.setAttribute('role', 'listitem');
      a.href = '#chapitre-' + c.n;
      a.dataset.idx = String(i);
      a.innerHTML = '<span class="title">' + c.title.replace(/</g, '&lt;') + '</span>' +
                    '<span class="arrow" aria-hidden="true">›</span>';
      a.addEventListener('click', (e) => {
        e.preventDefault();
        openChapter(parseInt(a.dataset.idx, 10));
      });
      frag.appendChild(a);
    }
    grid.appendChild(frag);
    if (filteredChaps.length > limit) {
      const note = document.createElement('div');
      note.className = 'empty';
      note.textContent = '... ' + (filteredChaps.length - limit) + ' chapitres supplémentaires. Affinez votre recherche pour en voir plus.';
      grid.appendChild(note);
    }
  }

  function openChapter(idx) {
    if (idx < 0 || idx >= filteredChaps.length) return;
    currentChapIdx = idx;
    const c = filteredChaps[idx];
    readerNum.textContent = 'Tome ' + c.book + ' · Chapitre ' + c.n;
    readerTitle.textContent = c.title;
    readerBody.innerHTML = '<div class="reader-loading">Chargement du chapitre...</div>';
    reader.hidden = false;
    readerPrev.disabled = idx === 0;
    readerNext.disabled = idx === filteredChaps.length - 1;
    reader.scrollIntoView({ behavior: 'smooth', block: 'start' });
    // fetch chapter text
    fetch(c.file, { cache: 'force-cache' })
      .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(text => {
        // retire BOM, split en paragraphes
        text = text.replace(/^\uFEFF/, '');
        const lines = text.split(/\n+/);
        // 1ère ligne = titre (on l'ignore dans le body)
        const paragraphs = lines.slice(1).map(l => l.trim()).filter(l => l.length > 0);
        if (paragraphs.length === 0) {
          readerBody.innerHTML = '<div class="reader-error">Chapitre vide.</div>';
          return;
        }
        const html = paragraphs.map((p, i) =>
          '<p' + (i === 0 ? ' class="lead-paragraph"' : '') + '>' + p.replace(/</g, '&lt;') + '</p>'
        ).join('');
        readerBody.innerHTML = html;
      })
      .catch(err => {
        // Fallback: fetch via file:// interdit → message d'instruction serveur
        readerBody.innerHTML =
          '<div class="reader-error">' +
          '<p><strong>Impossible de charger le contenu</strong> (fetch bloqué en file://).<br>' +
          'Lance le site via un mini serveur HTTP :</p>' +
          '<code>cd &quot;S:\\Livres\\EBOOK\\Renegade Immortal&quot; &amp;&amp; python -m http.server 8000</code>' +
          '<p style="margin-top:14px">Puis ouvre <code>http://localhost:8000/renegade-immortal-fr.html</code></p>' +
          '<p style="margin-top:14px;font-size:12px;color:var(--ink-3);">Erreur technique : ' + (err.message || err) + '</p>' +
          '</div>';
      });
  }

  readerPrev.addEventListener('click', () => openChapter(currentChapIdx - 1));
  readerNext.addEventListener('click', () => openChapter(currentChapIdx + 1));
  readerClose.addEventListener('click', () => { reader.hidden = true; });

  search.addEventListener('input', renderChapters);
  tomeSel.addEventListener('change', renderChapters);
  renderChapters();


  }  // end if (grid) — CHAPITRES

  // ============================================
  // WIKI FAN-DOM — indexation + recherche + lecteur
  // ============================================
  const WIKI = WIKI_DATA;
  const wikiGrid    = document.getElementById('wiki-grid');
  const wikiEmpty   = document.getElementById('wiki-empty');
  const wikiSearch  = document.getElementById('wiki-search');
  const wikiCat     = document.getElementById('wiki-cat-filter');
  const wikiStats   = document.getElementById('wiki-stats');
  const wikiReader  = document.getElementById('wiki-reader');
  const WIKI_PAGE_LIMIT = 200;
  if (wikiGrid) {

  // populate category filter (top 30 cats)
  const catCount = {};
  WIKI.forEach(w => (w.categories || []).forEach(c => { catCount[c] = (catCount[c] || 0) + 1; }));
  const topCats = Object.entries(catCount).sort((a, b) => b[1] - a[1]).slice(0, 30);
  topCats.forEach(([c, n]) => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c + ' (' + n + ')';
    wikiCat.appendChild(opt);
  });

  function renderWiki() {
    const q = (wikiSearch.value || '').toLowerCase().trim();
    const cat = wikiCat.value;
    const filtered = WIKI.filter(w => {
      if (cat !== 'all' && !(w.categories || []).includes(cat)) return false;
      if (!q) return true;
      const hay = (w.name + ' ' + w.title + ' ' + (w.preview || '')).toLowerCase();
      return hay.includes(q);
    });
    wikiStats.textContent = filtered.length + ' / ' + WIKI.length + ' pages';
    wikiGrid.innerHTML = '';
    if (filtered.length === 0) { wikiEmpty.hidden = false; wikiReader.hidden = true; return; }
    wikiEmpty.hidden = true;
    const limit = Math.min(filtered.length, WIKI_PAGE_LIMIT);
    const frag = document.createDocumentFragment();
    for (let i = 0; i < limit; i++) {
      const w = filtered[i];
      const card = document.createElement('article');
      card.className = 'wiki-card';
      card.dataset.name = w.name;
      const catsHtml = (w.categories || []).slice(0, 4).map(c =>
        '<span class="cat' + (i === 0 ? ' is-main' : '') + '">' + c.replace(/</g, '&lt;') + '</span>'
      ).join('');
      card.innerHTML =
        '<div class="name">' + w.name.replace(/</g, '&lt;') + '</div>' +
        '<div class="cats">' + catsHtml + '</div>' +
        (w.preview ? '<div class="preview">' + w.preview.replace(/</g, '&lt;') + '</div>' : '') +
        '<div class="size-hint">' + Math.round(w.size / 1024) + ' KB</div>';
      // Navigate to the dedicated wiki page
      const slug = (w.slug) || w.name.toLowerCase().replace(/[^\w]+/g, '-').replace(/^-|-$/g, '') || 'x';
      card.addEventListener('click', () => { window.location.href = 'wiki/' + slug + '.html'; });
      frag.appendChild(card);
    }
    wikiGrid.appendChild(frag);
    if (filtered.length > limit) {
      const note = document.createElement('div');
      note.className = 'empty';
      note.textContent = '... ' + (filtered.length - limit) + ' pages supplémentaires. Affinez votre recherche.';
      wikiGrid.appendChild(note);
    }
  }

  function openWikiPage(meta) {
    wikiReader.hidden = false;
    wikiReader.innerHTML = '<div class="reader-loading">Chargement de la page wiki : ' + meta.name + '...</div>';
    wikiReader.scrollIntoView({ behavior: 'smooth', block: 'start' });
    fetch(meta.file, { cache: 'force-cache' })
      .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(data => {
        renderWikiPage(data, meta);
      })
      .catch(err => {
        wikiReader.innerHTML =
          '<div class="reader-error">' +
          '<p><strong>Impossible de charger la page wiki</strong> (fetch bloqué en file://).</p>' +
          '<code>cd &quot;S:\\Livres\\EBOOK\\Renegade Immortal&quot; &amp;&amp; python -m http.server 8000</code>' +
          '<p style="margin-top:14px">Puis ouvre <code>http://localhost:8000/renegade-immortal-fr.html</code></p>' +
          '<p style="margin-top:14px;font-size:12px;color:var(--ink-3);">Erreur : ' + (err.message || err) + '</p>' +
          '</div>';
      });
  }

  function renderWikiPage(data, meta) {
    const content = data.content || '';
    // parse sections
    const ovs = [...content.matchAll(/^Overview$/gm)];
    const bodyStart = ovs.length >= 2 ? ovs[1].index : (ovs[0] ? ovs[0].index : 0);
    const body = content.slice(bodyStart).replace(/\[\s*\n\s*\]/g, '');
    const blocks = body.split(/\n\n+/).map(b => b.trim()).filter(Boolean);
    const KNOWN = new Set(['Overview','Personality','Background','History','Appearance','Manhua','Trivia','Links and References','Cultivation','Techniques','Items','Relationships','Fights','Quotes','Image Gallery','Description','Legacy','Abilities','Powers and Abilities','Equipment','Weaknesses','Gallery','Quote']);
    const isTitle = (b) => {
      if (KNOWN.has(b)) return true;
      if (/^Book \d+/.test(b)) return true;
      if (/^Chapter \d+\b/.test(b)) return true;
      if (b.length > 80) return false;
      if (/[.!?,;]$/.test(b)) return false;
      if (!/^[A-Z]/.test(b)) return false;
      if (b.includes(':')) return false;
      if (/^\d+(\.\d+)*$/.test(b)) return false;
      if (/^\[\d+\]$/.test(b)) return false;
      if (/[.!?,;]/.test(b)) return false;
      return true;
    };
    const sections = [];
    let current = null, buf = [];
    for (const b of blocks) {
      if (b === 'Overview' || isTitle(b)) {
        if (current && buf.length) sections.push([current, buf]);
        current = b;
        buf = [];
      } else {
        const cleaned = b.replace(/\[\d+\]/g, '').replace(/\s+/g, ' ').trim();
        if (cleaned.length > 40) buf.push(cleaned);
      }
    }
    if (current && buf.length) sections.push([current, buf]);

    // === Image gallery (from local assets) ===
    let galleryHtml = '';
    if (meta.images && meta.images.length > 0) {
      // Filter out placeholders
      const real = meta.images.filter(img => {
        const n = img.name.toLowerCase();
        return !n.includes('no-image') && !n.includes('no_image');
      });
      if (real.length > 0) {
        // Take up to 6 images
        const shown = real.slice(0, 6);
        const more = real.length - shown.length;
        galleryHtml = '<div class="wiki-gallery">' +
          shown.map((img, i) => {
            const alt = esc(img.name);
            return '<a href="' + img.path + '" target="_blank" rel="noopener" class="wiki-gallery-item' + (i === 0 ? ' is-main' : '') + '">' +
              '<img src="' + img.path + '" alt="' + alt + '" loading="lazy" onerror="this.parentNode.style.display=\'none\'"/>' +
              (i === 0 ? '<span class="wiki-gallery-label">Image principale</span>' : '') +
            '</a>';
          }).join('') +
          (more > 0 ? '<div class="wiki-gallery-more">+' + more + ' autres</div>' : '') +
        '</div>';
      }
    }

    const cats = (meta.categories || []).map(c => '<span class="cat">' + esc(c) + '</span>').join('');
    const sectHtml = sections.map(([title, paras]) => {
      if (paras.length === 0) return '';
      const isFirst = (sections.indexOf([title, paras]) === 0);
      const heading = isFirst ? '<h2>' + esc(title) + '</h2>' : '<h3>' + esc(title) + '</h3>';
      return heading + paras.map(p => '<p>' + esc(p) + '</p>').join('');
    }).join('');

    // === External FR sources footer (only for the main Xian Ni page) ===
    let externalHtml = '';
    if (data.title === 'Xian Ni' || data.title === 'Xian Ni Wikia' || data.title === 'Renegade Immortal') {
      externalHtml = '<div class="wiki-external-sources">' +
        '<h3>Sources complémentaires (FR)</h3>' +
        '<p>Pour aller plus loin, voici des ressources externes sur l\'œuvre :</p>' +
        '<ul>' +
          '<li><a class="fandom-link" href="https://baike.baidu.com/fr/item/Immortel%20Ren%C3%A9gat/1295062" target="_blank" rel="noopener">Baidu Encyclopédie — Immortel Renégat</a> (résumé encyclopédique complet : intrigue, système de cultivation, géographie, factions, personnages)</li>' +
          '<li><a class="fandom-link" href="https://cultivationfr.com/2026/01/renegade-immortal/" target="_blank" rel="noopener">CultivationFR — Présentation complète</a> (analyse éditoriale : ton, univers, héros)</li>' +
        '</ul>' +
      '</div>';
    }

    wikiReader.innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:start;gap:16px;flex-wrap:wrap;">' +
        '<h2>' + esc(data.title) + '</h2>' +
        '<button class="btn" id="wiki-reader-close" style="appearance:none;background:transparent;border:1px solid var(--line);color:var(--ink-2);padding:6px 12px;font-family:Cinzel,serif;font-size:10.5px;letter-spacing:.15em;text-transform:uppercase;cursor:pointer;border-radius:var(--r-md);">Fermer ✕</button>' +
      '</div>' +
      '<div class="wikicats">' + cats + '</div>' +
      (data.url ? '<a class="fandom-link" href="' + esc(data.url) + '" target="_blank" rel="noopener" style="font-size:13px;">Voir sur Fandom Wiki →</a>' : '') +
      galleryHtml +
      sectHtml +
      externalHtml;

    document.getElementById('wiki-reader-close').addEventListener('click', () => {
      wikiReader.hidden = true;
    });
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  wikiSearch.addEventListener('input', renderWiki);
  wikiCat.addEventListener('change', renderWiki);
  renderWiki();

  // Keyboard nav
  const order = ['home', 'chapters', 'characters', 'lore', 'wiki'];
  document.addEventListener('keydown', (e) => {
    if (e.target.matches('input, select, textarea')) return;
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const active = document.querySelector('.nav-tab.is-active');
    if (!active) return;
    const idx = order.indexOf(active.dataset.tab);
    const next = e.key === 'ArrowRight' ? order[(idx + 1) % order.length] : order[(idx - 1 + order.length) % order.length];
    /* navigation handled by link clicks */
    document.querySelector('.nav-tab[data-tab="' + next + '"]').focus();
  });

  // ============================================
  // YOUTUBE IFRAME API — OST Xian Ni
  // ============================================
  // L'API YouTube appelle onYouTubeIframeAPIReady() quand prête.
  // On garde un player caché (1x1px) qui streame l'OST.
  const YT_VIDEO_ID = 'bXJKwYzz5mw';
  const LS_KEY = 'ri_audio_v1';
  const Audio = (function () {
    let player = null;
    let ready = false;
    let playing = false;
    let volume = 40; // 0..100
    let loadTimer = null;
    let loadAttempts = 0;
    const subs = [];  // subscribers au changement d'état (pour l'UI)

    function emit(event, data) { subs.forEach(fn => { try { fn(event, data); } catch (e) {} }); }

    function save() {
      try { localStorage.setItem(LS_KEY, JSON.stringify({ playing, volume })); } catch (e) {}
    }
    function load() {
      try {
        const s = JSON.parse(localStorage.getItem(LS_KEY) || '{}');
        if (typeof s.volume === 'number') volume = Math.max(0, Math.min(100, s.volume));
      } catch (e) {}
    }
    load();

    // API YT appelle ce nom globalement quand le SDK est prêt
    window.onYouTubeIframeAPIReady = function () {
      try {
        player = new YT.Player('yt-player-host', {
          height: '1', width: '1',
          videoId: YT_VIDEO_ID,
          playerVars: {
            autoplay: 0,
            controls: 0,
            disablekb: 1,
            fs: 0,
            modestbranding: 1,
            playsinline: 1,
            rel: 0,
            origin: window.location.origin
          },
          events: {
            onReady: function (e) {
              ready = true;
              // applique le volume persisté
              try { e.target.setVolume(volume); } catch (err) {}
              // Si l'utilisateur avait laissé "playing" avant refresh, on ne relance PAS
              // (les navigateurs bloquent l'autoplay sans gesture)
              emit('ready');
            },
            onStateChange: function (e) {
              // YT.PlayerState.ENDED = 0, PLAYING = 1, PAUSED = 2, BUFFERING = 3
              if (e.data === 1) { playing = true; emit('play'); }
              else if (e.data === 2 || e.data === 0) { playing = false; emit('pause'); }
            },
            onError: function (e) {
              console.warn('YouTube player error', e);
              emit('error', e);
            }
          }
        });
      } catch (err) {
        console.warn('YT.Player init failed', err);
        emit('error', err);
      }
    };

    // Timeout: si l'API ne répond pas en 8s, on notifie l'UI
    function startLoadWatchdog() {
      loadTimer = setTimeout(function () {
        if (!ready) {
          loadAttempts++;
          if (loadAttempts < 2) {
            // retry une fois (parfois le SDK est lent au 1er load)
            const s = document.createElement('script');
            s.src = 'https://www.youtube.com/iframe_api';
            s.onload = function () { startLoadWatchdog(); };
            document.head.appendChild(s);
          } else {
            emit('error', 'timeout');
          }
        }
      }, 8000);
    }
    startLoadWatchdog();

    function setPlaying(p) {
      if (!ready || !player) { emit('error', 'not-ready'); return; }
      try {
        if (p) player.playVideo();
        else player.pauseVideo();
        // l'event onStateChange va flipper `playing`
        playing = p;
        save();
      } catch (err) { emit('error', err); }
    }
    function setVolume(v) {
      volume = Math.max(0, Math.min(100, v));
      if (ready && player) { try { player.setVolume(volume); } catch (e) {} }
      save();
    }
    function isPlaying() { return playing; }
    function isReady() { return ready; }
    function subscribe(fn) { subs.push(fn); }

    return { setPlaying, setVolume, isPlaying, isReady, subscribe };
  })();

  // Wire UI
  const dock = document.getElementById('audio-dock');
  const btn  = document.getElementById('audio-btn');
  const iconPlay  = document.getElementById('icon-play');
  const iconPause = document.getElementById('icon-pause');
  const vol  = document.getElementById('audio-vol');

  // Position du slider selon état persisté
  vol.value = String(Math.round(Audio.isReady() ? (player?._lastVol || 40) : 40));

  Audio.subscribe(function (event, data) {
    if (event === 'ready') {
      dock.classList.remove('is-loading');
      btn.setAttribute('aria-label', 'Lire l\'OST Xian Ni');
      const v = parseInt(vol.value, 10);
      if (!isNaN(v)) Audio.setVolume(v);
      // si l'overlay a déjà été dismissé (réutilisation), lance la lecture
      if (window.__ri_gesture_done && !Audio.isPlaying()) {
        Audio.setPlaying(true);
        dock.classList.add('is-playing');
      }
    }
    if (event === 'play') {
      btn.setAttribute('aria-pressed', 'true');
      btn.setAttribute('aria-label', 'Mettre en pause l\'OST Xian Ni');
      iconPlay.style.display  = 'none';
      iconPause.style.display = '';
      dock.classList.add('is-playing');
      dock.classList.remove('is-loading');
    }
    if (event === 'pause') {
      btn.setAttribute('aria-pressed', 'false');
      btn.setAttribute('aria-label', 'Lire l\'OST Xian Ni');
      iconPlay.style.display  = '';
      iconPause.style.display = 'none';
      dock.classList.remove('is-playing');
    }
    if (event === 'error') {
      console.warn('Audio error', data);
      dock.classList.remove('is-loading');
      dock.classList.add('is-error');
      btn.setAttribute('aria-label', 'Musique indisponible — réessaie plus tard');
      iconPlay.style.display  = '';
      iconPause.style.display = 'none';
    }
  });

  // État initial UI: bouton "on" par défaut
  dock.classList.add('is-loading');
  btn.setAttribute('aria-label', 'L\'OST Xian Ni démarre automatiquement');
  btn.setAttribute('aria-pressed', 'true');
  iconPlay.style.display  = 'none';
  iconPause.style.display = '';
  dock.classList.add('is-playing');

  btn.addEventListener('click', function () {
    if (dock.classList.contains('is-error')) return;
    if (!Audio.isReady()) {
      dock.classList.add('is-loading');
      return;
    }
    Audio.setPlaying(!Audio.isPlaying());
  });

    }  // end if (wikiGrid) — WIKI

// === GESTURE OVERLAY (pour satisfaire la politique autoplay des browsers) ===
  const gestureHint = document.getElementById('gesture-hint');
  function dismissGesture() {
    if (!gestureHint || gestureHint.classList.contains('is-hidden')) return;
    gestureHint.classList.add('is-hidden');
    // Force-hide via inline style as a safety net
    gestureHint.style.pointerEvents = 'none';
    gestureHint.style.opacity = '0';
    window.__ri_gesture_done = true;
    // Update dock visual state immediately
    btn.setAttribute('aria-pressed', 'true');
    btn.setAttribute('aria-label', 'Mettre en pause l\'OST Xian Ni');
    iconPlay.style.display  = 'none';
    iconPause.style.display = '';
    dock.classList.add('is-playing');
    dock.classList.remove('is-loading');
    // Try to start audio — works if API is ready, otherwise the subscribe handler
    // will catch the 'ready' event and call setPlaying(true) automatically
    try {
      Audio.setPlaying(true);
    } catch (e) {
      console.warn('setPlaying failed (will retry on ready):', e);
    }
    // retire du DOM après le fade-out
    setTimeout(() => { if (gestureHint && gestureHint.parentNode) gestureHint.parentNode.removeChild(gestureHint); }, 900);
  }
  gestureHint.addEventListener('click', dismissGesture, { once: false });
  // Backup: bind to document so any click on the page (during the overlay) works
  function _dismissOnAnyClick(e) {
    if (gestureHint && !gestureHint.classList.contains('is-hidden')) {
      dismissGesture();
    }
  }
  document.addEventListener('click', _dismissOnAnyClick, true);
  // ESC aussi pour skipper
  document.addEventListener('keydown', function onceK(e) {
    if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      dismissGesture();
      document.removeEventListener('keydown', onceK);
    }
  });
  // Fallback: si le browser autorise l'autoplay (rare), dismiss automatique après 1.2s
  setTimeout(() => {
    if (Audio.isReady() && Audio.isPlaying()) {
      dismissGesture();
    }
  }, 1200);

  vol.addEventListener('input', function () {
    Audio.setVolume(parseInt(vol.value, 10));
  });

  // === THEME TOGGLE (dark/light) ===
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    const saved = localStorage.getItem('ri_theme');
    if (saved === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
      themeBtn.textContent = '☾';
    } else {
      themeBtn.textContent = '☀';
    }
    themeBtn.addEventListener('click', function() {
      const current = document.documentElement.getAttribute('data-theme');
      if (current === 'light') {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('ri_theme', 'dark');
        themeBtn.textContent = '☀';
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('ri_theme', 'light');
        themeBtn.textContent = '☾';
      }
    });
  }
})();
