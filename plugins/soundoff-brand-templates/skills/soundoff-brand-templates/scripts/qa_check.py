#!/usr/bin/env python3
"""
Automated QA for SoundOff Signal branded output.

Run this after every build. It fails loudly on the defects worth catching
mechanically, so the eyeball pass on rendered pages is only about layout.

Checks
  front matter   required keys, classification in the PY-DC set, layout,
                 document identity (a doc_id carrying another department's
                 code, a malformed SOS ID), and version-control fields that
                 belong only on controlled documents
  marking        classification on every page / slide / sheet
  artifacts      no literal Markdown ("](", "```", "**", table delimiter rows,
                 heading markers) and no unfilled {{placeholders}}
  empty pages    no page with zero extractable text
  tables         no Word table wider than the content area
  Word           real Heading styles, core properties, alt text on images
  PDF / PPTX / XLSX  document properties populated

Usage:
    python qa_check.py --content body.md out.docx out.pdf out.pptx out.xlsx
    python qa_check.py out.docx                 # structure + text checks only

Exit code 0 = pass, 1 = at least one failure. Warnings do not fail the run
unless --strict is given.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brand  # noqa: E402
import md_blocks as M  # noqa: E402

REQUIRED_KEYS = ("title", "classification")
RECOMMENDED_KEYS = ("doc_type", "author", "department")
CONTROLLED_KEYS = ("version", "status", "review_cycle")
VERSION_CONTROL_KEYS = ("status", "version_history", "approvals",
                        "review_cycle")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]{1,80}\}\}")

ARTIFACTS = [
    (re.compile(r"\]\("), "literal Markdown link"),
    (re.compile(r"```"), "literal code fence"),
    (re.compile(r"\*\*\S"), "literal bold markers"),
    (re.compile(r"^\s*\|?\s*:?-{3,}:?\s*\|"), "literal table delimiter row"),
    (re.compile(r"^\s*#{1,6}\s+\S"), "literal heading marker"),
]

# Word content width at 0.75in margins, in twips (portrait / landscape).
DOCX_CONTENT_W = 12240 - 2 * 1080
DOCX_CONTENT_W_LANDSCAPE = 15840 - 2 * 1080


class Results:
    def __init__(self):
        self.failures = []
        self.warnings = []
        self.passes = []

    def ok(self, msg):
        self.passes.append(msg)

    def fail(self, msg):
        self.failures.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def report(self, strict=False):
        for msg in self.passes:
            print(f"  pass  {msg}")
        for msg in self.warnings:
            print(f"  warn  {msg}")
        for msg in self.failures:
            print(f"  FAIL  {msg}")
        bad = len(self.failures) + (len(self.warnings) if strict else 0)
        print(f"\n{len(self.passes)} passed, {len(self.warnings)} warning(s), "
              f"{len(self.failures)} failure(s)")
        return 1 if bad else 0


# --------------------------------------------------------------------------- #
# Front matter
# --------------------------------------------------------------------------- #
def check_front_matter(path, res):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    meta, body = M.split_front_matter(raw)
    if not meta:
        res.fail(f"{os.path.basename(path)}: no YAML front matter")
        return meta, body
    missing = [k for k in REQUIRED_KEYS if not meta.get(k)]
    if missing:
        res.fail(f"front matter missing required key(s): {', '.join(missing)}")
    else:
        res.ok("front matter carries the required keys")
    memo = str(meta.get("layout") or "").lower() == "memo"
    thin = [k for k in RECOMMENDED_KEYS if not meta.get(k)
            and not (memo and k == "doc_type")
            and not (memo and k == "author" and meta.get("from"))]
    if thin:
        res.warn(f"front matter has no {', '.join(thin)}; the cover and "
                 "document properties will be thinner")
    try:
        level, marking = brand.normalize_classification(
            meta.get("classification"))
        res.ok(f"classification {marking} is in the PY-DC set")
        meta["_marking"] = marking
        meta["_level"] = level
    except brand.ClassificationError as exc:
        res.fail(str(exc))
        meta["_marking"] = str(meta.get("classification", "")).upper()
    layout = str(meta.get("layout") or "report").lower()
    if layout not in brand.LAYOUTS:
        res.fail(f"layout {layout!r} is not one of {', '.join(brand.LAYOUTS)}")
    if layout == "memo" and not meta.get("to"):
        res.warn("memo layout with no `to:` recipients")

    # Identity: the main guard against another department's code.
    findings = brand.identity_findings(meta)
    for severity, msg in findings:
        (res.fail if severity == "warn" else res.warn)(msg)
    if not any(sev == "warn" for sev, _ in findings):
        res.ok("document identity is consistent"
               + (f" ({meta['doc_id']})" if meta.get("doc_id") else ""))

    # Version control belongs only on documents that go through approval.
    if brand.is_controlled(meta):
        gaps = [k for k in CONTROLLED_KEYS if not meta.get(k)]
        if gaps:
            res.warn(f"controlled document without {', '.join(gaps)}")
    else:
        extra = [k for k in VERSION_CONTROL_KEYS if meta.get(k)]
        if extra:
            res.warn(f"{', '.join(extra)} set on a document that is not a "
                     "controlled type (policy, standard, procedure, plan, "
                     "runbook, guideline, work instruction, form). Drop them "
                     "unless this document goes through approval and revision.")
    if meta.get("status") and str(meta["status"]).strip().lower() \
            not in brand.STATUS_LABELS:
        res.warn(f"status {meta['status']!r} is not one of "
                 f"{', '.join(sorted(brand.STATUS_LABELS))}")
    return meta, body


def code_text(body):
    """Every line inside a fenced code block, so QA does not flag real code."""
    lines = set()
    for block, _ in M.walk(M.parse(body, warn=False)):
        if block["type"] == "code":
            lines.update(l.strip() for l in block["text"].split("\n"))
    return {l for l in lines if l}


# --------------------------------------------------------------------------- #
# Page text extraction
# --------------------------------------------------------------------------- #
def _have(tool):
    return shutil.which(tool) is not None


def to_pdf(path, tmpdir, res):
    if path.lower().endswith(".pdf"):
        return path
    if not _have("soffice"):
        res.warn(f"soffice not installed: skipped page checks for "
                 f"{os.path.basename(path)}")
        return None
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf",
                    "--outdir", tmpdir, path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=False, timeout=300)
    out = os.path.join(tmpdir,
                       os.path.splitext(os.path.basename(path))[0] + ".pdf")
    if not os.path.exists(out):
        res.fail(f"{os.path.basename(path)}: LibreOffice could not render it")
        return None
    return out


def pdf_pages(pdf, res):
    if not _have("pdftotext"):
        res.warn("pdftotext not installed: skipped page text checks")
        return []
    try:
        n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
            ["pdfinfo", pdf], capture_output=True, text=True,
            check=True).stdout).group(1))
    except Exception:
        res.warn(f"could not read the page count of {os.path.basename(pdf)}")
        return []
    pages = []
    for i in range(1, n + 1):
        text = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), pdf, "-"],
                              capture_output=True, text=True,
                              check=False).stdout
        pages.append(text)
    return pages


def check_pages(label, pages, marking, allowed_code, res, *, cover=True):
    if not pages:
        return
    missing_mark, empty = [], []
    # Tracked (letter-spaced) banners extract with spaces between characters, so
    # compare against a whitespace-free copy as well as the normalized one.
    tight_mark = re.sub(r"\s+", "", marking or "").upper()
    for i, text in enumerate(pages, start=1):
        flat = re.sub(r"\s+", " ", text).upper()
        tight = re.sub(r"\s+", "", text).upper()
        if marking and marking.upper() not in flat and tight_mark not in tight:
            missing_mark.append(i)
        if not text.strip():
            empty.append(i)
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped in allowed_code:
                continue
            for pattern, name in ARTIFACTS:
                if pattern.search(stripped):
                    res.fail(f"{label} page {i}: {name} survived into the "
                             f"output: {stripped[:70]!r}")
            ph = PLACEHOLDER_RE.search(stripped)
            if ph:
                res.fail(f"{label} page {i}: unfilled placeholder "
                         f"{ph.group(0)!r}")
    if missing_mark:
        res.fail(f"{label}: classification marking missing on page(s) "
                 f"{', '.join(map(str, missing_mark))}")
    else:
        res.ok(f"{label}: marking present on all {len(pages)} page(s)")
    if empty:
        res.fail(f"{label}: page(s) {', '.join(map(str, empty))} contain no text")
    else:
        res.ok(f"{label}: no empty page(s)")


# --------------------------------------------------------------------------- #
# Format-specific structure
# --------------------------------------------------------------------------- #
def check_docx(path, meta, res):
    try:
        from docx import Document
    except ImportError:
        res.warn("python-docx not installed: skipped .docx structure checks")
        return
    doc = Document(path)
    styles_used = {p.style.name for p in doc.paragraphs if p.style is not None}
    headings = {s for s in styles_used if s.startswith("Heading")}
    if headings:
        res.ok(f"Word headings use real styles ({', '.join(sorted(headings))})")
    else:
        res.fail("no Heading style used: the navigation pane, TOC field, and "
                 "the accessibility checker will all be broken")
    cp = doc.core_properties
    if not cp.title or not cp.author or cp.author == "python-docx":
        res.fail("core document properties are empty: SharePoint has nothing "
                 "to index")
    else:
        res.ok(f"core properties set (author {cp.author!r})")
    if meta and meta.get("doc_id") and meta["doc_id"] not in (cp.comments or ""):
        res.warn("doc_id is not recorded in the document properties")
    sec = doc.sections[0]
    limit = DOCX_CONTENT_W_LANDSCAPE if sec.page_width > sec.page_height \
        else DOCX_CONTENT_W
    for i, table in enumerate(doc.tables, start=1):
        widths = [c.width.twips for c in table.columns if c.width is not None]
        total = sum(widths)
        if total and total > limit + 20:
            res.fail(f".docx table {i} is {total} twips wide; the content area "
                     f"is {limit}")
    res.ok(f".docx tables fit the content area ({len(doc.tables)} checked)")
    from docx.oxml.ns import qn
    pics = doc.element.body.findall(".//" + qn("wp:docPr"))
    no_alt = [p for p in pics if not (p.get("descr") or "").strip()]
    if no_alt:
        res.fail(f".docx: {len(no_alt)} image(s) without alt text")
    elif pics:
        res.ok(f".docx: all {len(pics)} image(s) carry alt text")
    for i, table in enumerate(doc.tables, start=1):
        for row in table.rows:
            for cell in row.cells:
                ph = PLACEHOLDER_RE.search(cell.text)
                if ph:
                    res.fail(f".docx table {i}: unfilled placeholder "
                             f"{ph.group(0)!r}")
                    break


def check_pptx(path, meta, res):
    try:
        from pptx import Presentation
    except ImportError:
        res.warn("python-pptx not installed: skipped .pptx structure checks")
        return
    prs = Presentation(path)
    marking = (meta or {}).get("_marking", brand.DEFAULT_MARKING).upper()
    bad = []
    for i, slide in enumerate(prs.slides, start=1):
        text = " ".join(sh.text_frame.text for sh in slide.shapes
                        if sh.has_text_frame).upper()
        if marking not in text:
            bad.append(i)
        for sh in slide.shapes:
            if sh.has_table and sh.left is not None \
                    and sh.left + sh.width > prs.slide_width:
                res.fail(f"slide {i}: a table runs past the slide edge")
        for sh in slide.shapes:
            texts = []
            if sh.has_text_frame:
                texts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                texts += [c.text for r in sh.table.rows for c in r.cells]
            for t in texts:
                ph = PLACEHOLDER_RE.search(t)
                if ph:
                    res.fail(f"slide {i}: unfilled placeholder "
                             f"{ph.group(0)!r}")
    if bad:
        res.fail(f".pptx: marking missing on slide(s) "
                 f"{', '.join(map(str, bad))}")
    else:
        res.ok(f".pptx: marking present on all {len(prs.slides)} slide(s)")
    if not prs.core_properties.title:
        res.fail(".pptx: document properties are empty")
    else:
        res.ok(".pptx: document properties set")


def check_xlsx(path, meta, res):
    try:
        from openpyxl import load_workbook
    except ImportError:
        res.warn("openpyxl not installed: skipped .xlsx structure checks")
        return
    wb = load_workbook(path)
    marking = (meta or {}).get("_marking", brand.DEFAULT_MARKING).upper()
    bad = []
    for ws in wb.worksheets:
        footer = (ws.oddFooter.left.text or "").upper()
        banner = " ".join(str(c.value) for row in ws.iter_rows(min_row=1,
                                                              max_row=4)
                          for c in row if c.value).upper()
        if marking not in footer and marking not in banner:
            bad.append(ws.title)
    if bad:
        res.fail(f".xlsx: marking missing from sheet(s) {', '.join(bad)}")
    else:
        res.ok(f".xlsx: marking present on all {len(wb.worksheets)} sheet(s)")
    if not wb.properties.title:
        res.fail(".xlsx: workbook properties are empty")
    else:
        res.ok(".xlsx: workbook properties set")
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and PLACEHOLDER_RE.search(c.value):
                    res.fail(f".xlsx {ws.title}!{c.coordinate}: unfilled "
                             f"placeholder {c.value[:40]!r}")


def check_pdf_metadata(path, res):
    if not _have("pdfinfo"):
        return
    info = subprocess.run(["pdfinfo", path], capture_output=True, text=True,
                          check=False).stdout
    have = {k.strip(): v.strip() for k, v in
            (line.split(":", 1) for line in info.splitlines() if ":" in line)}
    missing = [k for k in ("Title", "Author", "Keywords") if not have.get(k)]
    if missing:
        res.fail(f".pdf document properties missing: {', '.join(missing)}")
    else:
        res.ok(".pdf document properties populated")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="QA gate for SoundOff branded output")
    parser.add_argument("outputs", nargs="+",
                        help="built .docx / .pdf / .pptx / .xlsx files")
    parser.add_argument("--content", help="the Markdown source, for front "
                                         "matter and code-block checks")
    parser.add_argument("--classification",
                        help="expected marking, when the build overrode the "
                             "front-matter value on the command line")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    parser.add_argument("--no-render", action="store_true",
                        help="skip the LibreOffice page-level checks")
    args = parser.parse_args()

    res = Results()
    meta, allowed_code = {}, set()
    if args.content:
        print(f"front matter: {args.content}")
        meta, body = check_front_matter(args.content, res)
        allowed_code = code_text(body)
    marking = meta.get("_marking", brand.DEFAULT_MARKING)
    if args.classification:
        try:
            _, marking = brand.normalize_classification(args.classification)
            meta["_marking"] = marking
        except brand.ClassificationError as exc:
            res.fail(str(exc))

    with tempfile.TemporaryDirectory() as tmp:
        for path in args.outputs:
            print(f"\n{path}")
            if not os.path.exists(path):
                res.fail(f"{path}: missing")
                continue
            ext = os.path.splitext(path)[1].lower()
            if ext == ".docx":
                check_docx(path, meta, res)
            elif ext == ".pptx":
                check_pptx(path, meta, res)
            elif ext == ".xlsx":
                check_xlsx(path, meta, res)
            elif ext == ".pdf":
                check_pdf_metadata(path, res)
            if ext in (".pdf", ".docx") and not args.no_render:
                pdf = to_pdf(path, tmp, res)
                if pdf:
                    check_pages(os.path.basename(path), pdf_pages(pdf, res),
                                marking, allowed_code, res)

    print()
    sys.exit(res.report(strict=args.strict))


if __name__ == "__main__":
    main()
