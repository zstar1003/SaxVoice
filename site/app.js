'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const state = { catalog: null, song: 'juebieshu', instrument: 'soprano', page: 1, revision: 0 };
  const buttons = [...document.querySelectorAll('[data-instrument]')];
  const drawer = $('library-drawer');
  const mobileLayout = matchMedia('(max-width:760px)');
  drawer.open = !mobileLayout.matches;
  mobileLayout.addEventListener('change', event => { drawer.open = !event.matches; });
  const normalize = text => text.toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f\s·’'-]/g, '');
  const currentPiece = () => state.catalog.pieces.find(p => p.id === state.song);
  const currentEdition = () => currentPiece().variants[state.instrument];
  const imageURL = path => `./${path}?v=${state.catalog.version}`;
  const text = (id, value) => { $(id).textContent = value; };

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
    const query = normalize($('song-search').value);
    const genre = $('genre-filter').value;
    const results = state.catalog.pieces.filter(p => (!genre || p.genre === genre) && normalize(`${p.title} ${p.english} ${p.composer} ${p.aliases}`).includes(query));
    $('song-list').replaceChildren();
    for (const p of results) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'song-row';
      button.setAttribute('aria-current', String(p.id === state.song));
      button.setAttribute('aria-label', `${p.title}，${p.genre}，${p.difficulty}`);
      const label = document.createElement('span');
      const title = document.createElement('strong'); title.textContent = p.title;
      const detail = document.createElement('small'); detail.textContent = `${p.english} · ${p.difficulty}`;
      label.append(title, detail);
      const index = document.createElement('span'); index.className = 'row-index';
      index.textContent = String(state.catalog.pieces.indexOf(p) + 1).padStart(2, '0');
      button.append(label, index);
      button.addEventListener('click', () => {
        state.song = p.id; state.page = 1; renderScore(); updateURL(); renderList();
        if (matchMedia('(max-width:760px)').matches) {
          drawer.open = false; document.querySelector('.score-area').scrollIntoView({ behavior: 'smooth' });
        }
      });
      $('song-list').append(button);
    }
    text('result-count', `${results.length} / ${state.catalog.pieces.length} 首`);
    $('empty-results').hidden = results.length !== 0;
  }

  function showPage(page, push = false) {
    const edition = currentEdition();
    state.page = Math.max(1, Math.min(Number(page) || 1, edition.pages.length));
    const p = edition.pages[state.page - 1];
    $('load-error').hidden = true;
    $('score-image').src = imageURL(p.image);
    $('score-image').alt = `${currentPiece().title}，${edition.label}，第 ${state.page} 页，第 ${p.firstMeasure} 至 ${p.lastMeasure} 小节`;
    $('page-select').value = String(state.page);
    $('previous-page').disabled = state.page === 1;
    $('next-page').disabled = state.page === edition.pages.length;
    text('measure-range', `第 ${p.firstMeasure}–${p.lastMeasure} 小节`);
    text('viewer-status', $('score-image').alt);
    $('score-scroll').scrollTo(0, 0);
    if (push) updateURL();
  }

  function renderScore() {
    const p = currentPiece(), edition = currentEdition();
    const revision = ++state.revision;
    document.title = `${p.title} · ${edition.label} | SaxVoice 曲谱库`;
    text('piece-title', p.title);
    text('piece-category', `${p.genre} / ${String(state.catalog.pieces.indexOf(p)+1).padStart(3,'0')}`);
    text('piece-subtitle', `${p.composer} · ${p.difficulty} · ${p.measureCount} 小节`);
    text('written-key', `记谱 ${edition.writtenKey}`);
    text('score-summary', `${edition.pages.length} 页 · ${p.meterText}`);
    text('arrangement-note', p.description);
    const octave = edition.soundingOctaveOffset === 0 ? '实音按旋律基准音区演奏。' : '实音比高音版低一个八度，与高音版同调，可配同一调伴奏。';
    text('instrument-note', `${edition.label}，${octave}${state.instrument === 'tenor' ? '这是降 B 次中音版本。' : ''}`);
    text('rights-note', p.rights);
    text('verification-note', p.verificationNote || '采用单声部旋律，乐器版本包含移调与八度选择；未包含原曲的钢琴伴奏声部。');
    $('download-pdf').href = `./${edition.pdf}`;
    $('download-pdf').download = `${p.title}-${edition.label}-A4.pdf`;
    $('open-pdf').href = `./${edition.pdf}`;
    $('download-xml').href = `./${edition.musicxml}`;
    $('download-xml').download = `${p.title}-${state.instrument}.musicxml`;
    $('source-link').hidden = !p.source && !p.comparisonRecording;
    if (p.source || p.comparisonRecording) {
      $('source-link').href = p.source?.url || p.comparisonRecording;
      text('source-link', p.source?.label || '打开邓垚原发行版 ↗');
    }
    $('reference-pdf').hidden = !edition.referencePdf;
    if (edition.referencePdf) $('reference-pdf').href = `./${edition.referencePdf}`;
    buttons.forEach(button => {
      button.disabled = false;
      button.setAttribute('aria-pressed', String(button.dataset.instrument === state.instrument));
    });
    $('page-select').replaceChildren(...edition.pages.map((_, index) => new Option(`第 ${index+1} 页 / 共 ${edition.pages.length} 页`, index+1)));
    $('page-select').disabled = false;
    $('zoom-score').disabled = false;
    $('share-score').disabled = false;
    text('share-status', '');
    showPage(state.page);
    // Decode every page of the selected edition before enabling its print action.
    $('print-score').disabled = true;
    text('print-score', `打印 ${edition.pages.length} 页`);
    const images = edition.pages.map((page, index) => {
      const img = new Image(); img.alt = `${p.title} ${edition.label} 打印第 ${index+1} 页`;
      img.src = imageURL(page.image); return img;
    });
    $('print-pages').replaceChildren(...images);
    Promise.all(images.map(img => img.decode())).then(() => {
      if (state.revision === revision) $('print-score').disabled = false;
    }).catch(() => {
      if (state.revision === revision) text('print-score', '请下载 PDF 打印');
    });
  }

  function readURL() {
    const params = new URLSearchParams(location.search);
    state.song = state.catalog.pieces.some(p => p.id === params.get('song')) ? params.get('song') : 'juebieshu';
    state.instrument = ['soprano','alto','tenor'].includes(params.get('instrument')) ? params.get('instrument') : 'soprano';
    state.page = Number(params.get('page')) || 1;
    renderScore(); renderList(); updateURL(false);
  }

  $('song-search').addEventListener('input', renderList);
  $('genre-filter').addEventListener('change', renderList);
  $('clear-search').addEventListener('click', () => { $('song-search').value = ''; $('genre-filter').value = ''; renderList(); $('song-search').focus(); });
  buttons.forEach(button => button.addEventListener('click', () => {
    if (state.instrument === button.dataset.instrument) return;
    state.instrument = button.dataset.instrument; renderScore(); updateURL();
  }));
  $('previous-page').addEventListener('click', () => showPage(state.page-1, true));
  $('next-page').addEventListener('click', () => showPage(state.page+1, true));
  $('page-select').addEventListener('change', event => showPage(event.target.value, true));
  $('zoom-score').addEventListener('click', () => {
    const zoomed = $('score-scroll').classList.toggle('zoomed');
    $('zoom-score').setAttribute('aria-pressed', String(zoomed));
    text('zoom-score', zoomed ? '适合页面' : '放大阅读');
  });
  $('score-image').addEventListener('error', () => { $('load-error').hidden = false; });
  $('print-score').addEventListener('click', () => { if (!$('print-score').disabled) window.print(); });
  $('share-score').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); text('share-status','已复制，可以直接打开当前曲目与乐器版本。'); }
    catch { text('share-status','可复制浏览器地址栏中的当前链接。'); }
  });
  document.addEventListener('keydown', event => {
    if (!state.catalog || event.altKey || event.ctrlKey || event.metaKey || /^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(event.target.tagName) || event.target.isContentEditable) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); showPage(state.page + (event.key === 'ArrowLeft' ? -1 : 1), true); }
  });
  window.addEventListener('popstate', () => { if (state.catalog) readURL(); });
  fetch('./catalog.json?v=library-v3').then(response => { if (!response.ok) throw new Error('Catalog unavailable'); return response.json(); }).then(catalog => {
    if (!catalog.pieces?.length) throw new Error('Empty catalog');
    state.catalog = catalog;
    text('piece-count', String(catalog.pieces.length).padStart(2,'0'));
    text('edition-count', catalog.pieces.reduce((sum,p) => sum+Object.keys(p.variants).length, 0));
    for (const genre of new Set(catalog.pieces.map(p => p.genre))) $('genre-filter').add(new Option(genre,genre));
    $('song-search').disabled = false; $('genre-filter').disabled = false; readURL();
  }).catch(() => {
    $('catalog-error').hidden = false; text('song-list','书架加载失败，请重新加载。');
  });
})();
