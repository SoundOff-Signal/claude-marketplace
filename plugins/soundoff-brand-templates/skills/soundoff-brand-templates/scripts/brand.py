"""
SoundOff Signal brand constants and shared plumbing for every builder.

build_docx.py, build_pdf.py, build_pptx.py, and build_xlsx.py all import from
here, so a Word procedure, a board deck, a tracker, and a PDF report draw the
same red, the same Oswald headline scale, the same cover fields, and the same
classification marking. Change a value once and every format picks it up. Do not
redefine colors, fonts, cover rows, or marking text inside a builder.

Nothing in this module is specific to one person or department. Who wrote a
document and which department owns it always come from the document's own front
matter. Department codes come from references/departments/departments.yaml.

Markdown parsing lives in md_blocks.py; image and diagram handling in media.py.
"""

import re
import sys
from pathlib import Path

# --- Paths (resolved relative to the skill root, not the CWD) ---
SKILL_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = SKILL_ROOT / "assets" / "fonts"
LOGOS_DIR = SKILL_ROOT / "assets" / "logos"
TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"
TESTS_DIR = SKILL_ROOT / "assets" / "tests"
DEPARTMENTS_FILE = SKILL_ROOT / "references" / "departments" / "departments.yaml"

SKILL_VERSION = "2.0"

# --------------------------------------------------------------------------- #
# Color palette (hex; canonical)
# --------------------------------------------------------------------------- #
RED = "#A71B28"         # PMS 187, primary. Headlines, rules, table headers, accents.
RED_DARK = "#7E1420"    # depth, cover gradient base, H3
INK = "#1A1A1A"         # body text, classification banner background
GRAY = "#6E6E6E"        # subtitles, captions, secondary metadata
GRAY_LIGHT = "#9B9B9B"  # bar accents, light rules
RULE = "#D8D8D8"        # table cell borders, hairlines
BAND_EVEN = "#FAF6F6"   # even-row table banding (faint warm tint of red)
CODE_BG = "#F5F5F5"     # fenced code block background
METRIC_BLUE = "#1A5383" # KPI / metric values, NOTE callouts
WHITE = "#FFFFFF"

# Status scale (registers, trackers, callouts). Kept here so Excel fills and
# document callouts use one set of values.
AMBER = "#E06C2E"
AMBER_TEXT = "#B4501C"  # amber dark enough for text on white
YELLOW = "#E9C46A"
GREEN = "#7DA86B"
GREEN_TEXT = "#4F7A40"
NEUTRAL = "#E6E6E6"

# Light tints for callout backgrounds.
TINT_BLUE = "#EEF3F8"
TINT_GREEN = "#F0F6ED"
TINT_RED = "#F9EEEF"
TINT_AMBER = "#FCF1EA"

COMPANY = "SoundOff Signal"
SITE_URL = "soundoffsignal.com"


def hex_to_rgb(h):
    """'#A71B28' -> (167, 27, 40). python-docx/pptx want RGB ints."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


_NAMED = {
    "red": RED, "red_dark": RED_DARK, "ink": INK, "gray": GRAY,
    "gray_light": GRAY_LIGHT, "rule": RULE, "band_even": BAND_EVEN,
    "code_bg": CODE_BG, "metric_blue": METRIC_BLUE, "white": WHITE,
    "amber": AMBER, "amber_text": AMBER_TEXT, "yellow": YELLOW,
    "green": GREEN, "green_text": GREEN_TEXT, "neutral": NEUTRAL,
    "tint_blue": TINT_BLUE, "tint_green": TINT_GREEN, "tint_red": TINT_RED,
    "tint_amber": TINT_AMBER,
}
RGB = {name: hex_to_rgb(val) for name, val in _NAMED.items()}
HEX = dict(_NAMED)

# --------------------------------------------------------------------------- #
# Typography
# --------------------------------------------------------------------------- #
# Oswald is the headline face (bundled static weights 300-700). Body is Arial;
# Liberation Sans is the metric-compatible substitute for rendering on Linux.
FONT_HEADLINE = "Oswald"
FONT_BODY = "Arial"
FONT_BODY_FALLBACK = "Liberation Sans"
FONT_MONO = "Consolas"
FONT_MONO_FALLBACK = "Liberation Mono"

OSWALD_WEIGHTS = {
    300: "Oswald-Light.ttf",
    400: "Oswald-Regular.ttf",
    500: "Oswald-Medium.ttf",
    600: "Oswald-SemiBold.ttf",
    700: "Oswald-Bold.ttf",
}

# --------------------------------------------------------------------------- #
# Callouts (> [!NOTE] etc.): label, accent color name, tint color name
# --------------------------------------------------------------------------- #
CALLOUTS = {
    "note": ("Note", "metric_blue", "tint_blue"),
    "tip": ("Tip", "green_text", "tint_green"),
    "important": ("Important", "red_dark", "tint_red"),
    "warning": ("Warning", "amber_text", "tint_amber"),
    "caution": ("Caution", "red", "tint_red"),
}

# Mermaid theme so diagrams carry the brand instead of Mermaid's default purple.
MERMAID_CONFIG = {
    "theme": "base",
    "themeVariables": {
        "fontFamily": "Arial, Liberation Sans, sans-serif",
        "fontSize": "15px",
        "primaryColor": "#FFFFFF",
        "primaryBorderColor": RED,
        "primaryTextColor": INK,
        "secondaryColor": BAND_EVEN,
        "secondaryBorderColor": GRAY,
        "tertiaryColor": CODE_BG,
        "tertiaryBorderColor": RULE,
        "lineColor": GRAY,
        "textColor": INK,
        "edgeLabelBackground": WHITE,
        "clusterBkg": BAND_EVEN,
        "clusterBorder": RULE,
        "noteBkgColor": TINT_AMBER,
        "noteBorderColor": AMBER,
        "actorBkg": WHITE,
        "actorBorder": RED,
        "signalColor": INK,
    },
}

# --------------------------------------------------------------------------- #
# Classification marking
# --------------------------------------------------------------------------- #
# Authority: the SoundOff Signal Data Classification Policy (PY-DC), four levels,
# company-wide. SoundOff safeguards Federal Contract Information under
# FAR 52.240-93 (formerly 52.204-21) and holds no Controlled Unclassified
# Information, so no document should default toward CUI handling. The
# dual-banner path is the HIGHLY CONFIDENTIAL treatment.
CLASSIFICATION_MARKINGS = {
    "PUBLIC": "PUBLIC",
    "INTERNAL USE": "INTERNAL USE ONLY",
    "CONFIDENTIAL": "CONFIDENTIAL",
    "HIGHLY CONFIDENTIAL": "HIGHLY CONFIDENTIAL",
}
CLASSIFICATIONS = tuple(CLASSIFICATION_MARKINGS)

CLASSIFICATION_ALIASES = {
    "PUBLIC": "PUBLIC",
    "INTERNAL": "INTERNAL USE",
    "INTERNAL USE": "INTERNAL USE",
    "INTERNAL USE ONLY": "INTERNAL USE",
    "CONFIDENTIAL": "CONFIDENTIAL",
    "HIGHLY CONFIDENTIAL": "HIGHLY CONFIDENTIAL",
    "HIGHLY-CONFIDENTIAL": "HIGHLY CONFIDENTIAL",
    "CUI": "CUI",  # accepted but warned; see classification_note()
}

DEFAULT_LEVEL = "INTERNAL USE"
DEFAULT_MARKING = CLASSIFICATION_MARKINGS[DEFAULT_LEVEL]
DUAL_BANNER_LEVELS = {"HIGHLY CONFIDENTIAL", "CUI"}


class ClassificationError(ValueError):
    """Raised for a classification value that is not in PY-DC."""


def normalize_classification(value):
    """Canonical (level, marking) for a front-matter/CLI classification value."""
    raw = (value or DEFAULT_LEVEL)
    key = re.sub(r"\s+", " ", str(raw)).strip().upper()
    key = re.sub(r"^\(|\)$", "", key)
    if key in CLASSIFICATION_ALIASES:
        level = CLASSIFICATION_ALIASES[key]
        return level, CLASSIFICATION_MARKINGS.get(level, level)
    raise ClassificationError(
        f"classification {raw!r} is not a SoundOff data classification. "
        f"Allowed (PY-DC): {', '.join(CLASSIFICATIONS)}. "
        "'INTERNAL USE ONLY' is accepted as the marking form of INTERNAL USE."
    )


def classification_note(level):
    if level == "CUI":
        return ("classification CUI requested. SoundOff safeguards FCI under "
                "FAR 52.240-93 and holds no CUI; confirm the contract "
                "requirement before releasing this document.")
    return None


def needs_dual_banner(level):
    return level in DUAL_BANNER_LEVELS


# --------------------------------------------------------------------------- #
# Document status (controlled documents only)
# --------------------------------------------------------------------------- #
STATUS_LABELS = {
    "draft": "DRAFT · PENDING APPROVAL",
    "in review": "IN REVIEW",
    "review": "IN REVIEW",
    "approved": "APPROVED",
    "ratified": "RATIFIED",
    "retired": "RETIRED · SUPERSEDED",
}
DRAFT_STATUSES = {"draft", "in review", "review"}


def status_label(status, version=None):
    """'draft' + '1.0' -> 'v1.0 DRAFT · PENDING APPROVAL'. None if unset."""
    if not status:
        return None
    key = re.sub(r"\s+", " ", str(status)).strip().lower()
    label = STATUS_LABELS.get(key, str(status).strip().upper())
    return f"v{version} {label}" if version else label


def is_draft(status):
    return bool(status) and str(status).strip().lower() in DRAFT_STATUSES


# --------------------------------------------------------------------------- #
# Cover / metadata field order
# --------------------------------------------------------------------------- #
# One ordered list of (label, front-matter key) drives the cover metadata table
# in Word and PDF and the metadata line in Excel. `status` renders as a badge.
COVER_FIELDS = [
    ("Document ID", "doc_id"),
    ("Prepared by", "author"),
    ("Date", "date"),
    ("Version", "version"),
    ("Department", "department"),
    ("Owner", "owner"),
    ("Framework", "framework"),
    ("NIST CSF 2.0", "nist_csf"),
    ("Review Cycle", "review_cycle"),
    ("Reference", "reference"),
]


def cover_rows(meta):
    return [(label, str(meta[key])) for label, key in COVER_FIELDS
            if meta.get(key)]


# --------------------------------------------------------------------------- #
# Document identity: types, IDs, departments
# --------------------------------------------------------------------------- #
DOC_TYPE_CODES = {
    "PY": "Policy", "ST": "Standard", "PR": "Procedure", "WI": "Work Instruction",
    "PL": "Plan", "RB": "Runbook", "GD": "Guideline", "FM": "Form",
    "RG": "Register", "RP": "Report", "MM": "Memo",
}
# Types that go through approval and revision. Only these carry status,
# version history, approvals, and a review cycle.
CONTROLLED_CODES = {"PY", "ST", "PR", "WI", "PL", "RB", "GD", "FM"}
CONTROLLED_WORDS = ("policy", "standard", "procedure", "work instruction",
                    "plan", "runbook", "guideline", "form")
SEVERITY_SCALE = ("Critical", "High", "Medium", "Low")

SOS_ID_RE = re.compile(r"^SOS-([A-Z0-9]{2,})-([A-Z]{2})-([A-Z0-9]+(?:-[A-Z0-9]+)*)$")
LAYOUTS = ("report", "brief", "memo")
ORIENTATIONS = ("portrait", "landscape")


def load_departments():
    """{canonical name: {"code": str|None, "aliases": [...], "profile": str|None}}"""
    try:
        import yaml
        data = yaml.safe_load(DEPARTMENTS_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    out = {}
    for name, entry in data.items():
        entry = entry or {}
        code = entry.get("code")
        out[str(name)] = {
            "code": str(code).strip().upper() if code else None,
            "aliases": [str(a) for a in (entry.get("aliases") or [])],
            "profile": entry.get("profile"),
        }
    return out


def canonical_department(name, departments=None):
    """Registry name for a department or alias (case-insensitive), else None."""
    if not name:
        return None
    departments = departments if departments is not None else load_departments()
    key = str(name).strip().lower()
    for canon, entry in departments.items():
        if key == canon.lower() or key in (a.lower() for a in entry["aliases"]):
            return canon
    return None


def parse_doc_id(doc_id):
    """(dept_code, type_code, subject) for an SOS-form ID, else None."""
    m = SOS_ID_RE.match(str(doc_id or "").strip())
    return m.groups() if m else None


def is_controlled(meta):
    """True for documents that go through approval and revision."""
    parsed = parse_doc_id(meta.get("doc_id"))
    if parsed and parsed[1] in CONTROLLED_CODES:
        return True
    doc_type = str(meta.get("doc_type") or "").lower()
    return any(w in doc_type for w in CONTROLLED_WORDS)


def identity_findings(meta):
    """[(severity, message)] for the document's identity. severity is 'warn'
    for things that are probably wrong and 'info' for things worth knowing.

    The main job is catching a document that carries another department's code,
    which is how a non-Cybersecurity document used to end up as SOS-ITCS-...
    """
    out = []
    departments = load_departments()
    dept = meta.get("department")
    canon = canonical_department(dept, departments)
    doc_id = str(meta.get("doc_id") or "").strip()

    if doc_id.upper().startswith("SOS-"):
        parsed = parse_doc_id(doc_id)
        if not parsed:
            out.append(("warn", f"doc_id {doc_id!r} does not match "
                        "SOS-<dept code>-<type code>-<subject>"))
        else:
            code, type_code, _ = parsed
            owner = next((n for n, e in departments.items()
                          if e["code"] == code), None)
            if type_code not in DOC_TYPE_CODES:
                out.append(("warn", f"doc_id type code {type_code!r} is not one "
                            f"of {', '.join(DOC_TYPE_CODES)}"))
            if not dept:
                if owner:
                    out.append(("warn", f"doc_id uses {code}, the {owner} code, "
                                "but no department is set. Set department, or "
                                "drop the ID if this is not a "
                                f"{owner} document."))
            elif owner and (canon or str(dept).strip()) != owner:
                out.append(("warn", f"doc_id uses {code}, the {owner} code, but "
                            f"the department is {dept}. Use {dept}'s own "
                            "code, or no SOS ID if it has none."))
            elif canon and departments[canon]["code"] \
                    and departments[canon]["code"] != code:
                out.append(("warn", f"doc_id code {code} does not match "
                            f"{canon}'s registered code "
                            f"{departments[canon]['code']}"))
            elif not owner:
                out.append(("info", f"department code {code} is not in "
                            "references/departments/departments.yaml, so it "
                            "cannot be checked; register it there"))
    return out


def slug(text, maxlen=60):
    s = re.sub(r"[^A-Za-z0-9]+", "-", str(text or "")).strip("-")
    return s[:maxlen].strip("-")


def suggest_filename(meta, ext):
    """<doc_id>_<Title>_v<version>.<ext>, dropping whatever is not set."""
    parts = []
    if meta.get("doc_id"):
        parts.append(str(meta["doc_id"]).strip())
    parts.append(slug(meta.get("title") or "Untitled"))
    if meta.get("version"):
        parts.append(f"v{meta['version']}")
    return "_".join(p for p in parts if p) + "." + ext.lstrip(".")


# --------------------------------------------------------------------------- #
# Logos and fonts
# --------------------------------------------------------------------------- #
LOGOS = {
    "full_color": "soundoff-logo-full-color.png",
    "reverse_white": "soundoff-logo-reverse-white.png",
    "inverse_red_white": "soundoff-logo-inverse-red-white.png",
    "black": "soundoff-logo-black.png",
}
LOGO_ASPECT = 2.70


def logo_path(variant="full_color"):
    return LOGOS_DIR / LOGOS[variant]


def font_path(weight=400):
    return FONTS_DIR / OSWALD_WEIGHTS[weight]


# --------------------------------------------------------------------------- #
# Dependency preflight
# --------------------------------------------------------------------------- #
PIP_LINE = ("pip install --break-system-packages weasyprint pyyaml "
            "python-docx python-pptx openpyxl pillow")

_PIP_NAMES = {
    "yaml": "pyyaml", "docx": "python-docx", "pptx": "python-pptx",
    "openpyxl": "openpyxl", "weasyprint": "weasyprint", "PIL": "pillow",
}


def require(*modules):
    """Import-check on startup so a missing wheel prints the pip line."""
    import importlib
    missing = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(_PIP_NAMES.get(mod, mod))
    if missing:
        print(f"Missing Python package(s): {', '.join(missing)}\n"
              f"Install with:\n    {PIP_LINE}", file=sys.stderr)
        sys.exit(2)


# --------------------------------------------------------------------------- #
# Shared front matter / CLI plumbing
# --------------------------------------------------------------------------- #
# Every field a builder accepts, as (front-matter key, help text). CLI flags are
# the same keys with dashes. Defined once so the four builders cannot drift.
META_FIELDS = [
    ("title", "document title"),
    ("subtitle", "subtitle / secondary line"),
    ("doc_type", "label on the cover / title slide, e.g. Procedure, Report, Memo"),
    ("doc_id", "document ID, e.g. SOS-<dept code>-PR-<subject> (optional)"),
    ("author", "the person preparing the document"),
    ("department", "owning department (see departments.yaml)"),
    ("owner", "owning role or team, if different from the department"),
    ("date", "ISO date; defaults to today"),
    ("version", "version, for controlled documents"),
    ("status", "controlled documents: draft | in review | approved | "
               "ratified | retired"),
    ("review_cycle", "controlled documents: review cadence"),
    ("classification", " | ".join(CLASSIFICATIONS)),
    ("framework", "frameworks or standards the document maps to"),
    ("nist_csf", "NIST CSF 2.0 functions/categories"),
    ("reference", "related ticket, project, or source"),
    ("layout", "docx/pdf: report (cover page) | brief (title block) | memo"),
    ("orientation", "docx/pdf: portrait | landscape"),
    ("to", "memo: recipients"),
    ("from", "memo: sender (defaults to author)"),
    ("cc", "memo: copy recipients"),
    ("subject", "memo: subject line (defaults to title)"),
]


def add_common_args(parser, *, paged=False, strict=True):
    """Register --content/--output plus every shared metadata flag."""
    parser.add_argument("--content", required=True, help="Markdown content file")
    parser.add_argument("--output", required=True,
                        help="output file, or a directory to derive the name")
    for key, help_text in META_FIELDS:
        parser.add_argument("--" + key.replace("_", "-"), dest=key,
                            help=help_text)
    if paged:
        parser.add_argument("--cover", dest="cover", action="store_true",
                            default=None, help="same as --layout report")
        parser.add_argument("--no-cover", dest="cover", action="store_false",
                            help="same as --layout brief")
        parser.add_argument("--toc", action="store_true", default=None,
                            help="add a table of contents (also toc: true)")
    if strict:
        parser.add_argument("--strict", action="store_true",
                            help="treat warnings as errors (final deliverables)")
    return parser


def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def resolve_meta(meta, args, report=None):
    """Merge CLI over front matter, apply company defaults, validate.

    Returns the metadata dict with 'classification' normalized to its marking
    form plus private keys: _level, _dual_banner, _layout, _landscape, _toc.
    Exits 2 on an invalid classification. Identity problems (a doc_id carrying
    another department's code, a malformed ID) go to `report` as warnings so
    --strict catches them.
    """
    import datetime as _dt
    meta = dict(meta or {})
    for key, _ in META_FIELDS:
        val = getattr(args, key, None)
        if val is not None:
            meta[key] = val
    meta.setdefault("date", _dt.date.today().isoformat())
    if meta.get("date") is not None:
        meta["date"] = str(meta["date"])

    def _warn(msg):
        (report.warn if report else
         (lambda m: print(f"warning: {m}", file=sys.stderr)))(msg)

    def _info(msg):
        (report.info if report else
         (lambda m: print(f"note: {m}", file=sys.stderr)))(msg)

    try:
        level, marking = normalize_classification(meta.get("classification"))
    except ClassificationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    note = classification_note(level)
    if note:
        _warn(note)
    meta["classification"] = marking
    meta["_level"] = level
    meta["_dual_banner"] = needs_dual_banner(level)

    # Layout. `cover: false` (front matter or --no-cover) means brief.
    cover = getattr(args, "cover", None)
    if cover is None and "cover" in meta:
        cover = _truthy(meta["cover"])
    layout = str(meta.get("layout") or "").strip().lower()
    if not layout:
        layout = "brief" if cover is False else "report"
    if layout not in LAYOUTS:
        _warn(f"layout {layout!r} is not one of {', '.join(LAYOUTS)}; "
              "using report")
        layout = "report"
    meta["_layout"] = layout

    orientation = str(meta.get("orientation") or "portrait").strip().lower()
    if orientation not in ORIENTATIONS:
        _warn(f"orientation {orientation!r} is not portrait or landscape")
        orientation = "portrait"
    meta["_landscape"] = orientation == "landscape"

    toc = getattr(args, "toc", None)
    meta["_toc"] = bool(toc) or _truthy(meta.get("toc", False))

    if layout == "memo":
        meta.setdefault("subject", meta.get("title"))
        if meta.get("from") and not meta.get("author"):
            meta["author"] = meta["from"]
        meta.setdefault("from", meta.get("author"))

    for severity, msg in identity_findings(meta):
        (_warn if severity == "warn" else _info)(msg)
    if not meta.get("author"):
        _info("no author set; document properties will name the company")
    return meta


def resolve_output(output, meta, ext):
    """--output may name a directory; derive the filename from identity."""
    import os
    if output.endswith(("/", os.sep)) or os.path.isdir(output):
        os.makedirs(output, exist_ok=True)
        return os.path.join(output, suggest_filename(meta, ext))
    return output


def properties(meta):
    """Shared document-property values for every format."""
    keywords = [meta.get("doc_id"), meta.get("doc_type"),
                meta.get("classification"), meta.get("department"),
                meta.get("owner"), meta.get("framework"), meta.get("nist_csf")]
    comments = []
    if meta.get("doc_id"):
        comments.append(f"Document ID: {meta['doc_id']}")
    if meta.get("version"):
        comments.append(f"Version: {meta['version']}")
    if meta.get("status"):
        comments.append(f"Status: {status_label(meta['status'])}")
    comments.append(f"Classification: {meta['classification']}")
    if meta.get("review_cycle"):
        comments.append(f"Review cycle: {meta['review_cycle']}")
    return {
        "title": str(meta.get("title") or "Untitled Document"),
        "subject": str(meta.get("subtitle") or meta.get("doc_type") or ""),
        "author": str(meta.get("author") or COMPANY),
        "category": str(meta.get("doc_type") or ""),
        "keywords": "; ".join(str(k) for k in keywords if k),
        "comments": " | ".join(comments),
    }


class BuildReport:
    """Collects per-build warnings so nothing degrades silently.

    Builders add a line for every block they cannot represent; finish() prints
    the summary, honors --strict, and exits nonzero when the body came out empty.
    info() lines are printed but never fail a --strict build.
    """

    def __init__(self, fmt, strict=False):
        self.fmt = fmt
        self.strict = strict
        self.warnings = []
        self.counts = {}

    def warn(self, message):
        self.warnings.append(message)
        print(f"warning [{self.fmt}]: {message}", file=sys.stderr)

    def info(self, message):
        print(f"note [{self.fmt}]: {message}", file=sys.stderr)

    def skipped(self, kind, detail=""):
        self.counts[f"{kind} skipped"] = \
            self.counts.get(f"{kind} skipped", 0) + 1
        self.warn(f"skipped {kind}{': ' + detail if detail else ''}")

    def count(self, kind, n=1):
        self.counts[kind] = self.counts.get(kind, 0) + n

    def finish(self, output, *, empty=False):
        bits = [f"{v} {k}" for k, v in self.counts.items()]
        summary = ", ".join(bits) if bits else "no content counters"
        print(f"Wrote {output} ({summary})")
        if empty:
            print(f"error [{self.fmt}]: body rendered empty; nothing to "
                  "deliver", file=sys.stderr)
            sys.exit(1)
        if self.warnings and self.strict:
            print(f"error [{self.fmt}]: {len(self.warnings)} warning(s) and "
                  "--strict is set", file=sys.stderr)
            sys.exit(1)
