#!/usr/bin/env python3
"""
SoundOff Signal branded PowerPoint (.pptx) builder.

Builds decks FROM THE CORPORATE TEMPLATE bundled at
assets/templates/soundoff-deck-template.pptx. All slide design (red title and
divider slides with the signal-bar motif, content slide title treatment, logo
placement, fonts) comes from the template's slide layouts. This builder fills
placeholders and adds branded tables, images, diagrams, speaker notes, and the
classification marking (which the corporate template does not carry).

Layouts used: Title Slide [0], Divider Slide [1], Content Slide - Bullets [3],
Ending Slide [7].

Slide mapping (Markdown is parsed by the shared md_blocks.py):

    (front matter)          -> title slide
    # Section               -> divider slide, then a content slide for anything
                               that follows before the next heading
    ## Slide Title          -> content slide (bullets layout)
    ### Subhead             -> red subhead paragraph within the slide body
    - / 1. lists            -> bulleted or numbered list, nested by indent
    | md table |            -> branded table (red header, banding, fitted columns)
    ![alt](image.png)       -> picture scaled into the space left on the slide
    ```mermaid              -> branded diagram, placed like an image
    > [!NOTE] callout       -> labeled callout paragraph
    fenced code / > quote   -> monospace block / italic gray callout
    ???                     -> everything after it on that slide = speaker notes
    <!-- pagebreak -->      -> continue on a new slide with the same title
    === SECTION: Text       -> divider slide
    === CLOSING[: Text]     -> ending slide

Nothing is dropped silently: anything the deck cannot represent is reported on
stderr and counted in the build summary. --strict turns warnings into errors.

Usage:
    python build_pptx.py --content deck.md --output out.pptx [--strict]
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brand  # noqa: E402

brand.require("yaml", "pptx")

from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

import md_blocks as M  # noqa: E402
import media  # noqa: E402

C = lambda name: RGBColor(*brand.RGB[name])  # noqa: E731

TEMPLATE = brand.TEMPLATES_DIR / "soundoff-deck-template.pptx"
LAY_TITLE, LAY_DIVIDER, LAY_CONTENT, LAY_ENDING = 0, 1, 3, 7

# Content-slide body geometry from the template layout (inches).
BODY_LEFT, BODY_TOP, BODY_W, BODY_H = 1.04, 2.83, 13.03, 4.50
LEADIN_TOP = 2.25
BODY_BOTTOM = BODY_TOP + BODY_H

ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER,
         "right": PP_ALIGN.RIGHT}


# --------------------------------------------------------------------------- #
# Placeholder / run helpers
# --------------------------------------------------------------------------- #
def _clear_slides(prs):
    for i in range(len(prs.slides) - 1, -1, -1):
        rId = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[i]


def _ph(slide, idx):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def _drop_ph(slide, idx):
    ph = _ph(slide, idx)
    if ph is not None:
        ph._element.getparent().remove(ph._element)


def _set_runs(p, text, *, size=None, bold=None, italic=None, color=None,
              font=None, spacing=None, href=None):
    run = p.add_run()
    run.text = text
    if font:
        run.font.name = font
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color:
        run.font.color.rgb = C(color)
    if spacing is not None:
        rPr = run._r.get_or_add_rPr()
        rPr.set("spc", str(int(spacing * 100)))
    if href:
        run.hyperlink.address = href
    return run


def _add_inlines(p, inlines, *, size=14, color="ink"):
    for r in inlines:
        _set_runs(p, r["text"], size=size,
                  bold=r["bold"] or None, italic=r["italic"] or None,
                  color="red" if r["href"] else color,
                  font=brand.FONT_MONO_FALLBACK if r["code"] else None,
                  href=r["href"])


def _no_bullet(p):
    pPr = p._p.get_or_add_pPr()
    pPr.append(pPr.makeelement(qn("a:buNone"), {}))


def _bullet(p, depth=0):
    # PowerPoint tracks list position by the paragraph's own level, so depth has
    # to be set on lvl as well as marL: otherwise a nested list resets the
    # numbering of the ordered list it sits inside.
    p.level = min(depth, 4)
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.28 + 0.30 * depth)))
    pPr.set("indent", str(-Inches(0.22)))
    chars = ["•", "◦", "–"]
    pPr.append(pPr.makeelement(qn("a:buChar"),
                               {"char": chars[min(depth, 2)]}))


def _autonum(p, depth=0):
    p.level = min(depth, 4)
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.34 + 0.30 * depth)))
    pPr.set("indent", str(-Inches(0.28)))
    kinds = ["arabicPeriod", "alphaLcPeriod", "romanLcPeriod"]
    pPr.append(pPr.makeelement(qn("a:buAutoNum"),
                               {"type": kinds[min(depth, 2)]}))


def _marking(slide, meta, *, on_red):
    classification = meta["classification"]
    dual = meta["_dual_banner"]
    color = "white" if on_red else "red"
    if on_red:
        box = slide.shapes.add_textbox(Inches(BODY_LEFT), Inches(8.16),
                                       Inches(BODY_W), Inches(0.28))
        align = PP_ALIGN.CENTER
    else:
        box = slide.shapes.add_textbox(Inches(BODY_LEFT), Inches(8.08),
                                       Inches(6.5), Inches(0.3))
        align = PP_ALIGN.LEFT
    tf = box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    _set_runs(p, classification.upper(), font=brand.FONT_BODY, size=8,
              bold=True, color=color, spacing=1.2)
    if meta.get("doc_id") and not on_red:
        _set_runs(p, f"   ·   {meta['doc_id']}", font=brand.FONT_BODY, size=8,
                  color="gray_light")
    if dual:
        top = slide.shapes.add_textbox(Inches(BODY_LEFT), Inches(0.06),
                                       Inches(BODY_W), Inches(0.28))
        tf = top.text_frame
        tf.margin_left = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _set_runs(p, classification.upper(), font=brand.FONT_BODY, size=8.5,
                  bold=True, color=color, spacing=2.4)


# --------------------------------------------------------------------------- #
# Slide builders
# --------------------------------------------------------------------------- #
def title_slide(prs, meta):
    s = prs.slides.add_slide(prs.slide_layouts[LAY_TITLE])
    _ph(s, 0).text_frame.text = str(meta.get("title", "Untitled"))
    info = _ph(s, 10)
    bits = [str(meta.get("date", ""))]
    if meta.get("author"):
        bits.append(str(meta["author"]))
    if meta.get("version"):
        bits.append(f"v{meta['version']}")
    if meta.get("status"):
        # Short form only: the template's info placeholder is a single line.
        bits.append(str(meta["status"]).upper())
    if info is not None:
        info.text_frame.text = "  |  ".join(b for b in bits if b)
        for p in info.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(11)
    if meta.get("subtitle"):
        tf = _ph(s, 0).text_frame
        p = tf.add_paragraph()
        _set_runs(p, str(meta["subtitle"]), size=18)
    _marking(s, meta, on_red=True)
    return s


def section_slide(prs, meta, text):
    s = prs.slides.add_slide(prs.slide_layouts[LAY_DIVIDER])
    _ph(s, 0).text_frame.text = text
    _marking(s, meta, on_red=True)
    return s


def closing_slide(prs, meta, text=None):
    s = prs.slides.add_slide(prs.slide_layouts[LAY_ENDING])
    _ph(s, 0).text_frame.text = text or "Thank You!"
    info = _ph(s, 10)
    if info is not None:
        info.text_frame.text = brand.SITE_URL
        for p in info.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(12)
    _marking(s, meta, on_red=True)
    return s


def _est_lines(text, width_in, pt):
    if not text:
        return 1
    chars_per_line = max(int(width_in * 144 / pt), 1)
    return max(1, -(-len(text) // chars_per_line))


def _notes(slide, blocks):
    """Speaker notes from the blocks after a ??? line."""
    lines = []
    for b, depth in M.walk(blocks):
        if b["type"] in ("para", "heading"):
            lines.append(("  " * depth) + M.plain_text(b["inlines"]))
        elif b["type"] == "code":
            lines.append(b["text"])
    if lines:
        slide.notes_slide.notes_text_frame.text = "\n".join(lines)


def content_slide(prs, meta, title, blocks, report, notes=None):
    s = prs.slides.add_slide(prs.slide_layouts[LAY_CONTENT])
    _ph(s, 0).text_frame.text = title
    if notes:
        _notes(s, notes)
        report.count("slides with notes")

    blocks = list(blocks)
    # A short opening paragraph fills the template's red lead-in line; longer
    # intros flow into the body rather than overflowing the fixed layout box.
    lead = None
    if blocks and blocks[0]["type"] == "para":
        text = M.plain_text(blocks[0]["inlines"])
        if len(text) <= 105:
            lead = blocks.pop(0)
    if lead is not None:
        ph = _ph(s, 12)
        ph.text_frame.text = M.plain_text(lead["inlines"])
        for p in ph.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(14)
    else:
        _drop_ph(s, 12)

    visual = ("table", "image")
    text_blocks = [b for b in blocks if b["type"] not in visual]
    visuals = [b for b in blocks if b["type"] in visual]

    used_in = 0.0
    if text_blocks:
        body = _ph(s, 13)
        tf = body.text_frame
        tf.word_wrap = True
        state = {"first": True}

        def para():
            p = tf.paragraphs[0] if state["first"] else tf.add_paragraph()
            state["first"] = False
            return p

        used_in = _fill_body(para, text_blocks, report)
    else:
        _drop_ph(s, 13)

    # With no lead-in and no body text, visuals can use the lead-in line too.
    top = BODY_TOP if (lead is not None or text_blocks) else LEADIN_TOP
    y = top + used_in + (0.25 if text_blocks else 0.0)
    n_images = sum(1 for b in visuals if b["type"] == "image")
    if not text_blocks and len(visuals) == 1 and n_images == 1:
        # A slide that is just a picture: center it in the body area.
        b = visuals[0]
        room = BODY_BOTTOM + 0.3 - y
        _, h_in = media.fit(b["path"], BODY_W, room, b.get("width"))
        if h_in:
            y += max(0.0, (room - h_in - (0.3 if b.get("alt") else 0)) / 2)
    for block in visuals:
        if block["type"] == "table":
            y = _table(s, Inches(BODY_LEFT), Inches(y), Inches(BODY_W), block)
            y += 0.3
            report.count("tables")
        else:
            room = BODY_BOTTOM + 0.3 - y
            share = room / max(n_images, 1)
            y = _picture(s, block, y, max(share, 1.6), report)
            n_images -= 1
            y += 0.2
    if y > BODY_BOTTOM + 0.35:
        report.warn(f"slide '{title}' runs {y - BODY_BOTTOM:.1f}in past the "
                    "template body area: split it")

    _marking(s, meta, on_red=False)
    report.count("slides")
    return s


def _fill_body(para, blocks, report, depth=0):
    """Render blocks into a content placeholder; return estimated height used."""
    used = 0.0
    for block in blocks:
        t = block["type"]
        if t == "heading":
            p = para()
            _no_bullet(p)
            p.space_before = Pt(10)
            _set_runs(p, M.plain_text(block["inlines"]).upper(),
                      font=brand.FONT_HEADLINE, size=15, bold=True,
                      color="red_dark", spacing=0.6)
            used += 0.38
        elif t == "para":
            p = para()
            _no_bullet(p)
            p.space_after = Pt(8)
            if depth:
                p.level = min(depth, 4)
                p._p.get_or_add_pPr().set("marL", str(Inches(0.3 * depth)))
            _add_inlines(p, block["inlines"], size=14)
            used += _est_lines(M.plain_text(block["inlines"]), BODY_W,
                               14) * 0.27 + 0.10
        elif t == "list":
            for item in block["items"]:
                head, rest = None, list(item)
                if rest and rest[0]["type"] == "para":
                    head = rest.pop(0)
                p = para()
                if block["ordered"]:
                    _autonum(p, depth)
                else:
                    _bullet(p, depth)
                p.space_after = Pt(6)
                if head:
                    _add_inlines(p, head["inlines"], size=14)
                    used += _est_lines(M.plain_text(head["inlines"]),
                                       BODY_W - 0.3 * (depth + 1), 14) * 0.26 \
                        + 0.08
                if rest:
                    used += _fill_body(para, rest, report, depth + 1)
        elif t == "code":
            for line in block["text"].split("\n"):
                p = para()
                _no_bullet(p)
                p.space_after = Pt(0)
                p.level = min(depth + 1, 4)
                p._p.get_or_add_pPr().set("marL", str(Inches(0.3 * (depth + 1))))
                _set_runs(p, line or " ", font=brand.FONT_MONO_FALLBACK,
                          size=11, color="ink")
                used += 0.22
            used += 0.12
            report.count("code blocks")
        elif t == "quote":
            for inner in block["blocks"]:
                if inner["type"] == "para":
                    p = para()
                    _no_bullet(p)
                    p.space_after = Pt(8)
                    p._p.get_or_add_pPr().set("marL", str(Inches(0.3)))
                    _add_inlines(p, inner["inlines"], size=13, color="gray")
                    used += _est_lines(M.plain_text(inner["inlines"]),
                                       BODY_W - 0.3, 13) * 0.25 + 0.10
                else:
                    used += _fill_body(para, [inner], report, depth + 1)
            report.count("blockquotes")
        elif t == "callout":
            label, accent, _ = brand.CALLOUTS[block["kind"]]
            first = True
            inner_blocks = block["blocks"] or [
                {"type": "para", "inlines": []}]
            for inner in inner_blocks:
                if inner["type"] == "para":
                    p = para()
                    _no_bullet(p)
                    p.space_after = Pt(8)
                    if first:
                        _set_runs(p, (block.get("title") or label).upper()
                                  + "   ", font=brand.FONT_HEADLINE, size=13,
                                  bold=True, color=accent, spacing=1.0)
                        first = False
                    _add_inlines(p, inner["inlines"], size=14)
                    used += _est_lines(M.plain_text(inner["inlines"]),
                                       BODY_W - 1.2, 14) * 0.27 + 0.10
                else:
                    used += _fill_body(para, [inner], report, depth + 1)
            report.count("callouts")
        elif t == "hr":
            p = para()
            _no_bullet(p)
            _set_runs(p, "", size=6)
            used += 0.12
        elif t in ("table", "image"):
            report.warn(f"a {t} inside a list or quote was moved to the end "
                        "of the slide")
        elif t == "pagebreak":
            pass
        else:
            report.skipped(f"unsupported block '{t}' on a slide")
    return used


def _picture(slide, block, y, max_h, report):
    """Place an image centered in the body width, below what is already there."""
    w_in, h_in = media.fit(block["path"], BODY_W, max_h,
                           block.get("width"))
    if h_in is None:
        h_in = max_h
    cap_h = 0.3 if block.get("alt") else 0.0
    if h_in + cap_h > max_h:
        scale = (max_h - cap_h) / h_in
        w_in, h_in = w_in * scale, h_in * scale
    left = BODY_LEFT + (BODY_W - w_in) / 2
    pic = slide.shapes.add_picture(block["path"], Inches(left), Inches(y),
                                   Inches(w_in), Inches(h_in))
    # Alt text for screen readers.
    pic._element.nvPicPr.cNvPr.set("descr", block.get("alt") or
                                   ("Diagram" if block.get("diagram")
                                    else "Image"))
    y += h_in
    if block.get("alt"):
        box = slide.shapes.add_textbox(Inches(BODY_LEFT), Inches(y + 0.03),
                                       Inches(BODY_W), Inches(0.28))
        p = box.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _set_runs(p, block["alt"], size=11, italic=True, color="gray")
        y += cap_h
    return y


def _col_widths(header, rows, total_in, min_in=0.9):
    """Column widths proportional to content (same rule as the Word builder)."""
    weights = []
    for j in range(len(header)):
        words = M.plain_text(header[j]).split() or [""]
        head = max(len(w) for w in words)
        cells = [len(M.plain_text(r[j])) for r in rows if j < len(r)]
        longest = max(cells) if cells else 0
        avg = sum(cells) / len(cells) if cells else 0
        weights.append(max(head * 1.1, min(longest, 24) * 0.6 + avg * 0.7) + 3)
    total_w = sum(weights) or 1
    widths = [max(min_in, total_in * w / total_w) for w in weights]
    scale = total_in / sum(widths)
    return [w * scale for w in widths]


def _natural_width(header, rows, size):
    total = 0.0
    for j in range(len(header)):
        cells = [M.plain_text(r[j]) for r in rows if j < len(r)]
        words = M.plain_text(header[j]).split() or [""]
        longest = max([len(c) for c in cells] + [max(len(w) for w in words)])
        total += min(longest, 40) * size / 110.0 + 0.3
    return total


def _table(slide, left, top, width, block):
    header, rows, align = block["header"], block["rows"], block["align"]
    n_rows, n_cols = 1 + len(rows), len(header)
    # Larger tables step the type down so they stay inside the body area.
    size = 11 if n_rows <= 7 else 10 if n_rows <= 10 else 9
    # Narrow tables do not need the full body width.
    natural = _natural_width(header, rows, size)
    width = Inches(min(max(natural, BODY_W * 0.55), Emu(width).inches))
    widths = _col_widths(header, rows, Emu(width).inches)
    row_h_in = 0.36 if size == 11 else 0.32 if size == 10 else 0.28

    def lines(text, w_in):
        return max(1, -(-len(text) // max(int(w_in * 144 / size * 0.9), 1)))

    est = 0.0
    for r in [header] + rows:
        est += max(lines(M.plain_text(c), w) for c, w in zip(r, widths)) \
            * row_h_in * 0.75 + row_h_in * 0.25
    gtbl = slide.shapes.add_table(n_rows, n_cols, left, top, width,
                                  Inches(row_h_in) * n_rows).table
    gtbl.first_row = False
    gtbl.horz_banding = False
    for j, w in enumerate(widths):
        gtbl.columns[j].width = Inches(w)
    for j, cell_inlines in enumerate(header):
        cell = gtbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C("red")
        _cell_text(cell, [M.run(M.plain_text(cell_inlines).upper())],
                   font=brand.FONT_HEADLINE, size=size, color="white",
                   bold=True, align=align[j])
    for i, row in enumerate(rows):
        for j, cell_inlines in enumerate(row):
            cell = gtbl.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C("band_even") if i % 2 == 1 \
                else C("white")
            _cell_text(cell, cell_inlines, font=brand.FONT_BODY, size=size,
                       color="ink", align=align[j])
    return Emu(top).inches + est


def _cell_text(cell, inlines, *, font, size, color, bold=False, align="left"):
    cell.margin_left = cell.margin_right = Inches(0.1)
    cell.margin_top = cell.margin_bottom = Inches(0.03)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = ALIGN.get(align, PP_ALIGN.LEFT)
    for r in inlines:
        _set_runs(p, r["text"], font=brand.FONT_MONO_FALLBACK if r["code"]
                  else font, size=size, bold=bold or r["bold"] or None,
                  italic=r["italic"] or None,
                  color="red" if r["href"] else color, href=r["href"])


# --------------------------------------------------------------------------- #
# Blocks -> slide plan
# --------------------------------------------------------------------------- #
DIRECTIVE_SECTION = re.compile(r"^===\s*SECTION:\s*(.*)$")
DIRECTIVE_CLOSING = re.compile(r"^===\s*CLOSING:?\s*(.*)$")
NOTES_MARK = M.NOTES_MARK


def plan_slides(blocks, meta, report):
    """Turn the block list into an ordered slide plan of
    (kind, text, body_blocks, note_blocks)."""
    plan = []
    title, buf, notes, in_notes = None, [], [], False

    def flush():
        nonlocal title, buf, notes, in_notes
        if buf or title or notes:
            if title is None:
                title = str(meta.get("title") or "Overview")
                report.warn("content appeared before the first heading; it was "
                            f"placed on a slide titled {title!r}")
            plan.append(("content", title, buf, notes))
        title, buf, notes, in_notes = None, [], [], False

    for block in blocks:
        if block["type"] == "para":
            text = M.plain_text(block["inlines"]).strip()
            if text == NOTES_MARK:
                in_notes = True
                continue
            m = DIRECTIVE_SECTION.match(text)
            if m:
                flush()
                plan.append(("section", m.group(1).strip(), None, None))
                continue
            m = DIRECTIVE_CLOSING.match(text)
            if m:
                flush()
                plan.append(("closing", m.group(1).strip() or None, None,
                             None))
                continue
        if block["type"] == "heading" and block["level"] <= 2:
            text = M.plain_text(block["inlines"]).strip()
            flush()
            if block["level"] == 1:
                plan.append(("section", text, None, None))
            title = text
            continue
        if block["type"] == "pagebreak":
            cont = title
            flush()
            if cont:
                title = cont if cont.endswith("(cont.)") else f"{cont} (cont.)"
            continue
        if in_notes:
            notes.append(block)
            continue
        if block["type"] == "heading":
            if block["level"] >= 5:
                report.warn(f"H{block['level']} "
                            f"'{M.plain_text(block['inlines'])[:40]}' rendered "
                            "as a subhead (slides have one subhead level)")
            buf.append({"type": "heading", "level": 3,
                        "inlines": block["inlines"]})
            continue
        buf.append(block)
    flush()

    # Drop content slides that a divider already fully covers.
    return [p for p in plan
            if not (p[0] == "content" and not p[2] and not p[3])]


def _set_properties(prs, meta):
    props = brand.properties(meta)
    cp = prs.core_properties
    cp.title = props["title"]
    cp.subject = props["subject"]
    cp.author = props["author"]
    cp.last_modified_by = props["author"]
    cp.category = props["category"]
    cp.keywords = props["keywords"]
    cp.comments = props["comments"]


def main():
    parser = argparse.ArgumentParser(
        description="SoundOff Signal branded deck builder")
    brand.add_common_args(parser)
    args = parser.parse_args()

    report = brand.BuildReport("pptx", strict=args.strict)
    with open(args.content, encoding="utf-8") as f:
        raw = f.read()
    front, body_md = M.split_front_matter(raw)
    meta = brand.resolve_meta(front, args, report)
    output = brand.resolve_output(args.output, meta, "pptx")

    blocks, warnings = M.parse_with_warnings(body_md)
    for w in warnings:
        report.warn(w)
    blocks = media.prepare(blocks, media.base_dir_of(args.content), report,
                           "pptx")

    if not TEMPLATE.exists():
        print(f"error: corporate deck template missing: {TEMPLATE}",
              file=sys.stderr)
        sys.exit(1)

    prs = Presentation(str(TEMPLATE))
    _clear_slides(prs)
    title_slide(prs, meta)
    report.count("slides")

    for kind, text, body, notes in plan_slides(blocks, meta, report):
        if kind == "section":
            section_slide(prs, meta, text)
            report.count("slides")
            report.count("dividers")
        elif kind == "closing":
            closing_slide(prs, meta, text)
            report.count("slides")
        else:
            content_slide(prs, meta, text, body, report, notes)

    _set_properties(prs, meta)
    prs.save(output)
    report.finish(output, empty=M.is_empty(blocks))


if __name__ == "__main__":
    main()
