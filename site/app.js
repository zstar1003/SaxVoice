'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const state = {catalog: null, song: 'juebieshu', instrument: 'soprano', page: 1, revision: 0};
  const instruments = [...document.querySelectorAll('[data-instrument]')];
  const mobile = matchMedia('(max-width:760px)');
  const reduceMotion = matchMedia('(prefers-reduced-motion:reduce)');
  const normalize = value => value.toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f\s·’'-]/g, '');
  const piece = () => state.catalog.pieces.find(p => p.id === state.song);
  const edition = () => piece().variants[state.instrument];
  const text = (id, value) => { $(id).textContent = value; };
  const imageURL = path => `./${path}?v=${state.catalog.version}`;
  let toastTimer;
  const expanded = new Map();
  const categoryOf = p => state.catalog.categories.find(c => c.id === p.category);
  const groupOf = p => categoryOf(p).groups.find(g => g.id === p.subcategory);
  const branchKey = (kind, id) => `${kind}:${id}`;
  function openCurrentBranch() {
    const p = piece();
    expanded.set(branchKey('category', p.category), true);
    expanded.set(branchKey('group', p.subcategory), true);
  }

  function setDrawer(open, restoreFocus = true) {
    const shown = mobile.matches && open;
    document.body.classList.toggle('catalog-open', shown);
    $('open-library').setAttribute('aria-expanded', String(shown));
    $('drawer-backdrop').hidden = !shown;
    $('library').inert = document.body.classList.contains('reader-fullscreen') || (!shown && (mobile.matches || document.body.classList.contains('focus-mode')));
    $('score-main').inert = shown;
    if (shown) {
      $('library').setAttribute('role', 'dialog');
      $('library').setAttribute('aria-modal', 'true');
      requestAnimationFrame(() => {
        if (document.body.classList.contains('catalog-open')) $('song-search').focus();
      });
    } else {
      $('library').removeAttribute('role');
      $('library').removeAttribute('aria-modal');
      if (mobile.matches && restoreFocus) $('open-library').focus();
    }
  }
  setDrawer(false, false);
  mobile.addEventListener('change', () => setDrawer(false, false));
  $('open-library').addEventListener('click', () => setDrawer(true));
  $('close-library').addEventListener('click', () => setDrawer(false));
  $('drawer-backdrop').addEventListener('click', () => setDrawer(false));

  function updateURL(push = true) {
    const url = new URL(location.href);
    url.searchParams.delete('v');
    url.searchParams.set('song', state.song);
    url.searchParams.set('instrument', state.instrument);
    if (state.page > 1) url.searchParams.set('page', state.page);
    else url.searchParams.delete('page');
    if (!push || url.href !== location.href) history[push ? 'pushState' : 'replaceState'](null, '', url);
  }

  function renderList() {
    if (!state.catalog) return;
    const query = normalize($('song-search').value), category = $('genre-filter').value;
    const results = state.catalog.pieces.filter(p => (!category || p.category === category) && normalize(`${p.title} ${p.english} ${p.composer} ${p.aliases} ${categoryOf(p).label} ${groupOf(p).label}`).includes(query));
    const expandedByFilter = Boolean(query || category);
    $('song-list').replaceChildren();
    function branch(kind, id, label, count) {
      const details = document.createElement('details');
      details.className = `catalog-${kind}`; details.dataset.branch = id;
      details.open = expandedByFilter || Boolean(expanded.get(branchKey(kind, id)));
      const summary = document.createElement('summary');
      const name = document.createElement('span'); name.textContent = label;
      const total = document.createElement('small'); total.textContent = count;
      total.setAttribute('aria-label', `${count} 首`);
      summary.append(name, total); details.append(summary);
      details.addEventListener('toggle', () => {
        if (!expandedByFilter) expanded.set(branchKey(kind, id), details.open);
      });
      return details;
    }
    for (const category of state.catalog.categories) {
      const categoryPieces = results.filter(p => p.category === category.id);
      if (!categoryPieces.length) continue;
      const parent = branch('category', category.id, category.label, categoryPieces.length);
      const groups = document.createElement('div'); groups.className = 'category-groups';
      for (const group of category.groups) {
        const groupPieces = categoryPieces.filter(p => p.subcategory === group.id);
        if (!groupPieces.length) continue;
        const child = branch('group', group.id, group.label, groupPieces.length);
        const songs = document.createElement('div'); songs.className = 'group-songs';
        for (const p of groupPieces) {
          const button = document.createElement('button');
          button.type = 'button'; button.className = 'song-row';
          button.setAttribute('aria-current', String(p.id === state.song));
          button.setAttribute('aria-label', `${p.title}，${group.label}`);
          const title = document.createElement('strong'); title.textContent = p.title;
          button.append(title);
          button.addEventListener('click', () => {
            if (state.song !== p.id) {
              state.song = p.id; state.page = 1;
              document.querySelector('.edition-details').open = false;
              openCurrentBranch(); renderScore(); renderList(); updateURL();
            }
            setDrawer(false);
            window.scrollTo({top: 0, behavior: reduceMotion.matches ? 'instant' : 'smooth'});
          });
          songs.append(button);
        }
        child.append(songs); groups.append(child);
      }
      parent.append(groups); $('song-list').append(parent);
    }
    text('result-count', `${results.length} 首`);
    $('empty-results').hidden = results.length !== 0;
  }

  function showPage(number, push = false) {
    const part = edition();
    state.page = Math.max(1, Math.min(Number(number) || 1, part.pages.length));
    const page = part.pages[state.page - 1];
    $('load-error').hidden = true;
    $('score-image').src = imageURL(page.image);
    $('score-image').alt = `${piece().title}，${part.label}，第 ${state.page} 页，第 ${page.firstMeasure} 至 ${page.lastMeasure} 小节`;
    $('page-select').value = String(state.page);
    $('previous-page').disabled = state.page === 1;
    $('next-page').disabled = state.page === part.pages.length;
    text('measure-range', `${page.firstMeasure}–${page.lastMeasure} 小节`);
    text('viewer-status', $('score-image').alt);
    $('score-scroll').scrollTo(0, 0);
    if (push) updateURL();
  }

  function renderScore() {
    const p = piece(), part = edition(), revision = ++state.revision;
    document.title = `${p.title} · ${part.label} | SaxVoice`;
    text('piece-title', p.title);
    text('piece-category', `${categoryOf(p).label} / ${groupOf(p).label}`);
    text('piece-subtitle', p.creditTitle ? `${p.english} · ${p.composer}` : p.composer);
    text('written-key', part.writtenKey);
    text('score-summary', `${part.pages.length} 页`);
    text('arrangement-note', p.description);
    text('instrument-note', `${part.label} · 记谱 ${part.writtenKey} · 实音 ${p.concertKey} · ${p.meterText}。${part.soundingOctaveOffset === 0 ? '实音按旋律基准音区。' : '实音比高音版低一个八度。'}`);
    text('verification-note', p.verificationNote || '单声部旋律版，包含各乐器的移调与八度选择。');
    text('rights-note', p.rights);
    $('license-link').hidden = !p.license;
    if (p.license) { $('license-link').href = p.license.url; text('license-link', `${p.license.label} ↗`); }
    for (const id of ['download-pdf', 'open-pdf', 'error-pdf']) $(id).href = `./${part.pdf}`;
    $('download-pdf').download = `${p.title}-${part.label}-A4.pdf`;
    $('download-xml').href = `./${part.musicxml}`;
    $('download-xml').download = `${p.title}-${state.instrument}.musicxml`;
    $('source-link').hidden = !p.source && !p.comparisonRecording;
    if (p.source || p.comparisonRecording) {
      $('source-link').href = p.source?.url || p.comparisonRecording;
      text('source-link', p.source ? '参考版本 ↗' : '原发行录音 ↗');
    }
    $('reference-pdf').hidden = !part.referencePdf;
    if (part.referencePdf) $('reference-pdf').href = `./${part.referencePdf}`;
    instruments.forEach(button => {
      button.disabled = false;
      button.setAttribute('aria-pressed', String(button.dataset.instrument === state.instrument));
    });
    $('page-select').replaceChildren(...part.pages.map((_, index) => new Option(`${index + 1} / ${part.pages.length}`, index + 1)));
    $('page-select').disabled = part.pages.length === 1;
    $('fullscreen-score').disabled = false;
    text('fullscreen-title', `${p.title} · ${state.catalog.instruments[state.instrument].label}`);
    $('share-score').disabled = false;
    $('share-status').hidden = true;
    showPage(state.page);
    $('print-score').disabled = true;
    $('print-score').setAttribute('aria-label', `打印${p.title} ${part.label}，共 ${part.pages.length} 页`);
    $('print-score').title = `打印 ${part.pages.length} 页`;
    const images = part.pages.map((page, index) => {
      const img = new Image();
      img.alt = `${p.title} ${part.label} 打印第 ${index + 1} 页`;
      img.src = imageURL(page.image);
      return img;
    });
    $('print-pages').replaceChildren(...images);
    Promise.all(images.map(img => img.decode())).then(() => {
      if (state.revision === revision) $('print-score').disabled = false;
    }).catch(() => {
      if (state.revision === revision) $('print-score').title = '请下载 PDF 打印';
    });
  }

  function readURL() {
    const params = new URLSearchParams(location.search);
    state.song = state.catalog.pieces.some(p => p.id === params.get('song')) ? params.get('song') : 'juebieshu';
    state.instrument = ['soprano', 'alto'].includes(params.get('instrument')) ? params.get('instrument') : 'soprano';
    state.page = Number(params.get('page')) || 1;
    openCurrentBranch(); renderScore(); renderList(); updateURL(false);
  }

  $('song-search').addEventListener('input', renderList);
  $('genre-filter').addEventListener('change', renderList);
  $('clear-search').addEventListener('click', () => { $('song-search').value = ''; $('genre-filter').value = ''; renderList(); $('song-search').focus(); });
  instruments.forEach(button => button.addEventListener('click', () => {
    if (state.instrument === button.dataset.instrument) return;
    state.instrument = button.dataset.instrument; renderScore(); updateURL();
  }));
  $('previous-page').addEventListener('click', () => showPage(state.page - 1, true));
  $('next-page').addEventListener('click', () => showPage(state.page + 1, true));
  $('page-select').addEventListener('change', event => showPage(event.target.value, true));
  const reader = $('score-viewer');
  let fullscreenRevision = 0;
  const isFullscreen = () => reader.classList.contains('fullscreen-reader');
  function fullscreenFocusables() {
    return [...reader.querySelectorAll('button:not(:disabled), select:not(:disabled), a[href], [tabindex="0"]')].filter(e => e.checkVisibility());
  }
  function setFullscreen(active) {
    reader.classList.toggle('fullscreen-reader', active);
    document.body.classList.toggle('reader-fullscreen', active);
    (active ? reader : document.body).append($('share-status'));
    $('fullscreen-score').setAttribute('aria-pressed', String(active));
    text('fullscreen-score', active ? '退出' : '全屏');
    $('fullscreen-score').setAttribute('aria-label', active ? '退出全屏' : '全屏显示曲谱');
    $('library').inert = active || mobile.matches || document.body.classList.contains('focus-mode');
    document.querySelector('.site-header').inert = active;
    for (const el of document.querySelectorAll('.piece-heading, .edition-row, .edition-details')) el.inert = active;
    $('score-scroll').scrollTo(0, 0);
    if (!active) {
      reader.classList.remove('fit-page');
      $('fit-page').setAttribute('aria-pressed', 'false');
      text('fit-page', '整页');
    }
    $('fullscreen-score').focus({preventScroll: true});
  }
  async function exitFullscreen() {
    ++fullscreenRevision;
    setFullscreen(false);
    if (document.fullscreenElement === reader) {
      try { await document.exitFullscreen(); } catch { /* The browser can exit before this request. */ }
    }
  }
  $('fullscreen-score').addEventListener('click', async () => {
    if (isFullscreen()) { await exitFullscreen(); return; }
    const revision = ++fullscreenRevision;
    setFullscreen(true);
    if (reader.requestFullscreen) {
      try {
        await reader.requestFullscreen();
        // A pending native request must not re-enter after the user exits.
        if (revision !== fullscreenRevision && document.fullscreenElement === reader) await document.exitFullscreen();
      } catch { /* Keep the window-filling reader when native fullscreen is unavailable. */ }
    }
  });
  document.addEventListener('fullscreenchange', () => {
    if (document.fullscreenElement === reader) setFullscreen(true);
    else if (isFullscreen()) { ++fullscreenRevision; setFullscreen(false); }
  });
  $('fit-page').addEventListener('click', () => {
    const fit = reader.classList.toggle('fit-page');
    $('fit-page').setAttribute('aria-pressed', String(fit));
    text('fit-page', fit ? '适宽' : '整页');
    $('score-scroll').scrollTo(0, 0);
  });
  $('focus-reader').addEventListener('click', () => {
    const focused = document.body.classList.toggle('focus-mode');
    $('focus-reader').setAttribute('aria-pressed', String(focused));
    text('focus-reader', focused ? '退出专注' : '专注');
    $('library').inert = focused || mobile.matches;
  });
  $('score-image').addEventListener('error', () => { $('load-error').hidden = false; });
  $('print-score').addEventListener('click', () => { if (!$('print-score').disabled) window.print(); });
  $('share-score').addEventListener('click', async () => {
    let message;
    try { await navigator.clipboard.writeText(location.href); message = '链接已复制'; }
    catch { message = '请复制浏览器地址栏中的链接'; }
    text('share-status', message); $('share-status').hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('share-status').hidden = true; }, 2500);
  });
  $('retry-catalog').addEventListener('click', () => location.reload());
  document.addEventListener('keydown', event => {
    if (document.body.classList.contains('catalog-open')) {
      if (event.key === 'Escape') { event.preventDefault(); setDrawer(false); return; }
      if (event.key === 'Tab') {
        const focusable = [...$('library').querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), summary')].filter(e => e.checkVisibility());
        const first = focusable[0], last = focusable.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
      return;
    }
    if (isFullscreen()) {
      if (event.key === 'Escape') { event.preventDefault(); exitFullscreen(); return; }
      if (event.key === 'Tab') {
        const controls = fullscreenFocusables(), first = controls[0], last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
      if (event.key === '/') { event.preventDefault(); return; }
    }
    if (event.target.tagName === 'SUMMARY') return;
    if (!state.catalog || event.altKey || event.ctrlKey || event.metaKey || /^(INPUT|SELECT|TEXTAREA)$/.test(event.target.tagName) || event.target.isContentEditable) return;
    if (event.key === '/') { event.preventDefault(); if (mobile.matches) setDrawer(true); else if (!document.body.classList.contains('focus-mode')) $('song-search').focus(); }
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); showPage(state.page + (event.key === 'ArrowLeft' ? -1 : 1), true); }
    if (event.key === 'Escape' && document.body.classList.contains('focus-mode')) $('focus-reader').click();
  });
  window.addEventListener('popstate', () => { if (state.catalog) readURL(); });
  fetch('./catalog.json?v=fullscreen-v7').then(response => {
    if (!response.ok) throw new Error('Catalog unavailable');
    return response.json();
  }).then(catalog => {
    if (!catalog.pieces?.length) throw new Error('Empty catalog');
    state.catalog = catalog;
    text('piece-count', `${catalog.pieces.length} 首`);
    for (const category of catalog.categories) $('genre-filter').add(new Option(category.label, category.id));
    $('song-search').disabled = false; $('genre-filter').disabled = false;
    readURL();
  }).catch(() => { $('catalog-error').hidden = false; text('song-list', '曲库加载失败'); });
})();
