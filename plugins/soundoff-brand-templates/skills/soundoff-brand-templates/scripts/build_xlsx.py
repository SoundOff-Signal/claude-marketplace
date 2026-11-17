#!/usr/bin/env python3
"""
SoundOff Signal branded Excel (.xlsx) builder: registers, trackers, matrices,
KPI scoreboards.

Renders a Markdown content file (front matter + one or more pipe tables) into a
brand-compliant workbook: red title banner, classification marking, styled
header row with frozen panes and autofilter, zebra banding, and live status
coloring. Shares brand.py and the md_blocks.py parser with the other builders.

What makes a sheet a working tracker rather than a picture of one:
  * Typed cells. 42 -> number, 1,250.5 -> number, 45% -> percent,
    $1,200 -> currency, 2026-11-17 -> date. Sorting and filtering work.
  * Formulas. A cell starting with = is written as a formula. {row} becomes the
    cell's own row number, {prev} the row above it, {first} / {last} the first
    and last table rows. A totals row sums the rows above it:
    =C{row}*D{row}   or   =SUM(E{first}:E{prev})
  * Live status colors. Severity / Priority / Status / Risk Level / Rating /
    Result / State columns get conditional formatting, so changing "Open" to
    "Closed" recolors the cell, plus a dropdown of the allowed values
    (warning-only, so new values can still be typed).

Content syntax:
    (front matter)     -> banner + marking + metadata line
    # / ## Sheet Name  -> start a new worksheet
    | md table |       -> the sheet's data
    paragraphs, lists, callouts -> note lines above the table
    ## Name [metrics]  -> KPI tile layout (Metric | Value | Target | Context...)

Usage:
    python build_xlsx.py --content register.md --output out.xlsx [--strict]
"""
import argparse
import datetime as dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brand  # noqa: E402

brand.require("yaml", "openpyxl")

from openpyxl import Workbook  # noqa: E402
from openpyxl.formatting.rule import CellIsRule  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402
from openpyxl.worksheet.properties import PageSetupProperties  # noqa: E402

import md_blocks as M  # noqa: E402

HEX = lambda name: "FF" + "".join(f"{c:02X}" for c in brand.RGB[name])  # noqa: E731

# Status vocabulary -> (fill color name, text color name). Keyed lowercase.
_RED, _AMB, _YEL, _GRN, _NEU = (("red", "white"), ("amber", "white"),
                               ("yellow", "ink"), ("green", "white"),
                               ("neutral", "ink"))
STATUS_COLORS = {
    "critical": _RED, "high": _AMB, "medium": _YEL, "low": _GRN,
    "open": _RED, "blocked": _RED, "overdue": _RED, "fail": _RED,
    "failed": _RED, "at risk": _AMB, "in progress": _YEL, "in review": _YEL,
    "pending": _YEL, "on hold": _NEU, "not started": _NEU, "planned": _NEU,
    "deferred": _NEU, "accepted": _NEU, "closed": _GRN, "resolved": _GRN,
    "done": _GRN, "complete": _GRN, "completed": _GRN, "pass": _GRN,
    "passed": _GRN, "on track": _GRN, "mitigated": _GRN,
}
STATUS_COLS = {"severity", "priority", "status", "risk level", "rating",
               "result", "state", "health", "risk rating", "inherent risk",
               "residual risk"}
SCALE_LOWER = [v.lower() for v in brand.SEVERITY_SCALE]
SPARE_ROWS = 500   # formatting and dropdowns extend past the data for new rows

HAIR = Side(style="thin", color="FFD8D8D8")
BORDER = Border(left=HAIR, right=HAIR, top=HAIR, bottom=HAIR)


# --------------------------------------------------------------------------- #
# Blocks -> sheets
# --------------------------------------------------------------------------- #
def plan_sheets(blocks, report):
    """[(sheet_name_or_None, notes, table_block_or_None), ...]"""
    sheets = []
    name, notes, table = None, [], None

    def flush():
        nonlocal name, notes, table
        if table is not None or notes or name:
            sheets.append((name, notes[:], table))
        name, notes, table = None, [], None

    for block in blocks:
        t = block["type"]
        if t == "heading":
            if block["level"] <= 2:
                flush()
                name = M.plain_text(block["inlines"]).strip()
            else:
                notes.append(M.plain_text(block["inlines"]).strip().upper())
            continue
        if t == "table":
            if table is not None:
                flush()
            table = block
            continue
        if t == "para":
            notes.append(M.plain_text(block["inlines"]).strip())
            continue
        if t == "list":
            for item in block["items"]:
                for inner in item:
                    if inner["type"] == "para":
                        notes.append("• " + M.plain_text(inner["inlines"]))
            continue
        if t == "callout":
            label = (block.get("title") or brand.CALLOUTS[block["kind"]][0])
            text = " ".join(M.plain_text(b["inlines"]) for b in block["blocks"]
                            if b["type"] == "para")
            notes.append(f"{label.upper()}: {text}".strip())
            continue
        if t in ("hr", "pagebreak"):
            continue
        report.skipped(t, "a worksheet cannot represent this block")
    flush()
    return [s for s in sheets if s[2] is not None or s[1]]


# --------------------------------------------------------------------------- #
# Typed values
# --------------------------------------------------------------------------- #
_NUM_RE = re.compile(r"^-?\d{1,3}(,\d{3})*(\.\d+)?$|^-?\d+(\.\d+)?$")
_PCT_RE = re.compile(r"^-?\d+(\.\d+)?%$")
_CUR_RE = re.compile(r"^-?\$\s?\d{1,3}(,\d{3})*(\.\d+)?$|^-?\$\s?\d+(\.\d+)?$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def typed(raw, row, first, last):
    """(value, number_format or None) for one cell's raw text."""
    text = (raw or "").strip()
    if not text:
        return None, None
    if text.startswith("="):
        return (text.replace("{row}", str(row)).replace("{prev}", str(row - 1))
                .replace("{first}", str(first))
                .replace("{last}", str(last))), None
    plain = text.replace("\\", "")
    if _PCT_RE.match(plain):
        return float(plain[:-1]) / 100.0, "0%" if "." not in plain else "0.0%"
    if _CUR_RE.match(plain):
        val = float(plain.replace("$", "").replace(",", "").replace(" ", ""))
        return val, '"$"#,##0.00' if "." in plain else '"$"#,##0'
    if _NUM_RE.match(plain):
        val = float(plain.replace(",", ""))
        if val.is_integer() and "." not in plain:
            return int(val), "#,##0" if "," in plain else None
        return val, None
    if _DATE_RE.match(plain):
        try:
            return dt.date.fromisoformat(plain), "yyyy-mm-dd"
        except ValueError:
            pass
    return None, None


# --------------------------------------------------------------------------- #
# Shared chrome
# --------------------------------------------------------------------------- #
def _banner(ws, meta, last_col):
    """Title banner, subtitle line, and the metadata/classification line."""
    r = 1
    ws.merge_cells(f"A{r}:{last_col}{r}")
    c = ws[f"A{r}"]
    c.value = meta.get("title") or "Untitled Workbook"
    c.font = Font(name=brand.FONT_HEADLINE, size=20, bold=True,
                  color="FFFFFFFF")
    c.fill = PatternFill("solid", fgColor=HEX("red"))
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[r].height = 34
    r += 1

    # Subtitle and metadata rows are deliberately not merged: merged cells clip,
    # and these lines can be long. Unmerged, they overflow across empty cells.
    if meta.get("subtitle") or meta.get("doc_type"):
        c = ws[f"A{r}"]
        bits = [b for b in [meta.get("doc_type"), meta.get("subtitle")] if b]
        c.value = "  |  ".join(str(b) for b in bits)
        c.font = Font(name=brand.FONT_BODY, size=10, color=HEX("gray"))
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[r].height = 18
        r += 1

    c = ws[f"A{r}"]
    bits = [meta["classification"].upper()]
    for key, prefix in (("doc_id", ""), ("department", ""), ("date", ""),
                        ("version", "v"), ("framework", ""),
                        ("nist_csf", "NIST CSF: "), ("owner", "Owner: ")):
        if meta.get(key):
            bits.append(f"{prefix}{meta[key]}")
    if meta.get("status"):
        bits.append(str(meta["status"]).upper())
    c.value = "    |    ".join(str(b) for b in bits)
    c.font = Font(name=brand.FONT_BODY, size=9, bold=True, color=HEX("red"))
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[r].height = 16
    return r + 1


def _notes(ws, notes, start_row):
    r = start_row
    for note in notes:
        if not note:
            continue
        c = ws[f"A{r}"]
        c.value = note
        c.font = Font(name=brand.FONT_BODY, size=9.5, color=HEX("ink"))
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        r += 1
    return r


def _print_setup(ws, meta):
    ws.oddFooter.left.text = meta["classification"].upper()
    ws.oddFooter.center.text = (f"{brand.COMPANY}"
                               + (f" · {meta['doc_id']}" if meta.get("doc_id")
                                  else ""))
    ws.oddFooter.right.text = "Page &P of &N"
    if meta["_dual_banner"]:
        ws.oddHeader.center.text = meta["classification"].upper()
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)


# --------------------------------------------------------------------------- #
# Sheet styles
# --------------------------------------------------------------------------- #
def style_metrics_sheet(ws, meta, header, rows, notes, report):
    """KPI tiles: uppercase red label, large metric-blue value, gray caption.
    Expects Metric | Value | Target; extra columns join the caption."""
    ncols = max(3 * len(rows), 6)
    last_col = get_column_letter(ncols)
    r = _banner(ws, meta, last_col)
    r = _notes(ws, notes, r) + 1

    label_r, value_r, caption_r = r, r + 1, r + 2
    ws.row_dimensions[value_r].height = 44
    for i, row in enumerate(rows):
        col = 1 + i * 3
        cl, cr = get_column_letter(col), get_column_letter(col + 1)
        metric = row[0] if len(row) > 0 else ""
        value = row[1] if len(row) > 1 else ""
        caption = "  •  ".join(v for v in row[2:] if v)
        ws.merge_cells(f"{cl}{label_r}:{cr}{label_r}")
        c = ws[f"{cl}{label_r}"]
        c.value = metric.upper()
        c.font = Font(name=brand.FONT_HEADLINE, size=11, bold=True,
                      color=HEX("red"))
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells(f"{cl}{value_r}:{cr}{value_r}")
        c = ws[f"{cl}{value_r}"]
        val, fmt = typed(value, value_r, value_r, value_r)
        c.value = val if val is not None else value
        if fmt:
            c.number_format = fmt
        c.font = Font(name=brand.FONT_BODY, size=30, bold=True,
                      color=HEX("metric_blue"))
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells(f"{cl}{caption_r}:{cr}{caption_r}")
        c = ws[f"{cl}{caption_r}"]
        c.value = caption
        c.font = Font(name=brand.FONT_BODY, size=8.5, color=HEX("gray"))
        c.alignment = Alignment(horizontal="center", vertical="top",
                                wrap_text=True)
        ws.column_dimensions[cl].width = 16
        ws.column_dimensions[cr].width = 16
        ws.column_dimensions[get_column_letter(col + 2)].width = 3
    ws.row_dimensions[caption_r].height = 30
    ws.sheet_view.showGridLines = False
    _print_setup(ws, meta)
    report.count("KPI tiles", len(rows))


def _status_rules(ws, col_letter, first, last_fmt, values):
    """Conditional formatting so the color follows the value. Values keep
    their own casing so case-sensitive spreadsheet apps match too."""
    rng = f"{col_letter}{first}:{col_letter}{last_fmt}"
    for value in values:
        fill_name, text_name = STATUS_COLORS[value.lower()]
        ws.conditional_formatting.add(rng, CellIsRule(
            operator="equal", formula=[f'"{value}"'],
            fill=PatternFill("solid", fgColor=HEX(fill_name),
                             bgColor=HEX(fill_name)),
            font=Font(bold=True, color=HEX(text_name))))


def _dropdown(ws, col_letter, first, last_fmt, options):
    joined = ",".join(options)
    if not options or len(joined) > 250 or any("," in o for o in options):
        return False
    dv = DataValidation(type="list", formula1=f'"{joined}"', allow_blank=True,
                        errorStyle="warning", showErrorMessage=True,
                        errorTitle="Not in the list",
                        error="This value is not one of the listed options.")
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}{first}:{col_letter}{last_fmt}")
    return True


def style_sheet(ws, meta, table, notes, report):
    header = [M.plain_text(c) for c in table["header"]]
    raw_rows = table.get("raw_rows") or \
        [[M.plain_text(c) for c in row] for row in table["rows"]]
    text_rows = [[M.plain_text(c) for c in row] for row in table["rows"]]
    align = table["align"]
    ncols = len(header)
    last_col = get_column_letter(ncols)
    r = _banner(ws, meta, last_col)
    r = _notes(ws, notes, r) + 1

    header_row = r
    first = header_row + 1
    last = header_row + max(len(text_rows), 1)
    last_fmt = last + SPARE_ROWS
    status_cols = []
    for j, h in enumerate(header, start=1):
        cell = ws.cell(row=header_row, column=j, value=h.upper())
        cell.font = Font(name=brand.FONT_HEADLINE, size=10, bold=True,
                         color="FFFFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEX("red"))
        cell.alignment = Alignment(horizontal="left", vertical="center",
                                   wrap_text=True, indent=1)
        cell.border = BORDER
        if h.strip().lower() in STATUS_COLS:
            status_cols.append(j)
    ws.row_dimensions[header_row].height = 24

    formulas = 0
    for i, (raw, text) in enumerate(zip(raw_rows, text_rows)):
        rr = first + i
        band = i % 2 == 1
        for j in range(1, ncols + 1):
            raw_v = raw[j - 1] if j - 1 < len(raw) else ""
            txt_v = text[j - 1] if j - 1 < len(text) else ""
            val, fmt = typed(raw_v, rr, first, last)
            is_formula = isinstance(val, str) and val.startswith("=")
            formulas += is_formula
            cell = ws.cell(row=rr, column=j,
                           value=val if val is not None else (txt_v or None))
            if fmt:
                cell.number_format = fmt
            cell.font = Font(name=brand.FONT_BODY, size=10, color=HEX("ink"))
            numeric = val is not None and not isinstance(val, str)
            explicit = align[j - 1] if j - 1 < len(align) else "left"
            horiz = explicit if explicit != "left" else \
                ("center" if numeric or is_formula else "left")
            cell.alignment = Alignment(horizontal=horiz, vertical="top",
                                       wrap_text=True,
                                       indent=1 if horiz == "left" else 0)
            cell.border = BORDER
            if band:
                cell.fill = PatternFill("solid", fgColor=HEX("band_even"))
            if j in status_cols:
                cell.alignment = Alignment(horizontal="center",
                                           vertical="center")

    for j in status_cols:
        col = get_column_letter(j)
        present = []
        for row in text_rows:
            v = (row[j - 1] if j - 1 < len(row) else "").strip()
            if v and v.lower() not in [p.lower() for p in present]:
                present.append(v)
        lower = {p.lower() for p in present}
        if lower and lower <= set(SCALE_LOWER):
            options = list(brand.SEVERITY_SCALE)
        else:
            options = present
        values, seen = [], set()
        for o in options + present:
            if o.lower() in STATUS_COLORS and o not in seen:
                seen.add(o)
                values.append(o)
        _status_rules(ws, col, first, last_fmt, values)
        if _dropdown(ws, col, first, last_fmt, options):
            report.count("dropdowns")

    for j, h in enumerate(header, start=1):
        maxlen = len(h)
        for row in text_rows:
            if j - 1 < len(row):
                maxlen = max(maxlen, len(row[j - 1]))
        ws.column_dimensions[get_column_letter(j)].width = \
            min(max(maxlen + 4, 12), 52)

    ws.freeze_panes = ws.cell(row=first, column=1)
    ws.auto_filter.ref = f"A{header_row}:{last_col}{last}"
    _print_setup(ws, meta)
    report.count("rows", len(text_rows))
    if formulas:
        report.count("formulas", formulas)


def _set_properties(wb, meta):
    props = brand.properties(meta)
    p = wb.properties
    p.title = props["title"]
    p.subject = props["subject"]
    p.creator = props["author"]
    p.lastModifiedBy = props["author"]
    p.category = props["category"]
    p.keywords = props["keywords"]
    p.description = props["comments"]


def main():
    parser = argparse.ArgumentParser(
        description="SoundOff Signal branded Excel builder")
    brand.add_common_args(parser)
    args = parser.parse_args()

    report = brand.BuildReport("xlsx", strict=args.strict)
    with open(args.content, encoding="utf-8") as f:
        raw = f.read()
    front, body_md = M.split_front_matter(raw)
    meta = brand.resolve_meta(front, args, report)
    output = brand.resolve_output(args.output, meta, "xlsx")

    blocks, warnings = M.parse_with_warnings(body_md)
    for w in warnings:
        report.warn(w)
    blocks, n_notes = M.strip_notes(blocks)
    if n_notes:
        report.info(f"{n_notes} speaker-notes section(s) (???) left out; "
                    "they appear only in decks")

    sheets = plan_sheets(blocks, report)
    if not any(table is not None for _, _, table in sheets):
        print("error: no table found in the content; an .xlsx needs at least "
              "one pipe table", file=sys.stderr)
        sys.exit(1)

    wb = Workbook()
    wb.remove(wb.active)
    used = set()
    prose_only = [name or "(unnamed)" for name, _, table in sheets
                  if table is None]
    if prose_only:
        report.warn(f"{len(prose_only)} prose-only section(s) produced no "
                    f"worksheet: {', '.join(prose_only[:6])}"
                    f"{' ...' if len(prose_only) > 6 else ''}. An .xlsx carries "
                    "tables; put narrative in the .docx or .pdf.")
        report.count("sections without a table", len(prose_only))
    for name, notes, table in sheets:
        if table is None:
            continue
        is_metrics = bool(name and re.search(r"\[metrics\]", name, re.I))
        clean = re.sub(r"\s*\[metrics\]\s*", "", name or "", flags=re.I).strip()
        sheet_name = re.sub(r"[\[\]:*?/\\]", "-", clean or "Sheet")[:31]
        base, n = sheet_name, 2
        while sheet_name.lower() in used:
            sheet_name = f"{base[:28]} {n}"
            n += 1
        used.add(sheet_name.lower())
        ws = wb.create_sheet(title=sheet_name)
        if is_metrics:
            header = [M.plain_text(c) for c in table["header"]]
            rows = [[M.plain_text(c) for c in row] for row in table["rows"]]
            style_metrics_sheet(ws, meta, header, rows, notes, report)
        else:
            style_sheet(ws, meta, table, notes, report)
        report.count("sheets")

    _set_properties(wb, meta)
    wb.save(output)
    report.finish(output)


if __name__ == "__main__":
    main()
