---
name: soundoff-brand-templates
description: "Applies SoundOff Signal's brand (PMS 187 red, Oswald headlines, Arial body, logos, PY-DC classification marking) to Word, PDF, PowerPoint, and Excel files for any SoundOff department. Use it WHENEVER someone at SoundOff Signal wants a document, deck, or spreadsheet in one of those formats, even if they never say branded: policies, procedures, work instructions, reports, briefs, memos, proposals, one-pagers, leadership or customer decks, registers, trackers, scorecards, and KPI sheets for IT, Cybersecurity, HR, Quality, Marketing, Sales, Product Development, or leadership. It takes the author and department from the requester, keeps document IDs and version control correct, and handles images, Mermaid diagrams, callouts, memos, landscape pages, speaker notes, and live Excel formulas and status colors. Do NOT use for non-SoundOff documents."
license: Oswald fonts OFL-licensed (assets/fonts/OSWALD-OFL.txt). Logos are SoundOff Signal property.
---

# SoundOff Signal Brand Templates (v2.0)

Write the content once as Markdown with YAML front matter; the builders turn it
into on-brand Word, PDF, PowerPoint, or Excel output with the right marking,
identity, and layout. Brand values live in `scripts/brand.py` and parsing in
`scripts/md_blocks.py`, so every format matches and nothing is restyled by hand.

This skill is shared by every department. It assumes nothing about who is
writing or who owns the document; that comes from the requester, every time.

## 1. Establish who the document is for

Do this before writing front matter, because the author, department, and ID are
printed on every page and indexed in SharePoint.

- **author**: the person you are working with, with their title if known, from
  the conversation or their profile. If you do not know it, leave it out (the
  properties then name the company). Never carry a name over from an example,
  an earlier document, or this skill.
- **department**: the requester's department, using its name in
  `references/departments/departments.yaml` (aliases there resolve). If it is
  not clear and the document needs it (controlled documents, anything with an
  SOS ID), ask once.
- **department profile**: if `departments.yaml` lists a `profile` for that
  department, read it before writing. It holds that department's boilerplate,
  frameworks, and terminology. Departments without one use the company defaults
  in `references/document-patterns.md`. Never borrow another department's
  profile: a Cybersecurity roles table or NIST CSF mapping in an HR policy is
  exactly the kind of leak this version exists to stop.

## 2. Pick the format

| Need | Format | Builder |
|---|---|---|
| Editable formal document sent for review or approval | `.docx` | `scripts/build_docx.py` |
| Fixed, font-portable report, one-pager, or handout | `.pdf` | `scripts/build_pdf.py` |
| Leadership, customer, or training presentation | `.pptx` | `scripts/build_pptx.py` |
| Register, tracker, matrix, scorecard | `.xlsx` | `scripts/build_xlsx.py` |

Default to `.docx` for formal written documents people will edit or approve.
Use `.pdf` when it must look identical everywhere. One Markdown source builds in
any format, so producing a `.docx` and a `.pdf` together costs nothing.

## 3. Decide: controlled or working document

Version control tells a reader the document went through approval. On a
one-off write-up it misleads them, so it belongs only on controlled documents.

| | Controlled | Working |
|---|---|---|
| Examples | policy, standard, procedure, work instruction, plan, runbook, guideline, form | report, brief, memo, proposal, recommendation, investigation write-up, deck, tracker |
| Front matter | `version`, `status`, `review_cycle`, `version_history`, `approvals`; `doc_id` if the department has a code | none of those; `doc_id` only if the department files that kind of record by ID |
| Structure | the controlled skeleton in `references/document-patterns.md` | whatever serves the reader (shapes in the same file) |

`status` is one of `draft`, `in review`, `approved`, `ratified`, `retired`. A
draft prints `v1.0 DRAFT · PENDING APPROVAL` on the cover and footer.

## 4. Document IDs

Format: `SOS-<dept code>-<type code>-<SUBJECT>`, for example
`SOS-<code>-PR-VENDORS` for a department's vendor-management procedure.

- The department code comes only from `departments.yaml`, for the document's
  own department. A department with no code gets no SOS ID; if it has its own
  numbering scheme, use that instead.
- Never reuse another department's code. The builders warn and `qa_check.py`
  fails when a document carries a code that is not its department's, or an ID
  with no department set.
- Type codes: PY Policy, ST Standard, PR Procedure, WI Work Instruction, PL Plan,
  RB Runbook, GD Guideline, FM Form, RG Register, RP Report, MM Memo.
- With `--output <folder>/`, the filename is derived from the ID, title, and
  version (`<doc_id>_<Title>_v<version>.docx`), dropping whatever is not set.

## 5. Write the content

Start from the closest file in `assets/examples/`: `controlled-document.md`
(skeleton with `{{placeholders}}`), `report-brief.md`, `memo.md`, `deck.md`,
`register.md`. Read `references/authoring.md` for the full front-matter schema
and syntax. Beyond standard Markdown (headings, lists, tables, code, links):

| Write | Get |
|---|---|
| `![Caption](chart.png){width=60%}` on its own line | image with caption and alt text (path relative to the .md file) |
| a ` ```mermaid ` block, optional first line `%% caption: Text` | brand-themed diagram (Word, PDF, deck) |
| `> [!NOTE]` / `[!TIP]` / `[!IMPORTANT]` / `[!WARNING]` / `[!CAUTION]` | colored callout box |
| `<!-- pagebreak -->` | page break; in a deck, a continuation slide |
| `<!-- any other comment -->` | nothing (author notes) |
| `???` line in a deck | everything after it on that slide becomes speaker notes |
| `=== SECTION: Text` / `=== CLOSING` | deck divider / ending slide |
| `=E{row}*F{row}`, `=SUM(G{first}:G{prev})` in a table cell | live Excel formula |

Front-matter layout options (Word and PDF): `layout: report` (cover page,
default), `layout: brief` (title block on page 1, no cover), `layout: memo`
(MEMORANDUM header with `to`, `from`, `cc`, `subject`); `orientation:
landscape` for wide tables; `toc: true` for a contents page.

## 6. Build, check, deliver

```bash
python scripts/build_docx.py --content doc.md --output /mnt/user-data/outputs/ --strict
python scripts/qa_check.py --content doc.md /mnt/user-data/outputs/<file>.docx
```

- `--strict` turns every warning (missing image, unrenderable block, another
  department's code) into a failed build. Use it for anything you deliver.
- `qa_check.py` is a gate: marking on every page, identity, no literal
  Markdown, no unfilled `{{placeholders}}`, real Word headings, alt text,
  document properties. Fix failures; do not explain them away.
- Then look at the rendered pages for layout only:
  `soffice --headless --convert-to pdf --outdir /tmp <file>` and
  `pdftoppm -png -r 60 /tmp/<file>.pdf /tmp/page`. PDF output renders directly.
- Builders print a one-line summary and report anything they could not
  represent; nothing is dropped silently.

## Classification marking

Authority: the SoundOff PY-DC Data Classification Policy, company-wide.

| `classification` | Printed | Treatment |
|---|---|---|
| `PUBLIC` | PUBLIC | customer-facing material |
| `INTERNAL USE` (default) | INTERNAL USE ONLY | footer marking, cover banner |
| `CONFIDENTIAL` | CONFIDENTIAL | same |
| `HIGHLY CONFIDENTIAL` | HIGHLY CONFIDENTIAL | marking repeated top and bottom of every page, strip above the cover |

Any other value fails the build. Pick the level from what the content is, not
from caution: over-marking trains people to ignore the marking. Never mark
below what the requester asked for. SoundOff holds no CUI; `CUI` is accepted
only with a warning to confirm a contract actually requires it.

## Dependencies

```bash
pip install --break-system-packages weasyprint pyyaml python-docx python-pptx openpyxl pillow
npm install -g @mermaid-js/mermaid-cli     # optional: Mermaid diagrams
mkdir -p ~/.fonts && cp assets/fonts/Oswald-*.ttf ~/.fonts && fc-cache -f ~/.fonts   # accurate previews
```

Builders check imports at startup and print the install line if something is
missing. Without the Mermaid CLI, diagrams stay as source text and the build
warns. Oswald is embedded in PDFs; Word and PowerPoint reference it by name, so
endpoints need it installed for exact rendering (PDF when that matters).

## Reference map

| File | Read when |
|---|---|
| `references/authoring.md` | writing any content: front matter, syntax, per-format behavior |
| `references/document-patterns.md` | choosing a structure; generic controlled-document boilerplate |
| `references/departments/departments.yaml` | finding the requester's department, code, and profile |
| `references/departments/<profile>.md` | the department has a profile (step 1) |
| `references/brand-reference.md` | changing the skill itself: tokens, templates, regression fixtures, adding a department |
