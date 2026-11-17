#!/usr/bin/env python3
"""
SoundOff Signal branded Word (.docx) builder.

Renders a Markdown content file (with YAML front matter) into a brand-compliant
Word document: PMS 187 red headlines and rules, Oswald headings, Arial body,
running header with logo, footer classification marking, and (for controlled
documents) a Document Control section.

Layouts (front matter `layout:`):
  report  cover page, then body (default)
  brief   compact title block on page 1, no cover (also `cover: false`)
  memo    MEMORANDUM header with To / From / CC / Date / Subject

Word-specific commitments, because Word is the review format:
  * Headings are real Heading 1-4 styles, so the navigation pane, a TOC field,
    cross-references, and Word's accessibility checker all work.
  * Core document properties are populated for SharePoint.
  * Lists, code, quotes, callouts, images (with alt text), Mermaid diagrams,
    hyperlinks, and page breaks render as themselves. Parsing is shared with the
    other builders via md_blocks.py, so Word and PDF output cannot diverge.

Usage:
    python build_docx.py --content body.md --output out.docx [--toc] [--strict]

--output may be a directory, in which case the filename is derived from doc_id,
title, and version.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brand  # noqa: E402

brand.require("yaml", "docx")

from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402
from docx.enum.style import WD_STYLE_TYPE  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import (WD_ALIGN_PARAGRAPH, WD_BREAK,  # noqa: E402
                            WD_TAB_ALIGNMENT)
from docx.opc.constants import RELATIONSHIP_TYPE as RT  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Pt, RGBColor, Twips  # noqa: E402

import md_blocks as M  # noqa: E402
import media  # noqa: E402

R = lambda name: RGBColor(*brand.RGB[name])  # noqa: E731

# US Letter with 0.75in margins, in twips (1440 = 1 inch). main() swaps the page
# for landscape; CONTENT_W / CONTENT_H follow.
PAGE_W = 12240
PAGE_H = 15840
MARGIN = 1080
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN

ALIGN = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
         "right": WD_ALIGN_PARAGRAPH.RIGHT}

HEADING_SPEC = {
    # level: (font, pt, color, bold, caps, tracking, space_before, space_after)
    1: (brand.FONT_HEADLINE, 19, "red", True, False, None, 16, 6),
    2: (brand.FONT_HEADLINE, 14, "ink", True, True, 6, 14, 6),
    3: (brand.FONT_HEADLINE, 11.5, "red_dark", True, False, None, 10, 4),
    4: (brand.FONT_HEADLINE, 10.5, "gray", True, True, 10, 8, 3),
}


# --------------------------------------------------------------------------- #
# Low-level XML helpers
# --------------------------------------------------------------------------- #
def _set_shading(element_pr, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    element_pr.append(shd)


def _cell_shading(cell, hex_color):
    _set_shading(cell._tc.get_or_add_tcPr(), hex_color)


def _borders(pPr, edges, hex_color, size_eighths=20, space=2):
    pbdr = pPr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = OxmlElement("w:pBdr")
        pPr.append(pbdr)
    for edge in edges:
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size_eighths))
        el.set(qn("w:space"), str(space))
        el.set(qn("w:color"), hex_color.lstrip("#"))
        pbdr.append(el)


def _para_border(paragraph, edges, hex_color, size_eighths=20, space=2):
    _borders(paragraph._p.get_or_add_pPr(), edges, hex_color, size_eighths,
             space)


def _tracking(run, twentieths):
    rPr = run._r.get_or_add_rPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:val"), str(twentieths))
    rPr.append(sp)


_THEME_ATTRS = ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme")


def _set_fonts(rPr, name):
    """Bind ascii/hAnsi/cs to a font and drop theme-font attributes, which
    otherwise win over the explicit font (Word would show Calibri Light)."""
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in _THEME_ATTRS:
        if rFonts.get(qn(attr)) is not None:
            del rFonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rFonts.set(qn(attr), name)


def _bind_font(run, name):
    _set_fonts(run._r.get_or_add_rPr(), name)


def _cell_margins(cell, top=80, left=140, bottom=80, right=140):
    """Inner padding for single-cell boxes (code, callouts), in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for edge, val in (("top", top), ("left", left), ("bottom", bottom),
                      ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def _runs(paragraph, text, font=brand.FONT_BODY, size=10.5, color="ink",
          bold=False, italic=False, caps=False, spacing=None, underline=False):
    run = paragraph.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    run.font.color.rgb = R(color)
    if caps:
        run.font.all_caps = True
    if spacing is not None:
        _tracking(run, spacing)
    _bind_font(run, font)
    return run


def _add_field(run, instruction, placeholder=None):
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(sep)
    if placeholder:
        t = OxmlElement("w:t")
        t.text = placeholder
        run._r.append(t)
    run._r.append(end)


def _hyperlink(paragraph, url, text, size=10.5):
    """A real Word hyperlink, not blue-looking text."""
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = _runs(paragraph, text, size=size, color="red", underline=True)
    run._r.getparent().remove(run._r)
    link.append(run._r)
    paragraph._p.append(link)
    return run


# --------------------------------------------------------------------------- #
# Styles: real Heading 1-4 plus code/quote/caption
# --------------------------------------------------------------------------- #
def _define_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = brand.FONT_BODY
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = R("ink")
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15
    _set_fonts(normal.element.get_or_add_rPr(), brand.FONT_BODY)

    for level, spec in HEADING_SPEC.items():
        font, size, color, bold, caps, track, before, after = spec
        style = doc.styles[f"Heading {level}"]
        style.base_style = doc.styles["Normal"]
        style.font.name = font
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.italic = False
        style.font.all_caps = caps
        style.font.color.rgb = R(color)
        pf = style.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.keep_with_next = True
        pf.page_break_before = False
        srPr = style.element.get_or_add_rPr()
        _set_fonts(srPr, font)
        if track is not None:
            sp = OxmlElement("w:spacing")
            sp.set(qn("w:val"), str(track))
            srPr.append(sp)
        if level == 1:
            _borders(style.element.get_or_add_pPr(), ["bottom"], brand.RED, 20, 3)

    # Body-adjacent custom styles.
    def _new(name, kind=WD_STYLE_TYPE.PARAGRAPH):
        if name in [s.name for s in doc.styles]:
            return doc.styles[name]
        return doc.styles.add_style(name, kind)

    code = _new("SOS Code")
    code.base_style = doc.styles["Normal"]
    code.font.name = brand.FONT_MONO
    code.font.size = Pt(8.5)
    code.font.color.rgb = R("ink")
    code.paragraph_format.space_after = Pt(0)
    code.paragraph_format.space_before = Pt(0)
    code.paragraph_format.line_spacing = 1.0
    _set_fonts(code.element.get_or_add_rPr(), brand.FONT_MONO)

    quote = _new("SOS Quote")
    quote.base_style = doc.styles["Normal"]
    quote.font.italic = True
    quote.font.color.rgb = R("gray")
    quote.paragraph_format.left_indent = Twips(280)
    quote.paragraph_format.space_before = Pt(4)
    quote.paragraph_format.space_after = Pt(8)
    _borders(quote.element.get_or_add_pPr(), ["left"], brand.GRAY_LIGHT, 18, 6)

    caption = _new("SOS Caption")
    caption.base_style = doc.styles["Normal"]
    caption.font.size = Pt(8)
    caption.font.color.rgb = R("gray")
    caption.paragraph_format.space_after = Pt(10)


# --------------------------------------------------------------------------- #
# Numbering: one definition per list, so numbering restarts where it should
# --------------------------------------------------------------------------- #
BULLET_CHARS = [("", "Symbol"), ("o", "Courier New"),
                ("", "Wingdings")]
DECIMAL_FMTS = [("decimal", "%1."), ("lowerLetter", "%2."),
                ("lowerRoman", "%3.")]


def _numbering(doc):
    return doc.part.numbering_part.element


def _next_ids(numbering):
    abstract = [int(e.get(qn("w:abstractNumId")))
                for e in numbering.findall(qn("w:abstractNum"))]
    nums = [int(e.get(qn("w:numId"))) for e in numbering.findall(qn("w:num"))]
    return (max(abstract) + 1 if abstract else 0,
            max(nums) + 1 if nums else 1)


def new_list_num(doc, ordered):
    """Create a fresh numbering instance and return its numId."""
    numbering = _numbering(doc)
    abstract_id, num_id = _next_ids(numbering)

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    mlt = OxmlElement("w:multiLevelType")
    mlt.set(qn("w:val"), "hybridMultilevel")
    abstract.append(mlt)
    for ilvl in range(3):
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(ilvl))
        start = OxmlElement("w:start"); start.set(qn("w:val"), "1")
        fmt = OxmlElement("w:numFmt")
        text = OxmlElement("w:lvlText")
        jc = OxmlElement("w:lvlJc"); jc.set(qn("w:val"), "left")
        if ordered:
            numfmt, lvltext = DECIMAL_FMTS[ilvl]
            fmt.set(qn("w:val"), numfmt)
            text.set(qn("w:val"), lvltext)
        else:
            char, font = BULLET_CHARS[ilvl]
            fmt.set(qn("w:val"), "bullet")
            text.set(qn("w:val"), char)
        pPr = OxmlElement("w:pPr")
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), str(360 + 360 * ilvl))
        ind.set(qn("w:hanging"), "360")
        pPr.append(ind)
        rPr = OxmlElement("w:rPr")
        if not ordered:
            rFonts = OxmlElement("w:rFonts")
            rFonts.set(qn("w:ascii"), BULLET_CHARS[ilvl][1])
            rFonts.set(qn("w:hAnsi"), BULLET_CHARS[ilvl][1])
            rFonts.set(qn("w:hint"), "default")
            rPr.append(rFonts)
        for el in (start, fmt, text, jc, pPr, rPr):
            lvl.append(el)
        abstract.append(lvl)

    existing = numbering.findall(qn("w:abstractNum"))
    if existing:
        existing[-1].addnext(abstract)
    else:
        numbering.insert(0, abstract)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    ref = OxmlElement("w:abstractNumId")
    ref.set(qn("w:val"), str(abstract_id))
    num.append(ref)
    numbering.append(num)
    return num_id


def _set_numpr(paragraph, num_id, ilvl):
    pPr = paragraph._p.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    ilvl_el = OxmlElement("w:ilvl"); ilvl_el.set(qn("w:val"), str(ilvl))
    num_el = OxmlElement("w:numId"); num_el.set(qn("w:val"), str(num_id))
    numPr.append(ilvl_el)
    numPr.append(num_el)
    pPr.append(numPr)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), str(360 + 360 * ilvl))
    ind.set(qn("w:hanging"), "360")
    pPr.append(ind)


# --------------------------------------------------------------------------- #
# Header / footer (running, on body pages)
# --------------------------------------------------------------------------- #
def _build_header_footer(section, meta):
    classification = meta["classification"]
    dual = meta["_dual_banner"]
    title = meta.get("title", "")
    doc_id = meta.get("doc_id", "")
    status = brand.status_label(meta.get("status"), meta.get("version"))

    header = section.header
    header.is_linked_to_previous = False
    htbl = header.add_table(rows=1, cols=2, width=Twips(CONTENT_W))
    htbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    htbl.columns[0].width = Twips(int(CONTENT_W * 0.45))
    htbl.columns[1].width = Twips(int(CONTENT_W * 0.55))
    lcell, rcell = htbl.rows[0].cells
    logo = brand.logo_path("full_color")
    if logo.exists():
        pic = lcell.paragraphs[0].add_run().add_picture(str(logo),
                                                        width=Inches(1.7))
        pic._inline.docPr.set("descr", f"{brand.COMPANY} logo")
    rp = rcell.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _runs(rp, title.upper(), font=brand.FONT_HEADLINE, size=8, color="gray",
          caps=True, spacing=12)
    sub_bits = [b for b in (doc_id, status) if b]
    if sub_bits:
        sp = rcell.add_paragraph()
        sp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _runs(sp, "  ·  ".join(sub_bits), font=brand.FONT_BODY, size=7,
              color="gray_light")
    if dual:
        cp = header.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _runs(cp, classification.upper(), font=brand.FONT_BODY, size=7.5,
              color="red", bold=True, spacing=28)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.paragraph_format.tab_stops.add_tab_stop(Twips(CONTENT_W // 2),
                                               WD_TAB_ALIGNMENT.CENTER)
    fp.paragraph_format.tab_stops.add_tab_stop(Twips(CONTENT_W),
                                               WD_TAB_ALIGNMENT.RIGHT)
    _runs(fp, classification.upper(), font=brand.FONT_BODY, size=7,
          color="red", bold=True, spacing=16)
    fp.add_run("\t")
    center = classification.upper() if dual else (doc_id or title)
    _runs(fp, center, font=brand.FONT_BODY, size=7,
          color="red" if dual else "gray", bold=dual,
          spacing=28 if dual else None)
    fp.add_run("\t")
    prun = _runs(fp, "", font=brand.FONT_BODY, size=7, color="gray")
    _add_field(prun, "PAGE", "1")
    _runs(fp, " of ", font=brand.FONT_BODY, size=7, color="gray")
    prun2 = _runs(fp, "", font=brand.FONT_BODY, size=7, color="gray")
    _add_field(prun2, "NUMPAGES", "1")
    if brand.is_draft(meta.get("status")):
        dp = footer.add_paragraph()
        dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _runs(dp, brand.status_label(meta["status"], meta.get("version")),
              font=brand.FONT_BODY, size=6.5, color="gray_light", spacing=20)


# --------------------------------------------------------------------------- #
# Cover page
# --------------------------------------------------------------------------- #
def _build_cover(doc, meta):
    classification = meta["classification"]
    dual = meta["_dual_banner"]
    # Landscape pages are 2.5in shorter; tighten the cover so it stays on one page.
    k = 0.5 if meta["_landscape"] else 1.0

    if dual:
        top = doc.add_paragraph()
        top.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _runs(top, classification.upper(), font=brand.FONT_BODY, size=9,
              color="red", bold=True, spacing=40)
        _para_border(top, ["bottom"], brand.RED, 16, 4)

    band = doc.add_table(rows=1, cols=1)
    band.alignment = WD_TABLE_ALIGNMENT.CENTER
    bcell = band.rows[0].cells[0]
    _cell_shading(bcell, brand.RED)
    bcell.width = Twips(CONTENT_W)
    bp = bcell.paragraphs[0]
    bp.paragraph_format.space_before = Pt(28 * k)
    bp.paragraph_format.space_after = Pt(28 * k)
    white_logo = brand.logo_path("reverse_white")
    if white_logo.exists():
        pic = bp.add_run().add_picture(str(white_logo),
                                       width=Inches(3.2 if k == 1 else 2.3))
        pic._inline.docPr.set("descr", f"{brand.COMPANY} logo")
    if meta.get("doc_type"):
        dp = bcell.add_paragraph()
        dp.paragraph_format.space_before = Pt(6)
        dp.paragraph_format.space_after = Pt(10)
        _runs(dp, str(meta["doc_type"]).upper(), font=brand.FONT_HEADLINE,
              size=12, color="white", caps=True, spacing=28)

    doc.add_paragraph().paragraph_format.space_after = Pt(24 * k)
    tp = doc.add_paragraph()
    tp.paragraph_format.space_after = Pt(2)
    _runs(tp, meta.get("title", "Untitled Document"),
          font=brand.FONT_HEADLINE, size=30, color="ink", bold=True)
    if meta.get("subtitle"):
        sp = doc.add_paragraph()
        _runs(sp, meta["subtitle"], font=brand.FONT_HEADLINE, size=16,
              color="gray")
    rule = doc.add_paragraph()
    rule.paragraph_format.space_before = Pt(8)
    rule.paragraph_format.space_after = Pt(4)
    _para_border(rule, ["bottom"], brand.RED, 24)

    status = brand.status_label(meta.get("status"), meta.get("version"))
    if status:
        stp = doc.add_paragraph()
        stp.paragraph_format.space_before = Pt(6)
        stp.paragraph_format.space_after = Pt(6)
        _runs(stp, status, font=brand.FONT_HEADLINE, size=10,
              color="red" if brand.is_draft(meta.get("status")) else "gray",
              bold=True, caps=True, spacing=24)

    rows = brand.cover_rows(meta)
    if rows:
        gap = doc.add_paragraph()
        gap.paragraph_format.space_before = Pt(10)
        meta_tbl = doc.add_table(rows=len(rows), cols=2)
        meta_tbl.columns[0].width = Twips(2200)
        meta_tbl.columns[1].width = Twips(CONTENT_W - 2200)
        for i, (label, v) in enumerate(rows):
            kc, vc = meta_tbl.rows[i].cells
            kc.width = Twips(2200)
            vc.width = Twips(CONTENT_W - 2200)
            _runs(kc.paragraphs[0], label.upper(), font=brand.FONT_HEADLINE,
                  size=8.5, color="gray", caps=True, spacing=12)
            _runs(vc.paragraphs[0], v, font=brand.FONT_BODY, size=10.5,
                  color="ink")
            if k < 1:
                for c in (kc, vc):
                    c.paragraphs[0].paragraph_format.space_after = Pt(1)

    doc.add_paragraph().paragraph_format.space_after = Pt(30 * k)
    cb = doc.add_table(rows=1, cols=1)
    cb.alignment = WD_TABLE_ALIGNMENT.CENTER
    ccell = cb.rows[0].cells[0]
    _cell_shading(ccell, brand.INK)
    ccell.width = Twips(CONTENT_W)
    cp = ccell.paragraphs[0]
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(6)
    cp.paragraph_format.space_after = Pt(6)
    _runs(cp, f"{classification}   |   {brand.COMPANY}",
          font=brand.FONT_BODY, size=9, color="white", bold=True, caps=True,
          spacing=36)
    # A near-zero-height paragraph carries the break, so it never spills a
    # blank page when the cover fills the sheet.
    brk = doc.add_paragraph()
    brk.paragraph_format.space_before = Pt(0)
    brk.paragraph_format.space_after = Pt(0)
    brk.paragraph_format.line_spacing = Pt(1)
    run = brk.add_run()
    run.font.size = Pt(1)
    run.add_break(WD_BREAK.PAGE)


def _build_title_block(doc, meta):
    """Brief layout: compact title block on page 1 instead of a cover."""
    if meta.get("doc_type"):
        dp = doc.add_paragraph()
        dp.paragraph_format.space_after = Pt(2)
        _runs(dp, str(meta["doc_type"]).upper(), font=brand.FONT_HEADLINE,
              size=9.5, color="red", bold=True, caps=True, spacing=24)
    tp = doc.add_paragraph()
    tp.paragraph_format.space_after = Pt(2)
    _runs(tp, meta.get("title", "Untitled Document"),
          font=brand.FONT_HEADLINE, size=24, color="ink", bold=True)
    if meta.get("subtitle"):
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        _runs(sp, meta["subtitle"], font=brand.FONT_HEADLINE, size=13,
              color="gray")
    line = [str(b) for b in (meta.get("doc_id"), meta.get("author"),
                             meta.get("date"), meta.get("department")) if b]
    if line:
        mp = doc.add_paragraph()
        mp.paragraph_format.space_after = Pt(2)
        _runs(mp, "   |   ".join(line), size=8.5, color="gray")
    status = brand.status_label(meta.get("status"), meta.get("version"))
    if status:
        stp = doc.add_paragraph()
        stp.paragraph_format.space_after = Pt(2)
        _runs(stp, status, font=brand.FONT_HEADLINE, size=9,
              color="red" if brand.is_draft(meta.get("status")) else "gray",
              bold=True, caps=True, spacing=20)
    rule = doc.add_paragraph()
    rule.paragraph_format.space_after = Pt(10)
    _para_border(rule, ["bottom"], brand.RED, 24)


def _build_memo_block(doc, meta):
    """Memo layout: MEMORANDUM label and the To / From / CC / Date / Subject block."""
    lp = doc.add_paragraph()
    lp.paragraph_format.space_after = Pt(8)
    _runs(lp, str(meta.get("doc_type") or "Memorandum").upper(),
          font=brand.FONT_HEADLINE, size=26, color="red", bold=True, caps=True,
          spacing=20)
    rows = [("To", meta.get("to")), ("From", meta.get("from")),
            ("CC", meta.get("cc")), ("Date", meta.get("date")),
            ("Subject", meta.get("subject"))]
    rows = [(k, v) for k, v in rows if v]
    if rows:
        tbl = doc.add_table(rows=len(rows), cols=2)
        tbl.autofit = False
        widths = (1300, CONTENT_W - 1300)
        tbl.columns[0].width = Twips(widths[0])
        tbl.columns[1].width = Twips(widths[1])
        for i, (k, v) in enumerate(rows):
            kc, vc = tbl.rows[i].cells
            kc.width, vc.width = Twips(widths[0]), Twips(widths[1])
            kc.paragraphs[0].paragraph_format.space_after = Pt(3)
            vc.paragraphs[0].paragraph_format.space_after = Pt(3)
            _runs(kc.paragraphs[0], k.upper(), font=brand.FONT_HEADLINE,
                  size=9, color="gray", caps=True, spacing=16)
            if isinstance(v, (list, tuple)):
                v = ", ".join(str(x) for x in v)
            _runs(vc.paragraphs[0], str(v), size=10.5, color="ink",
                  bold=(k == "Subject"))
    rule = doc.add_paragraph()
    rule.paragraph_format.space_before = Pt(4)
    rule.paragraph_format.space_after = Pt(12)
    _para_border(rule, ["bottom"], brand.RED, 24)


def _add_toc(doc, page_break=True):
    head = doc.add_paragraph(style="Heading 1")
    _runs(head, "Contents", font=brand.FONT_HEADLINE, size=19, color="red",
          bold=True)
    p = doc.add_paragraph()
    run = _runs(p, "", size=10.5)
    _add_field(run, 'TOC \\o "1-3" \\h \\z \\u',
               "Right-click and choose Update Field to build the table of "
               "contents.")
    if page_break:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# --------------------------------------------------------------------------- #
# Block rendering
# --------------------------------------------------------------------------- #
def _add_inlines(paragraph, inlines, size=10.5, color="ink", base_bold=False,
                 font=brand.FONT_BODY):
    for r in inlines:
        if r["href"]:
            _hyperlink(paragraph, r["href"], r["text"], size=size)
        elif r["code"]:
            run = _runs(paragraph, r["text"], font=brand.FONT_MONO,
                        size=size - 1, color="ink",
                        bold=r["bold"] or base_bold, italic=r["italic"])
            _set_shading(run._r.get_or_add_rPr(), brand.CODE_BG)
        else:
            _runs(paragraph, r["text"], font=font, size=size, color=color,
                  bold=r["bold"] or base_bold, italic=r["italic"])


def _add_code(doc, block, report):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Twips(CONTENT_W)
    _cell_shading(cell, brand.CODE_BG)
    _cell_margins(cell, 90, 160, 90, 160)
    lines = block["text"].split("\n") or [""]
    first = cell.paragraphs[0]
    for idx, line in enumerate(lines):
        p = first if idx == 0 else cell.add_paragraph()
        p.style = doc.styles["SOS Code"]
        _runs(p, line or " ", font=brand.FONT_MONO, size=8.5, color="ink")
    if len(lines) <= 25:
        _cant_split(tbl.rows[0])
    _table_borders(tbl, brand.RULE, left_accent=brand.RED)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    report.count("code blocks")


def col_weight(header, rows, j):
    """Relative width for column j. Headers wrap at spaces, so only their
    longest word must fit; text-heavy columns grow with their average length."""
    words = M.plain_text(header[j]).split() or [""]
    head = max(len(w) for w in words)
    cells = [len(M.plain_text(r[j])) for r in rows if j < len(r)]
    longest = max(cells) if cells else 0
    avg = sum(cells) / len(cells) if cells else 0
    return max(head * 1.1, min(longest, 24) * 0.6 + avg * 0.7) + 3


def col_widths(header, rows, total, min_w=900):
    """Column widths proportional to content, so a Role | Responsibility table
    does not split 50/50. Short columns get what they need; long text columns
    share the rest."""
    weights = [col_weight(header, rows, j) for j in range(len(header))]
    total_w = sum(weights) or 1
    widths = [max(min_w, int(total * w / total_w)) for w in weights]
    scale = total / sum(widths)
    return [int(w * scale) for w in widths]


def _add_table(doc, block, report):
    header, rows, align = block["header"], block["rows"], block["align"]
    ncols = len(header)
    tbl = doc.add_table(rows=1 + len(rows), cols=ncols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    widths = col_widths(header, rows, CONTENT_W)
    for c, w in zip(tbl.columns, widths):
        c.width = Twips(w)
    for j, cell_inlines in enumerate(header):
        cell = tbl.rows[0].cells[j]
        _cell_shading(cell, brand.RED)
        cell.width = Twips(widths[j])
        p = cell.paragraphs[0]
        p.alignment = ALIGN.get(align[j], WD_ALIGN_PARAGRAPH.LEFT)
        _runs(p, M.plain_text(cell_inlines).upper(),
              font=brand.FONT_HEADLINE, size=8.5, color="white", caps=True,
              spacing=6)
    _repeat_header(tbl.rows[0])
    for i, row in enumerate(rows):
        for j, cell_inlines in enumerate(row):
            cell = tbl.rows[i + 1].cells[j]
            cell.width = Twips(widths[j])
            if i % 2 == 1:
                _cell_shading(cell, brand.BAND_EVEN)
            p = cell.paragraphs[0]
            p.alignment = ALIGN.get(align[j], WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.space_after = Pt(2)
            _add_inlines(p, cell_inlines, size=9.5)
    _table_borders(tbl, brand.RULE)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    report.count("tables")


def _cant_split(row):
    """Keep a row on one page (callouts, short code blocks)."""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _table_borders(tbl, hex_color, left_accent=None):
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        if edge == "left" and left_accent:
            el.set(qn("w:sz"), "18")
            el.set(qn("w:color"), left_accent.lstrip("#"))
        else:
            el.set(qn("w:sz"), "4")
            el.set(qn("w:color"), hex_color.lstrip("#"))
        el.set(qn("w:space"), "0")
        borders.append(el)
    tblPr.append(borders)


def _add_image(doc, block, report):
    path = block["path"]
    w_in, _ = media.fit(path, CONTENT_W / 1440.0, CONTENT_H / 1440.0 * 0.8,
                        block.get("width"))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = bool(block.get("alt"))
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2 if block.get("alt") else 10)
    shape = p.add_run().add_picture(path, width=Inches(w_in))
    # Alt text for screen readers and Word's accessibility checker.
    shape._inline.docPr.set("descr", block.get("alt") or
                            ("Diagram" if block.get("diagram") else "Image"))
    if block.get("alt"):
        cp = doc.add_paragraph(style="SOS Caption")
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _runs(cp, block["alt"], size=8.5, color="gray", italic=True)


def _add_callout(doc, block, report):
    label, accent, tint = brand.CALLOUTS[block["kind"]]
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Twips(CONTENT_W)
    _cell_shading(cell, brand.HEX[tint])
    _cell_margins(cell, 110, 200, 90, 200)
    tp = cell.paragraphs[0]
    tp.paragraph_format.space_before = Pt(2)
    tp.paragraph_format.space_after = Pt(2)
    _runs(tp, (block.get("title") or label).upper(), font=brand.FONT_HEADLINE,
          size=9, color=accent, bold=True, caps=True, spacing=16)
    _render_into_cell(cell, block["blocks"], report)
    _cant_split(tbl.rows[0])
    _callout_borders(tbl, brand.HEX[accent], brand.HEX[tint])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    report.count("callouts")


def _callout_borders(tbl, accent, tint):
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "24" if edge == "left" else "4")
        el.set(qn("w:color"), (accent if edge == "left" else tint).lstrip("#"))
        el.set(qn("w:space"), "0")
        borders.append(el)
    tblPr.append(borders)


def _render_into_cell(cell, blocks, report, depth=0):
    """Callout bodies: paragraphs, lists, and code inside one table cell."""
    for b in blocks:
        t = b["type"]
        if t == "para":
            p = cell.add_paragraph()
            p.paragraph_format.space_after = Pt(3)
            if depth:
                p.paragraph_format.left_indent = Twips(280 * depth)
            _add_inlines(p, b["inlines"], size=10)
        elif t == "list":
            for n, item in enumerate(b["items"], start=1):
                marker = f"{n}." if b["ordered"] else "•"
                head, rest = None, list(item)
                if rest and rest[0]["type"] == "para":
                    head = rest.pop(0)
                p = cell.add_paragraph()
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.left_indent = Twips(280 * (depth + 1))
                p.paragraph_format.first_line_indent = Twips(-220)
                _runs(p, marker + " ", size=10)
                if head:
                    _add_inlines(p, head["inlines"], size=10)
                _render_into_cell(cell, rest, report, depth + 1)
        elif t == "code":
            for line in b["text"].split("\n"):
                p = cell.add_paragraph(style="SOS Code")
                _runs(p, line or " ", font=brand.FONT_MONO, size=8.5)
        elif t == "heading":
            p = cell.add_paragraph()
            _add_inlines(p, b["inlines"], size=10, base_bold=True)
        else:
            report.warn(f"a {t} inside a callout was rendered as text")
            p = cell.add_paragraph()
            _runs(p, M.plain_text(b.get("inlines", [])) or f"[{t}]", size=10)


def _render_blocks(doc, blocks, report, num_id=None, ilvl=0):
    for block in blocks:
        t = block["type"]
        if t == "heading":
            level = min(block["level"], 4)
            if block["level"] > 4:
                report.warn(f"H{block['level']} rendered as Heading 4 "
                            f"(Word styles stop at 4): "
                            f"{M.plain_text(block['inlines'])[:50]}")
            p = doc.add_paragraph(style=f"Heading {level}")
            _add_inlines(p, block["inlines"],
                         size=HEADING_SPEC[level][1],
                         color=HEADING_SPEC[level][2],
                         base_bold=HEADING_SPEC[level][3],
                         font=HEADING_SPEC[level][0])
            report.count(f"H{level}")
        elif t == "para":
            p = doc.add_paragraph()
            _add_inlines(p, block["inlines"])
            report.count("paragraphs")
        elif t == "list":
            list_num = new_list_num(doc, block["ordered"])
            for item in block["items"]:
                _render_item(doc, item, report, list_num, ilvl,
                             block["ordered"])
            report.count("lists")
        elif t == "code":
            _add_code(doc, block, report)
        elif t == "quote":
            for inner in block["blocks"]:
                if inner["type"] == "para":
                    p = doc.add_paragraph(style="SOS Quote")
                    _add_inlines(p, inner["inlines"], color="gray")
                else:
                    _render_blocks(doc, [inner], report)
            report.count("blockquotes")
        elif t == "table":
            _add_table(doc, block, report)
        elif t == "hr":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(10)
            _para_border(p, ["bottom"], brand.RULE, 8)
        elif t == "image":
            _add_image(doc, block, report)
        elif t == "callout":
            _add_callout(doc, block, report)
        elif t == "pagebreak":
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            report.count("page breaks")
        else:
            report.skipped(f"unsupported block '{t}'")


def _render_item(doc, item_blocks, report, num_id, ilvl, ordered):
    """First para carries the marker; nested content follows at ilvl + 1."""
    head, rest = None, list(item_blocks)
    if rest and rest[0]["type"] == "para":
        head = rest.pop(0)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    _set_numpr(p, num_id, min(ilvl, 2))
    if head:
        _add_inlines(p, head["inlines"])
    for block in rest:
        if block["type"] == "list":
            nested = new_list_num(doc, block["ordered"])
            for sub in block["items"]:
                _render_item(doc, sub, report, nested, ilvl + 1,
                             block["ordered"])
        elif block["type"] == "para":
            q = doc.add_paragraph()
            q.paragraph_format.left_indent = Twips(360 * (ilvl + 1))
            q.paragraph_format.space_after = Pt(3)
            _add_inlines(q, block["inlines"])
        else:
            _render_blocks(doc, [block], report, ilvl=ilvl + 1)


# --------------------------------------------------------------------------- #
# Document Control
# --------------------------------------------------------------------------- #
def _render_document_control(doc, meta, report):
    vh = meta.get("version_history") or []
    ap = meta.get("approvals") or []
    if not vh and not ap:
        return
    p = doc.add_paragraph(style="Heading 1")
    _add_inlines(p, [M.run("Document Control")], size=19, color="red",
                 base_bold=True, font=brand.FONT_HEADLINE)
    if vh:
        h = doc.add_paragraph(style="Heading 3")
        _add_inlines(h, [M.run("Version History")], size=11.5,
                     color="red_dark", base_bold=True, font=brand.FONT_HEADLINE)
        _add_table(doc, _plain_table(
            ["Version", "Date", "Author", "Description", "Approved By"],
            [[e.get("version", ""), e.get("date", ""), e.get("author", ""),
              e.get("description", ""), e.get("approved", "")] for e in vh]),
            report)
    if ap:
        h = doc.add_paragraph(style="Heading 3")
        _add_inlines(h, [M.run("Approvals")], size=11.5, color="red_dark",
                     base_bold=True, font=brand.FONT_HEADLINE)
        _add_table(doc, _plain_table(
            ["Name", "Role", "Date"],
            [[e.get("name", ""), e.get("role", ""), e.get("date", "")]
             for e in ap]), report)


def _plain_table(header, rows):
    return {"type": "table",
            "header": [[M.run(h)] for h in header],
            "rows": [[[M.run(str(c))] for c in row] for row in rows],
            "align": ["left"] * len(header)}


# --------------------------------------------------------------------------- #
# Core properties
# --------------------------------------------------------------------------- #
def _set_core_properties(doc, meta):
    props = brand.properties(meta)
    cp = doc.core_properties
    cp.title = props["title"]
    cp.subject = props["subject"]
    cp.author = props["author"]
    cp.last_modified_by = props["author"]
    cp.category = props["category"]
    cp.keywords = props["keywords"]
    cp.comments = props["comments"]
    if meta.get("version"):
        try:
            cp.revision = max(1, int(float(str(meta["version"]))))
        except (TypeError, ValueError):
            pass


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    global PAGE_W, PAGE_H, CONTENT_W, CONTENT_H
    parser = argparse.ArgumentParser(
        description="SoundOff Signal branded Word builder")
    brand.add_common_args(parser, paged=True)
    args = parser.parse_args()

    report = brand.BuildReport("docx", strict=args.strict)
    with open(args.content, encoding="utf-8") as f:
        raw = f.read()
    front, body_md = M.split_front_matter(raw)
    meta = brand.resolve_meta(front, args, report)
    output = brand.resolve_output(args.output, meta, "docx")

    blocks, warnings = M.parse_with_warnings(body_md)
    for w in warnings:
        report.warn(w)
    blocks, n_notes = M.strip_notes(blocks)
    if n_notes:
        report.info(f"{n_notes} speaker-notes section(s) (???) left out; "
                    "they appear only in decks")
    blocks = media.prepare(blocks, media.base_dir_of(args.content), report,
                           "docx")

    if meta["_landscape"]:
        PAGE_W, PAGE_H = PAGE_H, PAGE_W
        CONTENT_W, CONTENT_H = PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN

    doc = Document()
    _define_styles(doc)

    sec = doc.sections[0]
    sec.orientation = (WD_ORIENT.LANDSCAPE if meta["_landscape"]
                       else WD_ORIENT.PORTRAIT)
    sec.page_width = Twips(PAGE_W)
    sec.page_height = Twips(PAGE_H)
    sec.left_margin = Twips(MARGIN)
    sec.right_margin = Twips(MARGIN)
    sec.top_margin = Twips(1080)
    sec.bottom_margin = Twips(1080)
    layout = meta["_layout"]
    # With a cover, page 1 stays clean; the running marks start on body pages.
    sec.different_first_page_header_footer = layout == "report"

    _build_header_footer(sec, meta)
    if layout == "report":
        _build_cover(doc, meta)
    elif layout == "memo":
        _build_memo_block(doc, meta)
    else:
        _build_title_block(doc, meta)
    if meta["_toc"]:
        _add_toc(doc, page_break=layout == "report")
    _render_document_control(doc, meta, report)
    _render_blocks(doc, blocks, report)
    _set_core_properties(doc, meta)

    doc.save(output)
    report.finish(output, empty=M.is_empty(blocks))


if __name__ == "__main__":
    main()
