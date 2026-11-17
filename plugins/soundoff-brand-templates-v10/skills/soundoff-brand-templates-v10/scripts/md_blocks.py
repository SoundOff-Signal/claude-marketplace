"""
md_blocks: ONE Markdown parser for all four SoundOff builders.

Every builder renders the same block model, so a source file produces the same
document in Word, PDF, PowerPoint, and Excel. Fix a parser bug here and all four
formats get the fix.

Block model (plain dicts, JSON-shaped, easy to walk or assert on):

    {"type": "heading",  "level": 1-6, "inlines": [run, ...]}
    {"type": "para",     "inlines": [run, ...]}
    {"type": "list",     "ordered": bool, "items": [[block, ...], ...]}
    {"type": "code",     "lang": str, "text": str}
    {"type": "quote",    "blocks": [block, ...]}
    {"type": "callout",  "kind": "note|tip|important|warning|caution",
                         "title": str or None, "blocks": [block, ...]}
    {"type": "image",    "src": str, "alt": str, "width": float or None,
                         "path": str (absolute, set by media.prepare)}
    {"type": "table",    "header": [[run, ...], ...],
                         "rows": [[[run, ...], ...], ...],
                         "raw_rows": [[str, ...], ...],
                         "align": ["left"|"center"|"right", ...]}
    {"type": "hr"}
    {"type": "pagebreak"}

An inline run is {"text": str, "bold": bool, "italic": bool, "code": bool,
"href": str or None}. A list item is a list of blocks; the first is normally a
para carrying the item text, and any nested list is a later block in that item,
so nesting is preserved to arbitrary depth.

Supported syntax: ATX headings (#..######), paragraphs with hard-wrap
continuation, - / * / + bullets, 1. / 1) ordered lists, nesting by indent,
fenced code (``` or ~~~ with optional language; ```mermaid becomes a diagram),
> blockquotes, > [!NOTE] style callouts, a paragraph that is only an image
(![alt](path){width=60%}), pipe tables with alignment row, thematic breaks,
<!-- pagebreak --> (other HTML comments are dropped), and inline **bold**,
*italic*, `code`, [text](url), plus backslash escapes. Deliberately not
supported: footnotes, definition lists, raw HTML blocks, reference links.
`parse()` reports those on stderr rather than swallowing them.
"""

import html as _html
import re
import sys

__all__ = [
    "parse", "parse_with_warnings", "to_html", "heading_ids", "plain_text",
    "run", "walk", "is_empty", "strip_notes", "split_front_matter",
    "SUPPORTED_SYNTAX",
]

SUPPORTED_SYNTAX = (
    "headings, paragraphs, bullet and ordered lists (nested), fenced code, "
    "Mermaid diagrams, blockquotes, callouts, images, pipe tables, thematic "
    "breaks, page breaks, and inline bold/italic/code/links"
)

# Backslash escapes are parked on these sentinels so inline regexes cannot see
# the escaped character, then restored when runs are built.
_ESC = "\x00"
_ESCAPABLE = "\\`*_{}[]()#+-.!|>~"


# --------------------------------------------------------------------------- #
# Inline
# --------------------------------------------------------------------------- #
def run(text, bold=False, italic=False, code=False, href=None):
    return {"text": text, "bold": bold, "italic": italic, "code": code,
            "href": href}


_INLINE_RE = re.compile(
    r"""
      (?P<ctick>`+)(?P<code>.+?)(?P=ctick)
    | !\[(?P<ialt>[^\]]*)\]\(\s*(?P<isrc>[^)\s]+)(?:\s+"[^"]*")?\s*\)
    | \[(?P<ltext>[^\]]*)\]\(\s*(?P<lhref>[^)\s]+)(?:\s+"[^"]*")?\s*\)
    | (?P<smark>\*\*|__)(?P<strong>\S(?:.*?\S)?)(?P=smark)
    | (?P<emark>[*_])(?P<em>\S(?:.*?\S)?)(?P=emark)
    | <(?P<auto>(?:https?://|mailto:)[^>\s]+)>
    """,
    re.X | re.S,
)


def _escape_sentinels(text):
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] in _ESCAPABLE:
            out.append(_ESC + text[i + 1])
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _unescape(text):
    return re.sub(_ESC + r"(.)", r"\1", text)


def _inline(text, *, bold=False, italic=False, href=None, _top=True):
    """Parse inline Markdown into a flat list of styled runs."""
    if _top:
        text = _escape_sentinels(text)
    runs = []
    pos = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append(run(_unescape(text[pos:m.start()]), bold, italic,
                            False, href))
        if m.group("code") is not None:
            runs.append(run(_unescape(m.group("code")), bold, italic, True,
                            href))
        elif m.group("isrc") is not None:
            # No image support in the block model; keep the alt text visible.
            label = m.group("ialt") or m.group("isrc")
            runs.append(run(_unescape(label), bold, italic, False, href))
        elif m.group("lhref") is not None:
            label = m.group("ltext") or m.group("lhref")
            runs.extend(_inline(label, bold=bold, italic=italic,
                                href=m.group("lhref"), _top=False))
        elif m.group("strong") is not None:
            runs.extend(_inline(m.group("strong"), bold=True, italic=italic,
                                href=href, _top=False))
        elif m.group("em") is not None:
            runs.extend(_inline(m.group("em"), bold=bold, italic=True,
                                href=href, _top=False))
        elif m.group("auto") is not None:
            runs.extend(_inline(m.group("auto"), bold=bold, italic=italic,
                                href=m.group("auto"), _top=False))
        pos = m.end()
    if pos < len(text):
        runs.append(run(_unescape(text[pos:]), bold, italic, False, href))
    return [r for r in runs if r["text"]]


def plain_text(inlines):
    """Flatten runs back to unstyled text (labels, warnings, QA assertions)."""
    return "".join(r["text"] for r in inlines)


# --------------------------------------------------------------------------- #
# Block-level
# --------------------------------------------------------------------------- #
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([A-Za-z0-9_+.-]*)\s*$")
_HR_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])(\s+)(.*)$")
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
_DELIM_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
_COMMENT_RE = re.compile(r"^\s{0,3}<!--")
_PAGEBREAK_RE = re.compile(r"^\s{0,3}\\(?:pagebreak|newpage)\s*$")
_PAGEBREAK_WORDS = {"pagebreak", "page-break", "page break", "newpage"}
_IMAGE_RE = re.compile(
    r'^!\[(?P<alt>[^\]]*)\]\(\s*(?P<src>[^)\s]+)(?:\s+"[^"]*")?\s*\)'
    r'(?:\{\s*width\s*=\s*(?P<w>\d{1,3})\s*%\s*\})?$')
_CALLOUT_RE = re.compile(
    r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", re.I)
_UNSUPPORTED = (
    (re.compile(r"^\s{0,3}\[\^[^\]]+\]:"), "footnote definition"),
    (re.compile(r"^\s{0,3}\[[^\]]+\]:\s*\S+"), "reference link definition"),
    (re.compile(r"^\s{0,3}<(/?)(div|table|p|span|img|br|section)\b", re.I),
     "raw HTML block"),
    (re.compile(r"^\s{0,3}:\s+\S"), "definition list"),
)


def _is_block_start(line):
    return bool(
        not line.strip()
        or _HEADING_RE.match(line)
        or _FENCE_RE.match(line)
        or _HR_RE.match(line)
        or _ITEM_RE.match(line)
        or _QUOTE_RE.match(line)
        or _COMMENT_RE.match(line)
        or _PAGEBREAK_RE.match(line)
    )


def _split_row(line):
    line = line.strip()
    line = re.sub(r"^\|", "", line)
    line = re.sub(r"\|$", "", line)
    # An escaped pipe is not a cell boundary.
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip() for c in cells]


def _table_align(delim_line):
    out = []
    for cell in _split_row(delim_line):
        left, right = cell.startswith(":"), cell.endswith(":")
        out.append("center" if left and right else
                   "right" if right else "left")
    return out


def _dedent(line, width):
    stripped = line.lstrip(" ")
    removed = len(line) - len(stripped)
    if removed >= width:
        return " " * (removed - width) + stripped
    return stripped


def parse(text, *, warn=True, source="content"):
    """Markdown -> block list. Unsupported constructs are reported on stderr."""
    warnings = []
    lines = (text or "").replace("\t", "    ").split("\n")
    blocks = _parse_lines(lines, warnings)
    if warn:
        for w in warnings:
            print(f"warning [{source}]: {w}", file=sys.stderr)
    return blocks


def parse_with_warnings(text):
    warnings = []
    lines = (text or "").replace("\t", "    ").split("\n")
    return _parse_lines(lines, warnings), warnings


def _parse_lines(lines, warnings):
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # HTML comments: invisible notes to the author, or a page-break directive.
        if _COMMENT_RE.match(line):
            body = [line]
            while "-->" not in lines[i] and i + 1 < n:
                i += 1
                body.append(lines[i])
            i += 1
            inner = " ".join(body).strip()
            inner = re.sub(r"^\s*<!--|-->.*$", "", inner).strip().lower()
            if inner in _PAGEBREAK_WORDS:
                blocks.append({"type": "pagebreak"})
            continue

        if _PAGEBREAK_RE.match(line):
            blocks.append({"type": "pagebreak"})
            i += 1
            continue

        for pat, label in _UNSUPPORTED:
            if pat.match(line):
                warnings.append(
                    f"line {i + 1}: {label} is not supported and will render "
                    f"as literal text: {line.strip()[:60]}")
                break

        m = _FENCE_RE.match(line)
        if m:
            indent, fence, lang = m.group(1), m.group(2), m.group(3)
            body = []
            i += 1
            closer = re.compile(r"^\s*" + re.escape(fence[0]) + "{" +
                                str(len(fence)) + r",}\s*$")
            while i < n and not closer.match(lines[i]):
                body.append(_dedent(lines[i], len(indent)))
                i += 1
            i += 1  # consume the closing fence
            blocks.append({"type": "code", "lang": lang,
                           "text": "\n".join(body).rstrip("\n")})
            continue

        m = _HEADING_RE.match(line)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)),
                           "inlines": _inline(m.group(2))})
            i += 1
            continue

        if _HR_RE.match(line):
            blocks.append({"type": "hr"})
            i += 1
            continue

        if _QUOTE_RE.match(line):
            inner = []
            while i < n and (_QUOTE_RE.match(lines[i]) or
                             (lines[i].strip() and inner and
                              not _is_block_start(lines[i]))):
                qm = _QUOTE_RE.match(lines[i])
                inner.append(qm.group(1) if qm else lines[i].strip())
                i += 1
            cm = _CALLOUT_RE.match(inner[0].strip()) if inner else None
            if cm:
                blocks.append({"type": "callout", "kind": cm.group(1).lower(),
                               "title": cm.group(2).strip() or None,
                               "blocks": _parse_lines(inner[1:], warnings)})
            else:
                blocks.append({"type": "quote",
                               "blocks": _parse_lines(inner, warnings)})
            continue

        if _ITEM_RE.match(line):
            block, i = _parse_list(lines, i, warnings)
            blocks.append(block)
            continue

        # Pipe table: header row followed by an alignment/delimiter row.
        if "|" in line and i + 1 < n and _DELIM_RE.match(lines[i + 1]) \
                and "|" in lines[i + 1]:
            header = [_inline(c) for c in _split_row(line)]
            align = _table_align(lines[i + 1])
            i += 2
            rows, raw_rows = [], []
            while i < n and lines[i].strip() and "|" in lines[i]:
                cells = _split_row(lines[i])
                cells += [""] * (len(header) - len(cells))
                cells = cells[:len(header)]
                rows.append([_inline(c) for c in cells])
                # Raw text keeps formulas like =C{row}*D{row} intact for Excel.
                raw_rows.append([c.replace("\\|", "|") for c in cells])
                i += 1
            align += ["left"] * (len(header) - len(align))
            blocks.append({"type": "table", "header": header, "rows": rows,
                           "raw_rows": raw_rows,
                           "align": align[:len(header)]})
            continue

        # Paragraph: join hard-wrapped continuation lines into one paragraph.
        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not _is_block_start(lines[i]) \
                and not ("|" in lines[i] and i + 1 < n
                         and _DELIM_RE.match(lines[i + 1])):
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf)
        im = _IMAGE_RE.match(text)
        if im:
            width = int(im.group("w")) / 100.0 if im.group("w") else None
            if width is not None:
                width = min(max(width, 0.1), 1.0)
            blocks.append({"type": "image", "src": im.group("src"),
                           "alt": _unescape(_escape_sentinels(im.group("alt"))),
                           "width": width})
            continue
        blocks.append({"type": "para", "inlines": _inline(text)})
    return blocks


def _parse_list(lines, i, warnings):
    """Consume one list at the indent of lines[i]; return (block, next_index)."""
    n = len(lines)
    first = _ITEM_RE.match(lines[i])
    base = len(first.group(1))
    ordered = bool(re.match(r"\d", first.group(2)))
    items = []          # each: list of raw lines, dedented to item content
    chunk = None
    content_w = None

    while i < n:
        line = lines[i]
        if not line.strip():
            # A blank line only ends the list if the next content line is not
            # part of it (looser than CommonMark, kinder to real documents).
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j >= n:
                break
            nxt = lines[j]
            nxt_item = _ITEM_RE.match(nxt)
            nxt_indent = len(nxt) - len(nxt.lstrip(" "))
            if not ((nxt_item and nxt_indent >= base) or
                    (content_w and nxt_indent >= content_w)):
                break
            if chunk is not None:
                chunk.append("")
            i = j
            continue

        m = _ITEM_RE.match(line)
        indent = len(line) - len(line.lstrip(" "))
        if m and indent <= base + 1:
            this_ordered = bool(re.match(r"\d", m.group(2)))
            if chunk is not None and this_ordered != ordered:
                break  # marker type switched: a sibling list, not this one
            content_w = indent + len(m.group(2)) + len(m.group(3))
            chunk = [m.group(4)]
            items.append(chunk)
            i += 1
            continue
        if chunk is None:
            break
        if indent >= (content_w or base + 2) or not _is_block_start(line):
            # Indented continuation, nested list, or lazy continuation line.
            chunk.append(_dedent(line, content_w or base + 2))
            i += 1
            continue
        break

    parsed_items = []
    for chunk in items:
        while chunk and not chunk[-1].strip():
            chunk.pop()
        parsed_items.append(_parse_lines(chunk, warnings))
    return {"type": "list", "ordered": ordered, "items": parsed_items}, i


# --------------------------------------------------------------------------- #
# Walking / inspection
# --------------------------------------------------------------------------- #
def walk(blocks):
    """Yield (block, depth) depth-first, descending into lists and quotes."""
    def _w(bs, d):
        for b in bs:
            yield b, d
            if b["type"] == "list":
                for item in b["items"]:
                    yield from _w(item, d + 1)
            elif b["type"] in ("quote", "callout"):
                yield from _w(b["blocks"], d + 1)
    yield from _w(blocks, 0)


NOTES_MARK = "???"


def strip_notes(blocks):
    """Drop deck speaker notes (a ??? line and everything after it up to the
    next heading) for formats that have no notes pane. Returns (blocks, n)."""
    out, skipping, dropped = [], False, 0
    for b in blocks:
        if b["type"] == "heading":
            skipping = False
        elif b["type"] == "para" and plain_text(b["inlines"]).strip() == NOTES_MARK:
            skipping = True
            dropped += 1
            continue
        if not skipping:
            out.append(b)
    return out, dropped


def is_empty(blocks):
    """True when nothing renderable survived the parse."""
    for b, _ in walk(blocks):
        if b["type"] in ("code", "table", "image"):
            return False
        if b["type"] in ("heading", "para") and plain_text(b["inlines"]).strip():
            return False
    return True


# --------------------------------------------------------------------------- #
# HTML rendering (the PDF builder's input)
# --------------------------------------------------------------------------- #
def _runs_html(inlines):
    out = []
    for r in inlines:
        t = _html.escape(r["text"])
        if r["code"]:
            t = f"<code>{t}</code>"
        if r["bold"]:
            t = f"<strong>{t}</strong>"
        if r["italic"]:
            t = f"<em>{t}</em>"
        if r["href"]:
            t = f'<a href="{_html.escape(r["href"], quote=True)}">{t}</a>'
        out.append(t)
    return "".join(out)


def heading_ids(blocks):
    """Stable anchor ids for top-level headings, in document order."""
    ids, n = {}, 0
    for b in blocks:
        if b["type"] == "heading":
            n += 1
            ids[id(b)] = f"h{n}"
    return ids


def to_html(blocks, _ids=None):
    parts = []
    ids = _ids if _ids is not None else heading_ids(blocks)
    for b in blocks:
        t = b["type"]
        if t == "heading":
            lvl = min(b["level"], 6)
            anchor = ids.get(id(b))
            attr = f' id="{anchor}"' if anchor else ""
            parts.append(f"<h{lvl}{attr}>{_runs_html(b['inlines'])}</h{lvl}>")
        elif t == "image":
            from pathlib import Path as _P
            src = b.get("path") or b["src"]
            if b.get("path"):
                src = _P(src).resolve().as_uri()
            style = f' style="width:{int(b["width"] * 100)}%"' \
                if b.get("width") else ""
            cap = (f"<figcaption>{_html.escape(b['alt'])}</figcaption>"
                   if b.get("alt") else "")
            parts.append(f'<figure><img src="{_html.escape(src, quote=True)}" '
                         f'alt="{_html.escape(b.get("alt") or "", quote=True)}"'
                         f'{style}/>{cap}</figure>')
        elif t == "callout":
            kind = b["kind"]
            title = b.get("title") or kind.capitalize()
            parts.append(f'<div class="callout callout-{kind}">'
                         f'<div class="callout-title">{_html.escape(title)}'
                         f'</div>{to_html(b["blocks"], ids)}</div>')
        elif t == "pagebreak":
            parts.append('<div class="pagebreak"></div>')
        elif t == "para":
            parts.append(f"<p>{_runs_html(b['inlines'])}</p>")
        elif t == "hr":
            parts.append("<hr />")
        elif t == "code":
            cls = f' class="language-{_html.escape(b["lang"], quote=True)}"' \
                if b["lang"] else ""
            parts.append(f"<pre><code{cls}>{_html.escape(b['text'])}"
                         "</code></pre>")
        elif t == "quote":
            parts.append(f"<blockquote>{to_html(b['blocks'], ids)}"
                         "</blockquote>")
        elif t == "list":
            tag = "ol" if b["ordered"] else "ul"
            lis = "".join(f"<li>{_item_html(item)}</li>" for item in b["items"])
            parts.append(f"<{tag}>{lis}</{tag}>")
        elif t == "table":
            th = "".join(
                f'<th style="text-align:{a}">{_runs_html(c)}</th>'
                for c, a in zip(b["header"], b["align"]))
            trs = []
            for row in b["rows"]:
                tds = "".join(
                    f'<td style="text-align:{a}">{_runs_html(c)}</td>'
                    for c, a in zip(row, b["align"]))
                trs.append(f"<tr>{tds}</tr>")
            parts.append(f"<table><thead><tr>{th}</tr></thead><tbody>"
                         f"{''.join(trs)}</tbody></table>")
    return "".join(parts)


def _item_html(item_blocks):
    """A leading para inside <li> renders bare so bullets stay tight."""
    if item_blocks and item_blocks[0]["type"] == "para":
        head = _runs_html(item_blocks[0]["inlines"])
        return head + to_html(item_blocks[1:])
    return to_html(item_blocks)


# --------------------------------------------------------------------------- #
# Front matter (shared by every builder so the rules never diverge)
# --------------------------------------------------------------------------- #
def split_front_matter(text):
    """Return (metadata_dict, body_markdown)."""
    import yaml
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


if __name__ == "__main__":
    import json
    src = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1]).read()
    meta, body = split_front_matter(src)
    print(json.dumps({"front_matter": meta, "blocks": parse(body)}, indent=2,
                     default=str))
