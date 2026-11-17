#!/usr/bin/env python3
"""
SoundOff Signal branded PDF builder.

Renders a Markdown content file (with YAML front matter) into a brand-compliant
PDF: PMS 187 red, embedded Oswald headlines, Arial body, running header, footer
classification marking, bookmarks, document metadata, and tagged structure for
screen readers.

Layouts (front matter `layout:`): report (full-bleed cover, default), brief
(title block on page 1, also `cover: false`), memo (MEMORANDUM header).
`orientation: landscape` turns the page; `toc: true` (or --toc) adds a
contents page with page numbers.

Markdown is parsed by md_blocks.py from the same block model the Word, deck,
and Excel builders consume, so the four formats cannot drift.

Usage:
    python build_pdf.py --content body.md --output out.pdf [--toc] [--strict]
"""
import argparse
import base64
import html as _html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brand  # noqa: E402

brand.require("yaml", "weasyprint")

from weasyprint import HTML  # noqa: E402

import md_blocks as M  # noqa: E402
import media  # noqa: E402

SKILL = str(brand.SKILL_ROOT)
FONTS = str(brand.FONTS_DIR)


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _font_face(family, file, weight, style="normal"):
    p = os.path.join(FONTS, file)
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};"
        f"font-style:{style};src:url('file://{p}') format('truetype');}}"
    )


def _esc(text):
    return _html.escape(str(text or ""), quote=True)


def _css_str(text):
    """Escape a value for a CSS content: "..." string."""
    return str(text or "").replace("\\", "\\\\").replace('"', '\\"')


def build_css(meta):
    logo_color = _b64(str(brand.logo_path("full_color")))
    classification = meta["classification"]
    dual = meta["_dual_banner"]
    land = meta["_landscape"]
    doc_title = _css_str(meta.get("title", ""))
    doc_id = _css_str(meta.get("doc_id", ""))
    status = brand.status_label(meta.get("status"), meta.get("version"))
    header_sub = "  ·  ".join(b for b in (doc_id, _css_str(status or "")) if b)
    footer_left = classification.upper()
    footer_center = classification.upper() if dual else (doc_id or doc_title)
    top_center = classification.upper() if dual else ""
    page_w, page_h = ("279.4mm", "215.9mm") if land else ("215.9mm", "279.4mm")
    band_h = 64 if land else 92
    logo_top, doctype_top = (14, 46) if land else (22, 66)
    body_top = band_h + (10 if land else 12)

    faces = "".join(_font_face("Oswald", f, w)
                    for w, f in brand.OSWALD_WEIGHTS.items())

    callout_css = "".join(
        f".callout-{k} {{ border-left-color: {brand.HEX[a]}; "
        f"background: {brand.HEX[t]}; }} "
        f".callout-{k} .callout-title {{ color: {brand.HEX[a]}; }}\n"
        for k, (_, a, t) in brand.CALLOUTS.items())

    return f"""
{faces}

@page {{
    size: Letter {'landscape' if land else 'portrait'};
    margin: 26mm 18mm 22mm 18mm;
    @top-left {{
        content: "";
        background-image: url('data:image/png;base64,{logo_color}');
        background-repeat: no-repeat;
        background-size: contain;
        background-position: left center;
        width: 46mm; height: 12mm;
    }}
    @top-right {{
        content: "{doc_title}\\A {header_sub}";
        white-space: pre-line;
        font-family: 'Oswald'; font-weight: 500; font-size: 8pt;
        letter-spacing: .06em; text-transform: uppercase; color: {brand.GRAY};
        text-align: right; line-height: 1.35;
        vertical-align: bottom; padding-bottom: .5mm;
    }}
    @top-center {{
        content: "{top_center}";
        font-family: 'Liberation Sans','Arial',sans-serif; font-size: 7.5pt;
        font-weight: 700; letter-spacing: .14em; color: {brand.RED};
        vertical-align: bottom; padding-bottom: 1mm;
    }}
    @bottom-left {{
        content: "{footer_left}";
        font-family: 'Liberation Sans','Arial',sans-serif; font-size: 7pt;
        font-weight: 700; letter-spacing: .08em; color: {brand.RED};
    }}
    @bottom-center {{
        content: "{footer_center}";
        font-family: 'Liberation Sans','Arial',sans-serif; font-size: 7pt;
        font-weight: {700 if dual else 400};
        letter-spacing: {'.14em' if dual else '0'};
        color: {brand.RED if dual else brand.GRAY};
    }}
    @bottom-right {{
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Liberation Sans','Arial',sans-serif; font-size: 7pt;
        color: {brand.GRAY};
    }}
}}

@page cover {{
    margin: 0;
    @top-left {{ content: none; }}
    @top-right {{ content: none; }}
    @top-center {{ content: none; }}
    @bottom-left {{ content: none; }}
    @bottom-center {{ content: none; }}
    @bottom-right {{ content: none; }}
}}

html {{ font-family: 'Liberation Sans','Arial',sans-serif; color: {brand.INK};
        font-size: 10.5pt; line-height: 1.5; }}

h1,h2,h3,h4,h5,h6 {{ font-family: 'Oswald'; color: {brand.INK};
               line-height: 1.15; margin: 0 0 .35em; break-after: avoid; }}
h1 {{ font-weight: 700; font-size: 19pt; letter-spacing: .01em;
      color: {brand.RED}; border-bottom: 2.5pt solid {brand.RED};
      padding-bottom: 3pt; margin-top: .6em; }}
main > h1:first-child, .titleblock + h1, .memo + h1 {{ margin-top: 0; }}
h2 {{ font-weight: 600; font-size: 14pt; margin-top: 1.1em;
      text-transform: uppercase; letter-spacing: .03em; }}
h3 {{ font-weight: 600; font-size: 11.5pt; color: {brand.RED_DARK};
      margin-top: .9em; }}
h4,h5,h6 {{ font-weight: 500; font-size: 10.5pt; color: {brand.GRAY};
      text-transform: uppercase; letter-spacing: .05em; }}

p {{ margin: 0 0 .7em; }}
ul,ol {{ margin: 0 0 .8em; padding-left: 1.4em; }}
li {{ margin-bottom: .25em; }}
li > ul, li > ol {{ margin: .25em 0 .1em; }}
a {{ color: {brand.RED}; text-decoration: underline; }}
strong {{ color: {brand.INK}; }}
em {{ font-style: italic; }}
code {{ font-family: 'Liberation Mono',monospace; font-size: 9pt;
        background: {brand.CODE_BG}; padding: 1px 4px; border-radius: 2px; }}
pre {{ background: {brand.CODE_BG}; border-left: 3pt solid {brand.RED};
       padding: 8pt 10pt; font-family: 'Liberation Mono',monospace;
       font-size: 8.5pt; line-height: 1.4; overflow-wrap: break-word;
       white-space: pre-wrap; break-inside: avoid; margin: 0 0 .8em; }}
pre code {{ background: none; padding: 0; }}
blockquote {{ margin: 0 0 .8em; padding: 6pt 12pt;
              border-left: 3pt solid {brand.GRAY_LIGHT};
              color: {brand.GRAY}; font-style: italic; }}
blockquote p {{ margin: 0; }}

.callout {{ border-left: 4pt solid {brand.GRAY}; padding: 7pt 12pt 3pt;
            margin: 0 0 .9em; break-inside: avoid; }}
.callout-title {{ font-family: 'Oswald'; font-weight: 600; font-size: 9pt;
                  text-transform: uppercase; letter-spacing: .12em;
                  margin-bottom: 3pt; }}
.callout p {{ margin: 0 0 .45em; }}
{callout_css}

figure {{ margin: .3em 0 1em; text-align: center; break-inside: avoid; }}
figure img {{ max-width: 100%; max-height: {'135mm' if land else '190mm'}; }}
figcaption {{ font-size: 8.5pt; color: {brand.GRAY}; font-style: italic;
              margin-top: 3pt; }}
.pagebreak {{ break-after: page; height: 0; }}

table {{ border-collapse: collapse; width: 100%; margin: .4em 0 1em;
         font-size: 9.5pt; }}
thead {{ display: table-header-group; }}
tr {{ break-inside: avoid; }}
th {{ background: {brand.RED}; color: #fff; font-family: 'Oswald';
      font-weight: 500; text-align: left; padding: 5pt 8pt;
      text-transform: uppercase; letter-spacing: .03em; font-size: 8.5pt; }}
td {{ padding: 5pt 8pt; border-bottom: .75pt solid {brand.RULE};
      vertical-align: top; }}
tbody tr:nth-child(even) td {{ background: {brand.BAND_EVEN}; }}

hr {{ border: none; border-top: .75pt solid {brand.RULE}; margin: 1.2em 0; }}

/* ---------------- Contents ---------------- */
.toc {{ break-after: page; }}
.toc ul {{ list-style: none; padding: 0; margin: 0; }}
.toc li {{ margin: 0 0 4pt; }}
.toc li.l2 {{ padding-left: 14pt; font-size: 9.5pt; color: {brand.GRAY}; }}
.toc a {{ color: {brand.INK}; text-decoration: none; }}
.toc li.l2 a {{ color: {brand.GRAY}; }}
.toc a::after {{ content: leader('.') target-counter(attr(href), page);
                 color: {brand.GRAY}; }}

/* ---------------- Brief title block ---------------- */
.titleblock {{ border-bottom: 3pt solid {brand.RED}; padding-bottom: 6pt;
               margin-bottom: 14pt; }}
.tb-type {{ font-family: 'Oswald'; font-weight: 600; font-size: 9.5pt;
            color: {brand.RED}; text-transform: uppercase;
            letter-spacing: .14em; }}
.tb-title {{ font-family: 'Oswald'; font-weight: 700; font-size: 24pt;
             line-height: 1.1; margin: 2pt 0 2pt; }}
.tb-sub {{ font-family: 'Oswald'; font-weight: 300; font-size: 13pt;
           color: {brand.GRAY}; margin-bottom: 4pt; }}
.tb-meta {{ font-size: 8.5pt; color: {brand.GRAY}; }}
.tb-status {{ font-family: 'Oswald'; font-weight: 600; font-size: 9pt;
              letter-spacing: .14em; text-transform: uppercase;
              margin-top: 3pt; }}
.tb-status.draft {{ color: {brand.RED}; }} .tb-status.final {{ color: {brand.GRAY}; }}

/* ---------------- Memo ---------------- */
.memo {{ border-bottom: 3pt solid {brand.RED}; padding-bottom: 6pt;
         margin-bottom: 16pt; }}
.memo-label {{ font-family: 'Oswald'; font-weight: 700; font-size: 26pt;
               color: {brand.RED}; text-transform: uppercase;
               letter-spacing: .08em; margin-bottom: 8pt; }}
.memo table {{ width: auto; margin: 0; font-size: 10.5pt; }}
.memo td {{ border: none; padding: 2pt 0; background: none !important; }}
.memo td.k {{ font-family: 'Oswald'; font-weight: 500; font-size: 9pt;
              color: {brand.GRAY}; text-transform: uppercase;
              letter-spacing: .1em; padding-right: 12mm; white-space: nowrap; }}
.memo tr.subject td.v {{ font-weight: 700; }}

/* ---------------- Cover ---------------- */
.cover {{ page: cover; position: relative; width: {page_w}; height: {page_h};
          page-break-after: always; color: {brand.INK}; }}
.cover-band {{ position: absolute; top: 0; left: 0; right: 0; height: {band_h}mm;
    background: linear-gradient(135deg, {brand.RED} 0%, {brand.RED_DARK} 100%); }}
.cover-band:after {{ content: ""; position: absolute; bottom: 0; left: 0; right: 0;
    height: 6mm; background: repeating-linear-gradient(135deg,
    rgba(255,255,255,.0) 0 6mm, rgba(255,255,255,.10) 6mm 7.5mm); }}
.cover-logo {{ position: absolute; top: {logo_top}mm; left: 22mm;
               width: {78 if land else 92}mm; }}
.cover-doctype {{ position: absolute; top: {doctype_top}mm; left: 23mm; right: 22mm;
    font-family: 'Oswald'; font-weight: 500; font-size: 12pt; color: #fff;
    text-transform: uppercase; letter-spacing: .14em; opacity: .92; }}
.cover-body {{ position: absolute; top: {body_top}mm; left: 22mm; right: 22mm; }}
.cover-title {{ font-family: 'Oswald'; font-weight: 700;
    font-size: {30 if land else 34}pt; line-height: 1.05; color: {brand.INK};
    margin: 0 0 4mm; }}
.cover-subtitle {{ font-family: 'Oswald'; font-weight: 300; font-size: 16pt;
    color: {brand.GRAY}; margin: 0 0 {5 if land else 8}mm; line-height: 1.2; }}
.cover-rule {{ width: 38mm; height: 3pt; background: {brand.RED};
    margin-bottom: {4 if land else 5}mm; }}
.cover-status {{ font-family: 'Oswald'; font-weight: 600; font-size: 10pt;
    letter-spacing: .16em; text-transform: uppercase;
    margin-bottom: {4 if land else 7}mm; }}
.cover-status.draft {{ color: {brand.RED}; }}
.cover-status.final {{ color: {brand.GRAY}; }}
.cover-meta {{ font-size: 10pt; color: {brand.INK}; }}
.cover-meta table {{ width: auto; margin: 0; }}
.cover-meta td {{ border: none; padding: {'1.2pt' if land else '2pt'} 0;
    background: none !important; }}
.cover-meta .k {{ font-family: 'Oswald'; font-weight: 500;
    text-transform: uppercase; letter-spacing: .05em; font-size: 8.5pt;
    color: {brand.GRAY}; padding-right: 10mm; white-space: nowrap; }}
.cover-meta .v {{ font-size: 10pt; color: {brand.INK}; }}
.cover-class {{ position: absolute; bottom: 0; left: 0; right: 0;
    background: {brand.INK}; color: #fff; text-align: center; padding: 4mm 0;
    font-family: 'Liberation Sans','Arial',sans-serif; font-weight: 700;
    font-size: 9pt; letter-spacing: .18em; text-transform: uppercase; }}
.cover-class .dot {{ color: {brand.RED}; }}
.cover-banner-top {{ position: absolute; top: 0; left: 0; right: 0; z-index: 5;
    background: #fff; color: {brand.RED}; text-align: center; padding: 2.5mm 0;
    font-family: 'Liberation Sans','Arial',sans-serif; font-weight: 700;
    font-size: 9pt; letter-spacing: .2em; border-bottom: 2pt solid {brand.RED}; }}
"""


def render_cover(meta):
    logo_white = _b64(str(brand.logo_path("reverse_white")))
    title = _esc(meta.get("title", "Untitled Document"))
    subtitle = _esc(meta.get("subtitle", ""))
    doc_type = _esc(meta.get("doc_type", ""))
    classification = meta["classification"]

    meta_rows = "".join(
        f'<tr><td class="k">{_esc(k)}</td><td class="v">{_esc(v)}</td></tr>'
        for k, v in brand.cover_rows(meta))
    subtitle_html = (f'<div class="cover-subtitle">{subtitle}</div>'
                     if subtitle else "")
    doctype_html = (f'<div class="cover-doctype">{doc_type}</div>'
                    if doc_type else "")
    status = brand.status_label(meta.get("status"), meta.get("version"))
    status_html = ""
    if status:
        cls = "draft" if brand.is_draft(meta.get("status")) else "final"
        status_html = f'<div class="cover-status {cls}">{_esc(status)}</div>'
    banner_top = (f'<div class="cover-banner-top">{classification.upper()}</div>'
                  if meta["_dual_banner"] else "")

    return f"""
<div class="cover">
  {banner_top}
  <div class="cover-band"></div>
  <img class="cover-logo" alt="{_esc(brand.COMPANY)}"
       src="data:image/png;base64,{logo_white}"/>
  {doctype_html}
  <div class="cover-body">
    <div class="cover-title">{title}</div>
    {subtitle_html}
    <div class="cover-rule"></div>
    {status_html}
    <div class="cover-meta"><table><tbody>{meta_rows}</tbody></table></div>
  </div>
  <div class="cover-class">{classification} <span class="dot">|</span>
    {brand.COMPANY}</div>
</div>
"""


def render_title_block(meta):
    parts = ['<div class="titleblock">']
    if meta.get("doc_type"):
        parts.append(f'<div class="tb-type">{_esc(meta["doc_type"])}</div>')
    parts.append(f'<div class="tb-title">'
                 f'{_esc(meta.get("title", "Untitled Document"))}</div>')
    if meta.get("subtitle"):
        parts.append(f'<div class="tb-sub">{_esc(meta["subtitle"])}</div>')
    line = [str(b) for b in (meta.get("doc_id"), meta.get("author"),
                             meta.get("date"), meta.get("department")) if b]
    if line:
        parts.append(f'<div class="tb-meta">{"   |   ".join(map(_esc, line))}'
                     "</div>")
    status = brand.status_label(meta.get("status"), meta.get("version"))
    if status:
        cls = "draft" if brand.is_draft(meta.get("status")) else "final"
        parts.append(f'<div class="tb-status {cls}">{_esc(status)}</div>')
    parts.append("</div>")
    return "".join(parts)


def render_memo_block(meta):
    rows = [("To", meta.get("to")), ("From", meta.get("from")),
            ("CC", meta.get("cc")), ("Date", meta.get("date")),
            ("Subject", meta.get("subject"))]
    trs = []
    for k, v in rows:
        if not v:
            continue
        if isinstance(v, (list, tuple)):
            v = ", ".join(str(x) for x in v)
        cls = ' class="subject"' if k == "Subject" else ""
        trs.append(f'<tr{cls}><td class="k">{k}</td>'
                   f'<td class="v">{_esc(v)}</td></tr>')
    label = _esc(meta.get("doc_type") or "Memorandum")
    return (f'<div class="memo"><div class="memo-label">{label}</div>'
            f'<table><tbody>{"".join(trs)}</tbody></table></div>')


def render_document_control(meta):
    """Version History / Approvals, matching the Word builder."""
    vh = meta.get("version_history") or []
    ap = meta.get("approvals") or []
    if not vh and not ap:
        return ""
    out = ['<h1 id="document-control">Document Control</h1>']
    if vh:
        out.append("<h3>Version History</h3><table><thead><tr>"
                   "<th>Version</th><th>Date</th><th>Author</th>"
                   "<th>Description</th><th>Approved By</th></tr></thead><tbody>")
        for e in vh:
            out.append("<tr>" + "".join(
                f"<td>{_esc(e.get(k, ''))}</td>"
                for k in ("version", "date", "author", "description",
                          "approved")) + "</tr>")
        out.append("</tbody></table>")
    if ap:
        out.append("<h3>Approvals</h3><table><thead><tr><th>Name</th>"
                   "<th>Role</th><th>Date</th></tr></thead><tbody>")
        for e in ap:
            out.append("<tr>" + "".join(
                f"<td>{_esc(e.get(k, ''))}</td>"
                for k in ("name", "role", "date")) + "</tr>")
        out.append("</tbody></table>")
    return "".join(out)


def render_toc(meta, blocks, ids):
    items = []
    if meta.get("version_history") or meta.get("approvals"):
        items.append('<li class="l1"><a href="#document-control">'
                     'Document Control</a></li>')
    for b in blocks:
        if b["type"] == "heading" and b["level"] <= 2 and id(b) in ids:
            items.append(f'<li class="l{b["level"]}"><a href="#{ids[id(b)]}">'
                         f'{_esc(M.plain_text(b["inlines"]))}</a></li>')
    return (f'<div class="toc"><h1>Contents</h1><ul>{"".join(items)}</ul>'
            "</div>")


def render_meta_tags(meta):
    """WeasyPrint maps these onto real PDF document properties."""
    props = brand.properties(meta)
    tags = [
        f'<title>{_esc(props["title"])}</title>',
        f'<meta name="author" content="{_esc(props["author"])}"/>',
        f'<meta name="description" content="{_esc(props["comments"])}"/>',
        f'<meta name="keywords" content="{_esc(props["keywords"])}"/>',
        f'<meta name="generator" content="{_esc(brand.COMPANY)} brand '
        f'templates {brand.SKILL_VERSION} (build_pdf.py)"/>',
        f'<meta name="dcterms.created" content="{_esc(meta.get("date"))}"/>',
    ]
    return "".join(tags)


def main():
    parser = argparse.ArgumentParser(
        description="SoundOff Signal branded PDF builder")
    brand.add_common_args(parser, paged=True)
    args = parser.parse_args()

    report = brand.BuildReport("pdf", strict=args.strict)
    with open(args.content, encoding="utf-8") as f:
        raw = f.read()
    front, body_md = M.split_front_matter(raw)
    meta = brand.resolve_meta(front, args, report)
    output = brand.resolve_output(args.output, meta, "pdf")

    blocks, warnings = M.parse_with_warnings(body_md)
    for w in warnings:
        report.warn(w)
    blocks, n_notes = M.strip_notes(blocks)
    if n_notes:
        report.info(f"{n_notes} speaker-notes section(s) (???) left out; "
                    "they appear only in decks")
    blocks = media.prepare(blocks, media.base_dir_of(args.content), report,
                           "pdf")
    for block, _ in M.walk(blocks):
        report.count({"heading": "headings", "para": "paragraphs",
                      "list": "lists", "code": "code blocks",
                      "table": "tables", "quote": "blockquotes",
                      "callout": "callouts", "image": "figures",
                      "pagebreak": "page breaks",
                      "hr": "rules"}.get(block["type"], block["type"]))

    ids = M.heading_ids(blocks)
    body_html = M.to_html(blocks, ids)
    layout = meta["_layout"]
    if layout == "report":
        front_html = render_cover(meta)
    elif layout == "memo":
        front_html = render_memo_block(meta)
    else:
        front_html = render_title_block(meta)
    toc_html = render_toc(meta, blocks, ids) if meta["_toc"] else ""
    if layout == "report":
        pre, main_open = front_html + toc_html, ""
    else:
        pre, main_open = "", front_html + toc_html

    full = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'{render_meta_tags(meta)}<style>{build_css(meta)}</style></head>'
            f'<body>{pre}<main>{main_open}{render_document_control(meta)}'
            f'{body_html}</main></body></html>')

    doc = HTML(string=full, base_url=SKILL)
    try:
        doc.write_pdf(output, pdf_tags=True)
    except TypeError:  # older WeasyPrint without tagged-PDF support
        doc.write_pdf(output)
    report.finish(output, empty=M.is_empty(blocks))


if __name__ == "__main__":
    main()
