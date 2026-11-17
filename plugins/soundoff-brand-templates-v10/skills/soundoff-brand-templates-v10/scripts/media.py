"""
media: images and Mermaid diagrams for every builder.

prepare() walks the parsed block model once, before a builder renders it:

  * image blocks get an absolute, verified `path` (relative paths resolve from
    the content file's folder). A missing or remote image becomes a visible
    "[missing image: ...]" paragraph and a warning, never a silent gap.
  * ```mermaid fenced blocks are rendered to PNG with the brand theme
    (brand.MERMAID_CONFIG) and become image blocks. A first line of
    `%% caption: Text` sets the caption. If the Mermaid CLI (mmdc) is not
    installed, the block stays as code and the build warns, so the source is
    still visible and nothing is lost.

Rendered diagrams are cached by content hash in the system temp folder, so
building the same source to four formats renders each diagram once.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import brand
import md_blocks as M

RASTER = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
CACHE = Path(tempfile.gettempdir()) / "soundoff-brand-diagrams"
_CAPTION_RE = re.compile(r"^\s*%%\s*caption\s*:\s*(.+)$", re.I)


def image_size(path):
    """(width_px, height_px) or None."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def fit(path, max_w_in, max_h_in, width_frac=None):
    """(w_in, h_in) for an image scaled to fit the box, keeping its aspect."""
    size = image_size(path)
    target_w = max_w_in * (width_frac or 1.0)
    if not size:
        return target_w, None
    w, h = size
    aspect = h / w if w else 1.0
    if not width_frac:
        # Do not blow small images up past ~1.5x their 96-dpi size.
        target_w = min(target_w, max(w / 96.0 * 1.5, 1.5))
    if target_w * aspect > max_h_in:
        target_w = max_h_in / aspect
    return target_w, target_w * aspect


def _missing(alt, src, reason, report):
    report.warn(f"image {src!r}: {reason}")
    label = alt or src
    return {"type": "para",
            "inlines": [M.run(f"[missing image: {label}]", italic=True)]}


def _resolve_image(block, base_dir, report, fmt):
    src = block["src"]
    if re.match(r"^[a-z]+://", src, re.I):
        return _missing(block.get("alt"), src, "remote images are not "
                        "fetched; save the file next to the content and "
                        "reference it by path", report)
    path = Path(src)
    if not path.is_absolute():
        path = (Path(base_dir) / path)
    path = path.resolve()
    if not path.exists():
        return _missing(block.get("alt"), src, f"not found at {path}", report)
    ext = path.suffix.lower()
    if ext == ".svg" and fmt != "pdf":
        return _missing(block.get("alt"), src, "SVG only renders in PDF; "
                        "export a PNG for Word and PowerPoint", report)
    if ext not in RASTER and ext != ".svg":
        return _missing(block.get("alt"), src, f"unsupported type {ext}",
                        report)
    out = dict(block)
    out["path"] = str(path)
    return out


def _mmdc():
    return shutil.which("mmdc")


def render_mermaid(source, report):
    """PNG path for Mermaid source, or None if it cannot be rendered here."""
    exe = _mmdc()
    if not exe:
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(
        (source + json.dumps(brand.MERMAID_CONFIG, sort_keys=True)).encode()
    ).hexdigest()[:20]
    png = CACHE / f"{digest}.png"
    if png.exists():
        return str(png)
    src = CACHE / f"{digest}.mmd"
    cfg = CACHE / "brand-config.json"
    src.write_text(source, encoding="utf-8")
    cfg.write_text(json.dumps(brand.MERMAID_CONFIG), encoding="utf-8")
    cmd = [exe, "-i", str(src), "-o", str(png), "-b", "white", "-s", "3",
           "-c", str(cfg), "-q"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0 and "sandbox" in (res.stderr or "").lower():
            pcfg = CACHE / "puppeteer.json"
            pcfg.write_text(json.dumps({"args": ["--no-sandbox"]}))
            res = subprocess.run(cmd + ["-p", str(pcfg)], capture_output=True,
                                 text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        report.warn(f"Mermaid render failed: {exc}")
        return None
    if res.returncode != 0 or not png.exists():
        detail = (res.stderr or res.stdout or "").strip().splitlines()
        report.warn("Mermaid render failed"
                    + (f": {detail[-1][:160]}" if detail else ""))
        return None
    return str(png)


def _diagram(block, report):
    lines = block["text"].split("\n")
    caption = None
    if lines and _CAPTION_RE.match(lines[0]):
        caption = _CAPTION_RE.match(lines[0]).group(1).strip()
        lines = lines[1:]
    source = "\n".join(lines).strip()
    png = render_mermaid(source, report)
    if not png:
        if not _mmdc():
            report.warn("a Mermaid diagram was left as source text because "
                        "the Mermaid CLI is not installed "
                        "(npm install -g @mermaid-js/mermaid-cli)")
        return block
    report.count("diagrams")
    return {"type": "image", "src": "mermaid", "alt": caption or "",
            "width": None, "path": png, "diagram": True}


def prepare(blocks, base_dir, report, fmt):
    """Return a new block list with images resolved and diagrams rendered."""
    out = []
    for b in blocks:
        t = b["type"]
        if t == "image":
            nb = _resolve_image(b, base_dir, report, fmt)
            if nb["type"] == "image":
                report.count("images")
            out.append(nb)
        elif t == "code" and b.get("lang", "").lower() == "mermaid":
            out.append(_diagram(b, report))
        elif t == "list":
            out.append(dict(b, items=[prepare(item, base_dir, report, fmt)
                                      for item in b["items"]]))
        elif t in ("quote", "callout"):
            out.append(dict(b, blocks=prepare(b["blocks"], base_dir, report,
                                              fmt)))
        else:
            out.append(b)
    return out


def base_dir_of(content_path):
    return os.path.dirname(os.path.abspath(content_path))
