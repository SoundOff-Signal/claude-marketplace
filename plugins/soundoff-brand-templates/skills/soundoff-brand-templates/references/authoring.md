# Authoring reference: front matter, syntax, per-format behavior

All four builders read the same Markdown + YAML front matter, parsed once by
`scripts/md_blocks.py`, so a source written for one format builds in the others.

Contents: Front matter · CLI · Markdown syntax · Word · PDF · PowerPoint · Excel

## Front matter

Every key is optional except `title`. Every key is also a CLI flag with dashes
(`--doc-type Procedure`, `--classification CONFIDENTIAL`), and the CLI wins.

| Key | Use | Notes |
|---|---|---|
| `title` | document title | required |
| `subtitle` | secondary line | |
| `doc_type` | label on the cover / title slide: Policy, Procedure, Report, Memo... | also tells QA whether the document is controlled |
| `doc_id` | `SOS-<dept code>-<type code>-<SUBJECT>` or the department's own number | only with a registered code; see SKILL.md step 4 |
| `author` | the requester, "Name, Title" | never a default person |
| `department` | owning department, as named in `departments.yaml` | drives the ID check |
| `owner` | owning role or team, when it differs from the department | |
| `date` | ISO date | defaults to today |
| `classification` | PUBLIC, INTERNAL USE, CONFIDENTIAL, HIGHLY CONFIDENTIAL | defaults to INTERNAL USE |
| `version` | controlled documents | |
| `status` | controlled documents: draft, in review, approved, ratified, retired | prints a badge |
| `review_cycle` | controlled documents: Annual, Biennial... | |
| `version_history` | controlled documents: list of `version, date, author, description, approved` | renders a Document Control section |
| `approvals` | controlled documents: list of `name, role, date` | |
| `framework` | standards the document maps to, free text | shown on the cover as Framework |
| `nist_csf` | NIST CSF 2.0 functions/categories | for departments whose profile uses CSF |
| `reference` | related ticket, project, or source document | |
| `layout` | `report` (cover, default), `brief` (title block, no cover), `memo` | Word and PDF; `cover: false` means brief |
| `orientation` | `portrait` (default) or `landscape` | Word and PDF |
| `toc` | `true` for a contents page | Word inserts a TOC field (right-click, Update Field); PDF prints page numbers |
| `to`, `from`, `cc`, `subject` | memo header | `from` defaults to author, `subject` to title |

Keys from v1 that are no longer used (`cost_center`, `cover`) are ignored or
mapped, so old sources still build.

## CLI

```bash
python scripts/build_<fmt>.py --content doc.md --output <file or folder/> [--strict] [--toc]
python scripts/qa_check.py --content doc.md <outputs...> [--strict] [--no-render]
```

- `--output folder/` derives the filename from doc_id, title, and version.
- `--strict` fails the build on any warning. Use it for deliverables.
- `qa_check.py --classification X` when the build overrode the front-matter
  marking on the command line.

## Markdown syntax

| Construct | Syntax | Renders as |
|---|---|---|
| Headings | `#` to `######` | Word Heading 1 to 4 styles; PDF bookmarks; deck dividers (`#`) and slide titles (`##`); Excel sheet names (`#`/`##`) |
| Paragraph | hard-wrapped lines | one paragraph; source line breaks are joined |
| Bullets / numbers | `-`, `*`, `+` / `1.`, `1)`; nest by indenting 2 to 4 spaces | real lists, three visual levels; numbering restarts per list |
| Inline | `**bold**`, `*italic*`, `` `code` ``, `[text](url)`, `\*` escapes | bold, italic, mono, live link, literal |
| Table | pipe table with a `---` row; `:--:` center, `--:` right | red header, banding, columns sized to content |
| Code | fenced with ``` or ~~~, optional language | shaded box with a red rule |
| Blockquote | `> text` | gray italic quote |
| Callout | `> [!NOTE]` (or TIP, IMPORTANT, WARNING, CAUTION), optional title after it | tinted box with a colored label; kept on one page in Word |
| Image | `![Caption](path.png)` alone on a line, optional `{width=60%}` | centered figure, caption from the alt text, alt text for screen readers |
| Diagram | ` ```mermaid ` block; optional first line `%% caption: Text` | brand-themed PNG (needs the Mermaid CLI) |
| Rule | `---` | hairline |
| Page break | `<!-- pagebreak -->` or `\pagebreak` | new page; in a deck, a "(cont.)" slide |
| Comment | `<!-- ... -->` | dropped from output |
| Speaker notes | a `???` line | deck: rest of that slide goes to notes; other formats: dropped |

Image paths resolve relative to the Markdown file. PNG, JPG, GIF, and BMP work
everywhere; SVG only in PDF. Remote URLs are not fetched: save the file and
reference it by path. A missing image renders as `[missing image: ...]` and
warns. Not supported (reported, not swallowed): footnotes, definition lists,
reference-style links, raw HTML blocks.

**Mermaid tips.** Prefer `flowchart LR` for short processes and `flowchart TD`
for longer ones; keep labels short. Sequence, state, and gantt diagrams work too.
The brand theme is applied automatically; do not add `%%{init}%%` color overrides.

## Word (`build_docx.py`)

- Cover (report layout): red band with the white logo and doc-type label, Oswald
  title, subtitle, red rule, status badge (controlled documents), metadata
  table, classification banner. Brief and memo layouts put a title block or
  memo header on page 1 instead.
- Body pages: running header (logo, title, doc_id and status), footer
  (classification, doc_id or title, page X of Y, draft note).
- Headings are real Heading 1 to 4 styles in Oswald, so the navigation pane,
  TOC, cross-references, and accessibility checker work, and headings a reader
  adds later in Word match.
- Tables: red header row that repeats across pages, banding, widths
  proportional to content. Callouts and short code blocks do not split across
  pages.
- Core properties (title, author, category, keywords, comments with ID,
  version, status, classification) are set for SharePoint.

## PDF (`build_pdf.py`)

Same content and layouts. Oswald is embedded, so it renders identically
anywhere. Bookmarks for every heading, document metadata, and tagged structure
for screen readers. `toc: true` adds a contents page with dotted leaders and
page numbers. Report covers are full-bleed with no running header.

## PowerPoint (`build_pptx.py`)

Decks are built from the corporate template
`assets/templates/soundoff-deck-template.pptx`; the builder fills its layouts
(Title, Divider, Content - Bullets, Ending) and adds tables, pictures, notes, and
the marking.

| Source | Slide |
|---|---|
| front matter | title slide; date, author, version, status in the info line |
| `# Section` | divider slide; content after it gets its own slide |
| `## Title` | content slide; a first paragraph of 105 characters or fewer becomes the red lead-in line |
| `### Subhead` | red subhead inside the slide body |
| lists, code, quotes, callouts | body text |
| table | branded table under the text, narrowed when the content is narrow, smaller type for long tables |
| image or Mermaid | placed in the space left on the slide, centered when it is the only content |
| `???` | speaker notes for that slide |
| `<!-- pagebreak -->` | continue on a new slide titled "Title (cont.)" |
| `=== SECTION: Text` / `=== CLOSING[: Text]` | divider / ending slide ("Thank You!" by default) |

Keep to about 5 to 7 bullets or one table or one picture per slide. The builder
warns when content runs past the body area; split the slide (a page-break
comment is the quickest way). Marking sits at the bottom of every slide; HIGHLY
CONFIDENTIAL adds a top banner.

## Excel (`build_xlsx.py`)

Front matter plus one or more pipe tables. Each `#` or `##` heading starts a
sheet; paragraphs, lists, and callouts before a table become note lines under
the banner.

- **Typed cells.** `42` and `1,250.5` become numbers, `45%` a percentage,
  `$1,200` currency, `2026-11-17` a date, so sorting and filtering work.
- **Formulas.** A cell starting with `=` is a formula. `{row}` is the cell's own
  row, `{prev}` the row above, `{first}` and `{last}` the first and last table
  rows. Row score: `=E{row}*F{row}`. Totals row: `=SUM(G{first}:G{prev})`.
  Formulas compute when the file opens in Excel.
- **Live status columns.** A column named Severity, Priority, Status, Risk
  Level, Rating, Result, State, or Health gets conditional formatting (the color
  follows the value when someone edits it) and a dropdown of the allowed values.
  Severity-type columns use the scale Critical, High, Medium, Low. Recognized
  words: Critical/High/Medium/Low; Open, Blocked, Overdue, Fail (red); At Risk
  (amber); In Progress, In Review, Pending (yellow); Not Started, Planned, On
  Hold, Deferred, Accepted (gray); Closed, Resolved, Done, Complete, Pass, On
  Track, Mitigated (green).
- **KPI tiles.** `## Scoreboard [metrics]` with a `Metric | Value | Target |
  Context` table renders tiles: red label, large blue value, gray caption. Keep
  raw data on its own sheet and state direction (lower or higher is better).
- Layout: red title banner, subtitle line, classification and metadata line,
  frozen header row, autofilter, banding, landscape fit-to-width printing with
  the marking in the footer, workbook properties set.
- Prose a worksheet cannot hold (code, quotes, images) is reported, not dropped.
  Put narrative in a Word or PDF document.
