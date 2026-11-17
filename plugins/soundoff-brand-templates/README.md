# SoundOff Signal Brand Templates (v2.0)

Branded Word, PDF, PowerPoint, and Excel output for every SoundOff Signal
department. Claude writes the content as Markdown; the bundled builders apply
the brand, the PY-DC classification marking, and the document's identity.

The plugin is named `soundoff-brand-templates`; the version is in
`.claude-plugin/plugin.json`. It does not replace v1.0, which was named
`soundoff-brand-templates-v10`. Remove v1.0 first so the two do not run
side by side.

## What changed in 2.0

**Department-neutral by default**

- No built-in author, department, owner, or cost center. Author and department
  come from the person requesting the document. v1 stamped Cybersecurity, the
  ITCS code, and a named author onto documents from any department.
- Department registry (`references/departments/departments.yaml`) holds each
  department's document-ID code and optional profile. Only Cybersecurity (ITCS)
  has a code today; other departments get no SOS ID until they register one.
- Builds warn, and QA fails, when a document carries another department's code
  or an SOS ID with no department set.
- Cybersecurity's boilerplate, frameworks, and tooling moved out of the core
  into `references/departments/cybersecurity.md`. Company-wide boilerplate with
  `{{placeholders}}` replaces it as the default.
- Version control (status, version history, approvals, review cycle) is for
  controlled documents only; QA flags it on reports and write-ups.

**More capable**

- Layouts: `report` (cover), `brief` (title block, no cover), `memo`
  (To/From/CC/Subject header); `orientation: landscape`; `toc: true` with real
  page numbers in PDF.
- Images with captions and alt text; Mermaid diagrams rendered in the brand
  theme; NOTE / TIP / IMPORTANT / WARNING / CAUTION callouts; page breaks;
  author comments.
- Decks: speaker notes (`???`), pictures and diagrams on slides, continuation
  slides, tables sized to their content.
- Excel: typed numbers, percentages, currency, and dates; formulas with
  `{row}` / `{prev}` / `{first}` / `{last}`; status colors that follow edits;
  dropdowns; every status column colored, not just the first.
- Word tables sized to content instead of equal columns; callouts and short
  code blocks no longer split across pages.
- Tagged PDFs; document properties on decks and workbooks.

**Fixes**

- Word headings now actually render in Oswald (v1 overrode the style with
  Arial at run level, and theme fonts overrode the style itself).
- Titles with & or quotes no longer print as HTML entities (&amp;) in PDF headers.
- FCI citation updated to FAR 52.240-93 (formerly 52.204-21).
- Draft label reads `DRAFT · PENDING APPROVAL`.

**Cleanup**

- SKILL.md rewritten as a short workflow; one reference for syntax
  (`authoring.md`), one for structures (`document-patterns.md`), one for
  maintainers (`brand-reference.md`). Classification and compliance rules are
  stated once instead of three times.
- Starter files for each document type in `skills/.../assets/examples/`.

## Upgrading v1 sources

v1 Markdown still builds. Differences to expect:

- Sources without `author` or `department` no longer get Cybersecurity values.
  Add them.
- `cost_center` is ignored; the code lives in the doc ID and the registry.
- `cover: false` still works and now produces the brief layout with a title
  block on page 1.

## Registering a department

1. Add or edit its entry in `skills/soundoff-brand-templates/references/departments/departments.yaml`
   (`code`, `aliases`, optional `profile`).
2. Optionally copy `_template.md` to `<department>.md` for its own boilerplate.
3. Run the regression in `references/brand-reference.md`.
