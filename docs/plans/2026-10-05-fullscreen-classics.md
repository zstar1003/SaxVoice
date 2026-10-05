# Fullscreen reader and classic scores

Request: replace zoom with one-click fullscreen, add Merry Christmas, Mr. Lawrence, Going Home and classic saxophone repertoire as real in-site scores, and rewrite README for the whole library. The user confirmed negotiated authorization and asked to proceed directly.

Implemented:

- Native Fullscreen API with a window-filling fallback; default fit-width score, optional whole-page fit, in-place paging, share feedback, printing and exit. Escape exits, browser fullscreen changes synchronize state, keyboard focus stays in the reader, and background controls remain inert across mobile rotation.
- Three new pieces in soprano B-flat and alto E-flat. Each has an A4 vector PDF, MusicXML and PDF-rendered preview. Theme/solo selection and register adjustments are recorded in the catalog, PDF and source notes.
- Exact 3:2 triplets using rational durations and integer MusicXML divisions; printed tuplet groups and duration validation. PDF key names use Chinese flat/sharp words because the CJK font lacks those glyphs; short final systems avoid stretching a single bar across the page.
- New “流行与当代 / 萨克斯名曲” subcategory, updated search entries and generic README. Total: 49 pieces, 98 editions, 102 A4 pages, 5 categories, 11 subcategories.

Verification:

- 39 desktop browser checks: native entry/exit, browser-triggered exit, fallback rejection, Escape, fit modes, paging, keyboard wrap, share toast, six real new downloads, search and category integration; no JavaScript errors.
- 32 mobile/search checks at 390×844, 844×390 and 320×568: window-filling fallback with no native API, toolbar bounds, fit-page, rotation across the drawer breakpoint, restored focusability, long titles and mobile selection.
- Printing while fullscreen produced all three A4 pages of the selected score, with no clipped page or extra UI.
- Library validation passed for all 49 pieces / 98 editions / 102 pages: rhythms, ties, triplet ratios and boundaries, printed accidentals, instrument transposition, range, PDF dimensions and vector content.
- Viewed all six new previews and revised key labels/final-system spacing. Existing 46 pieces’ score files remain byte-identical.
- JavaScript syntax, Python compilation and git whitespace checks passed.

Research PDFs, browser test scripts, screenshots and logs live in ignored output directories. Source/version records are in docs/library-sources.md and docs/music-review.md.
