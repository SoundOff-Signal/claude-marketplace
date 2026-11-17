# Brand reference and maintenance

Read this when you need an exact token, or when changing the skill itself.
Authoritative values live in `scripts/brand.py`; every builder imports them.

## Color tokens

| Token | Hex | Use |
|---|---|---|
| Primary red (PMS 187) | `#A71B28` | headlines, rules, table headers, footer marking, accents |
| Dark red | `#7E1420` | cover gradient base, H3, IMPORTANT callouts |
| Ink | `#1A1A1A` | body text, classification banner |
| Gray | `#6E6E6E` | subtitles, captions, secondary metadata |
| Light gray | `#9B9B9B` | light rules, quote bar |
| Hairline | `#D8D8D8` | table borders, rules |
| Band | `#FAF6F6` | table zebra banding |
| Code background | `#F5F5F5` | code blocks, inline code |
| Metric blue | `#1A5383` | KPI values, NOTE callouts |
| Amber / Yellow / Green / Neutral | `#E06C2E` / `#E9C46A` / `#7DA86B` / `#E6E6E6` | status fills in trackers |
| Callout tints | blue `#EEF3F8`, green `#F0F6ED`, red `#F9EEEF`, amber `#FCF1EA` | callout backgrounds |

PMS 187 is the canonical brand red; `#A71B28` is its working hex value.

## Typography and logos

- Headlines: Oswald, bundled weights 300 to 700 (`assets/fonts/`, OFL).
- Body: Arial; Liberation Sans is the metric-compatible substitute on Linux.
- Code: Consolas in Office, Liberation Mono in PDF.
- Logos (`assets/logos/`, about 2297 px wide, transparent PNG):

| File | Background | Used for |
|---|---|---|
| `soundoff-logo-full-color.png` | light | running headers, default |
| `soundoff-logo-reverse-white.png` | red or dark | cover band |
| `soundoff-logo-inverse-red-white.png` | dark | dark backgrounds where red should read |
| `soundoff-logo-black.png` | light | single-color or print-constrained output |

Use red as an accent and as full backgrounds on cover, divider, and banner
elements, not as thin decorative stripes.

## Layout defaults

- US Letter. Word margins 0.75 in; PDF margins 26/18/22/18 mm (T/R/B/L).
- Report cover: red gradient band with the white logo and doc-type label,
  Oswald title, gray subtitle, red rule, status badge, metadata table, black
  classification banner at the bottom.
- Running header: logo left; title, doc_id, and status right. Footer:
  classification left, doc_id (or title) center, page X of Y right.
- Mermaid diagrams use `brand.MERMAID_CONFIG`: white nodes with red borders,
  gray connectors, Arial labels.

## Changing the skill

| To change | Edit | Notes |
|---|---|---|
| Colors, fonts, marking text, status labels, logos, callout colors, Mermaid theme | `scripts/brand.py` | all four builders pick it up |
| Cover and metadata rows | `brand.COVER_FIELDS` | one list drives Word, PDF, and the Excel metadata line |
| A department, its code, or its profile | `references/departments/departments.yaml` (+ a profile from `_template.md`) | the ID check reads the YAML |
| Markdown handling | `scripts/md_blocks.py` | then run the regression below |
| Images and diagrams | `scripts/media.py` | |
| Word styles | `_define_styles()` in `build_docx.py` | change styles, not inline formatting, or the navigation pane and TOC stop matching |
| PDF layout | `build_css()` and the `render_*` functions in `build_pdf.py` | |
| Deck design | replace `assets/templates/soundoff-deck-template.pptx` | no code change if layout order holds: 0 Title, 1 Divider, 3 Content - Bullets, 7 Ending (placeholders idx 0 title, 10 info, 12 lead-in, 13 body) |
| Excel status words and colors | `STATUS_COLORS` / `STATUS_COLS` in `build_xlsx.py` | |

Keep the skill free of personal or single-department defaults: anything that
names a person, a department, or a department code belongs in the requester's
front matter or in that department's profile, never in `brand.py` or SKILL.md.

## Regression

After any change to `md_blocks.py`, `media.py`, or a builder, rebuild the
fixtures and run QA:

```bash
mkdir -p /tmp/qa && rm -f /tmp/qa/*
for f in docx pdf pptx; do
  python scripts/build_$f.py --content assets/tests/fixture.md --output /tmp/qa/ --strict
done
python scripts/build_xlsx.py --content assets/examples/register.md --output /tmp/qa/ --strict
python scripts/qa_check.py --content assets/tests/fixture.md /tmp/qa/*.docx /tmp/qa/*.pdf /tmp/qa/*.pptx
python scripts/qa_check.py --content assets/examples/register.md /tmp/qa/*.xlsx
```

`assets/tests/fixture.md` exercises every construct the builders claim to
support (hard-wrapped paragraphs, nested lists, code, quotes, callouts, aligned
tables, an image, a Mermaid diagram, page breaks, comments, speaker notes).
Then look at the rendered pages. Also build each file in `assets/examples/` in
its natural format; they double as cross-department tests.
