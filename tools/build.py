#!/usr/bin/env python3
"""Build the SVG faceplates used by the ApexAi GitHub profile README.

Every file in assets/ is generated here from the apexaiofficial.com design system:
graphite faceplates, expanded Archivo nameplates, Martian Mono data, signal blue for
authority paths, and amber only for planned work.

Text is drawn as vector outlines from the site's own typefaces (tools/fonts, OFL), so the
images look the same in every browser and in the GitHub mobile apps, which never load
fonts inside an <img>.

Public availability lives in AVAILABILITY below. It must match content/availability.ts on
apexaiofficial.com; change it there first, then rebuild here.

    python3 -m venv .venv
    .venv/bin/pip install -r tools/requirements.txt
    .venv/bin/python tools/build.py
"""

from __future__ import annotations

import io
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "assets"

# ---------------------------------------------------------------------------
# Tokens (apexaiofficial.com docs/DESIGN_DIRECTION.md)

VOID = "#05070a"
GROUND = "#080b0e"
PANEL = "#0c1015"
PANEL_HI = "#10161c"
SEAM = "#19202a"
SEAM_HI = "#232c37"
SEAM_LIT = "#35414e"
ROUTE = "#33414f"
TEXT = "#e8edf2"
TEXT_2 = "#a3afbb"
TEXT_3 = "#7a8794"
SIGNAL = "#72aaff"
SIGNAL_HI = "#b4d2ff"
AMBER = "#e5a352"
ROSE = "#df8a8a"

W = 880  # README column is ~846px on github.com; images scale to fit.
NW = 420  # Narrow variants, served below 640px through <picture>; phones show them at ~0.85x.
NEDGE = 30  # Narrow text edge: 14px inset margin + 16px cell padding.
NIN = 14
EDGE = 44  # Shared left text edge: 24px inset margin + 20px cell padding.

# ---------------------------------------------------------------------------
# Public availability (mirror of apexaiofficial.com content/availability.ts)

STATES = {
    "IN_DEVELOPMENT": ("In development", SIGNAL_HI, "rgba(114,170,255,.45)", SIGNAL, "solid"),
    "PLANNED": ("Planned", "#f2cf9f", "rgba(229,163,82,.55)", AMBER, "dashed"),
    "NOT_PUBLICLY_HOSTED": ("Not publicly hosted", "#efc0c0", "rgba(223,138,138,.42)", ROSE, "ring"),
}

STATE_MEANING = {
    "IN_DEVELOPMENT": "Implemented in current development source; not generally released.",
    "PLANNED": "Part of the product direction; not built yet.",
    "NOT_PUBLICLY_HOSTED": "No public managed service, sign-up, or endpoint.",
}

SURFACES = ["Telegram operator", "Web Admin", "ApexAPI", "ApexMCP", "Product plugin", "Hosted service"]

AVAILABILITY = {
    "Scrapy": {
        "Telegram operator": "IN_DEVELOPMENT",
        "Web Admin": None,  # Scrapy has no Web Admin surface.
        "ApexAPI": "IN_DEVELOPMENT",
        "ApexMCP": "IN_DEVELOPMENT",
        "Product plugin": "IN_DEVELOPMENT",
        "Hosted service": "NOT_PUBLICLY_HOSTED",
    },
    "Communications": {
        "Telegram operator": "IN_DEVELOPMENT",
        "Web Admin": "IN_DEVELOPMENT",
        "ApexAPI": "IN_DEVELOPMENT",
        "ApexMCP": "PLANNED",
        "Product plugin": "PLANNED",
        "Hosted service": "NOT_PUBLICLY_HOSTED",
    },
}

# ---------------------------------------------------------------------------
# Content (apexaiofficial.com content/products.ts, plugins.ts, custom-orders.ts)

PRODUCTS = [
    {
        "slug": "scrapy",
        "name": "Scrapy",
        "code": "DATA",
        "category": "Web-data operations",
        "thesis": "Turn web sources into owned artifacts and versioned datasets.",
        "job": "Collect web content reliably and keep what was collected: the files, the records, and the evidence of how they were produced.",
        "workflow": "Source to dataset",
        "steps": [
            "Choose a cataloged source",
            "Pass the policy and egress gate",
            "Crawl, fetch, or render",
            "Classify and store artifacts",
            "Publish a dataset version",
            "Search and fetch records",
        ],
        "gate": 1,
        "capabilities": [
            "Multi-engine execution",
            "Browser rendering",
            "Artifacts and media",
            "Jobs and evidence",
            "Versioned datasets",
            "Your proxies, explicit egress",
        ],
        "execution": ["crawl · fetch", "render · extract"],
        "evidence": ["artifacts", "dataset versions"],
    },
    {
        "slug": "communications",
        "name": "Communications",
        "code": "COMMS",
        "category": "Business communications",
        "thesis": "Business communications on your own provider accounts, with consent and history built in.",
        "job": "Reach customers on the right channel, with permission, and know afterward exactly what was sent, what came back, and why each send was allowed.",
        "workflow": "Intent to evidence",
        "steps": [
            "Communication intent",
            "Workspace and role",
            "Consent and suppression",
            "Trust and Safety gate",
            "Workspace provider",
            "Delivery and history",
        ],
        "gate": 3,
        "capabilities": [
            "Five channels, distinct contracts",
            "Bring your own providers",
            "Consent and suppression",
            "Templates and automation",
            "History and audit",
            "Trust, safety, and credits",
        ],
        "execution": ["SMS · WhatsApp", "voice · email", "Telegram"],
        "evidence": ["delivery state", "history · audit"],
    },
]

HERO_LEDE = ("Two products that do real operating work, for the people who operate them, the software that "
             "integrates with them, and the AI agents that act through them.")
HERO_RULE = "Each product owns its gate: every caller passes the same product policy."

HEADS = {
    "availability": ("Public availability", "Opening for business soon.",
                     "Scrapy and Communications are real products in active development. Sign-up, hosted access, "
                     "and pricing open at launch."),
    "access": ("Access layers", "Software and agents reach the same product.",
               "Every caller reaches the product's own core, so adding a caller never adds a way around its "
               "rules. Each product ships its own contracts; there is no shared gateway."),
    "custom": ("Custom orders", "Bespoke software, scoped before it is built.",
               "Bots, integrations, automation, and agent tooling close to what ApexAi already builds in "
               "Scrapy and Communications. Each request is scoped individually and quoted after scope is agreed."),
    "open": ("Open source", "Guides, kits, and tools you can use today.", None),
}
CUSTOM_NOTE = "ApexAi declines work that depends on bypassing consent, platform rules, access controls, or the law."
FOOTER_LINES = ("Web-data and business communications products for operators, software, and AI agents.",
                "Designed and built independently by Logan P.")

CALLERS = [
    ("Operator", "Telegram · Web Admin"),
    ("ApexAPI", "software · typed HTTP"),
    ("ApexMCP", "agents · MCP tools"),
]
# (caller index, product index) routes that are planned rather than in the product.
PLANNED_ROUTES = {(2, 1)}

ACCESS = [
    {
        "name": "ApexAPI",
        "caller": "HTTP · software",
        "body": "Typed HTTP for applications that submit work, send communications, and read results and history.",
        "specimen": [("Scrapy", ["POST /v1/scrape/crawl"]), ("Communications", ["POST /api/v1/communications"])],
    },
    {
        "name": "ApexMCP",
        "caller": "MCP · agents",
        "body": "Tools and resources that let agents discover, inspect, retrieve, and take named actions inside a product.",
        "specimen": [("Scrapy tool", ["apex_scrapy_start_crawl"]), ("Scrapy resource", ["apex-scrapy://datasets"])],
    },
    {
        "name": "Product plugins",
        "caller": "operators · control",
        "body": "Keep a deployment healthy, verified, and correctable, with approvals and evidence for every step.",
        "specimen": [("Capability families", ["observe · verify", "control · record"])],
    },
]

FIT_AREAS = [
    ("MSG", "Telegram and messaging", ["Telegram bots", "Telegram Business workflows", "WhatsApp integrations"]),
    ("COM", "Communications automation", ["Twilio integrations", "Email and provider integrations", "Notification and follow-up flows"]),
    ("WEB", "Web data", ["Scraping and crawling systems", "Extraction pipelines", "Monitoring and change detection"]),
    ("INT", "Integrations and APIs", ["API integrations", "Connecting existing services", "Webhooks and data sync"]),
    ("AGT", "Agents and AI tooling", ["MCP servers and agent integrations", "AI-assisted operator tooling", "Structured AI workflows"]),
    ("OPS", "Operations and control", ["Admin and control surfaces", "Business process automation", "Extensions to Scrapy or Communications"]),
]

REPOS = [
    ("privacy-chain", "Guide", "CC BY 4.0",
     "How online identity leaks across devices, networks, browsers, and accounts, and the controls that reduce it."),
    ("telegram-bot-tutorial", "Tutorial", "Python · MIT",
     "Build a Telegram bot in Python from zero to deployed, with a runnable example at every stage."),
    ("termux-kit", "Kit", "Shell · MIT",
     "Turn Android Termux into a practical workbench: local services, a dev stack, helper scripts, and safe backups."),
    ("termux-telegram-bot", "Kit", "Shell · MIT",
     "Deploy and operate one Python Telegram bot on Android Termux, with strict token safety."),
    ("cookie-manager", "CLI", "Python",
     "Inspect, export, and replay browser cookies you control, with redacted values and correctly scoped replay."),
]

# ---------------------------------------------------------------------------
# Type: HarfBuzz shaping, outlines emitted once per document as <defs> and reused.


class Face:
    def __init__(self, filename: str):
        tt = TTFont(FONTS / filename)
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        self.face = hb.Face(buf.getvalue())
        self.upem = self.face.upem
        self._fonts: dict[tuple, hb.Font] = {}

    def font(self, wght: float, wdth: float) -> hb.Font:
        key = (wght, wdth)
        if key not in self._fonts:
            font = hb.Font(self.face)
            font.set_variations({"wght": wght, "wdth": wdth})
            self._fonts[key] = font
        return self._fonts[key]


FACES = {"sans": Face("archivo-variable-latin.woff2"), "mono": Face("martian-mono-variable-latin.woff2")}


class PathPen:
    """Collects a glyph outline as SVG path data, flipped to y-down, in font units."""

    def __init__(self):
        self.d: list[str] = []

    @staticmethod
    def _p(pt):
        return f"{round(pt[0])} {round(-pt[1])}"

    def moveTo(self, p):
        self.d.append("M" + self._p(p))

    def lineTo(self, p):
        self.d.append("L" + self._p(p))

    def qCurveTo(self, *pts):
        # HarfBuzz emits one off-curve point per call.
        self.d.append("Q" + " ".join(self._p(p) for p in pts))

    def curveTo(self, *pts):
        self.d.append("C" + " ".join(self._p(p) for p in pts))

    def closePath(self):
        self.d.append("Z")

    def endPath(self):
        pass


def shape(text: str, face: str, wght: float, wdth: float):
    f = FACES[face].font(wght, wdth)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(f, buf, {"kern": True, "liga": True})
    return f, buf.glyph_infos, buf.glyph_positions


def measure(text: str, size: float, face: str = "sans", wght: float = 400, wdth: float = 100, track: float = 0.0) -> float:
    _, infos, positions = shape(text, face, wght, wdth)
    upem = FACES[face].upem
    advance = sum(p.x_advance for p in positions)
    return (advance + track * upem * max(len(infos) - 1, 0)) * size / upem


def wrap(text: str, width: float, size: float, **style) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and measure(candidate, size, **style) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def fit(text: str, width: float, largest: float, **style) -> float:
    """Largest size (<= `largest`) at which `text` fits in `width`."""
    return min(largest, largest * width / measure(text, largest, **style))


# ---------------------------------------------------------------------------
# Documents


class Doc:
    def __init__(self, width: float, height: float, title: str, desc: str = ""):
        self.w, self.h = width, height
        self.title, self.desc = title, desc
        self.defs: list[str] = []
        self.glyphs: dict[tuple, str] = {}
        self.body: list[str] = []
        self.style = ""

    def add(self, *parts: str):
        self.body.extend(parts)

    def _glyph(self, face: str, font: hb.Font, wght, wdth, gid: int) -> str | None:
        key = (face, wght, wdth, gid)
        if key not in self.glyphs:
            pen = PathPen()
            font.draw_glyph_with_pen(gid, pen)
            if not pen.d:
                self.glyphs[key] = ""
            else:
                ident = f"g{len(self.glyphs)}"
                self.glyphs[key] = ident
                self.defs.append(f'<path id="{ident}" d="{"".join(pen.d)}"/>')
        return self.glyphs[key] or None

    def text(self, s: str, x: float, y: float, size: float, *, face: str = "sans", wght: float = 400,
             wdth: float = 100, track: float = 0.0, fill: str = TEXT, anchor: str = "start", extra: str = "") -> float:
        """Draw one line of text with its baseline at y. Returns the drawn width in px."""
        font, infos, positions = shape(s, face, wght, wdth)
        upem = FACES[face].upem
        width = measure(s, size, face, wght, wdth, track)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        uses, pen_x = [], 0.0
        for info, pos in zip(infos, positions):
            ident = self._glyph(face, font, wght, wdth, info.codepoint)
            if ident:
                gx = pen_x + pos.x_offset
                gy = -pos.y_offset
                uses.append(f'<use xlink:href="#{ident}" x="{gx:.0f}"' + (f' y="{gy:.0f}"' if gy else "") + "/>")
            pen_x += pos.x_advance + track * upem
        scale = size / upem
        self.body.append(
            f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f})" fill="{fill}"{extra}>' + "".join(uses) + "</g>"
        )
        return width

    def lines(self, lines: list[str], x: float, y: float, size: float, leading: float, **style) -> float:
        """Draw consecutive lines; returns the baseline of the last one."""
        for i, line in enumerate(lines):
            self.text(line, x, y + i * leading, size, **style)
        return y + (len(lines) - 1) * leading

    def render(self) -> str:
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.w:g}" height="{self.h:g}" viewBox="0 0 {self.w:g} {self.h:g}" '
            f'role="img" aria-labelledby="t d">'
        )
        parts = [head, f'<title id="t">{esc(self.title)}</title>', f'<desc id="d">{esc(self.desc or self.title)}</desc>']
        if self.style:
            parts.append(f"<style>{self.style}</style>")
        parts.append("<defs>" + "".join(self.defs) + "</defs>")
        parts.extend(self.body)
        parts.append("</svg>")
        return "".join(parts) + "\n"

    def save(self, name: str):
        (OUT / name).write_text(self.render(), encoding="utf-8")
        print(f"assets/{name}  {self.w:g}x{self.h:g}  {len(self.render()) / 1024:.1f} KB")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Shared components


def legend(doc: Doc, s: str, x: float, y: float, fill: str = TEXT_3, size: float = 11, anchor: str = "start") -> float:
    """Engraved faceplate legend: fully expanded caps. The brand keeps its casing."""
    return doc.text(s.upper(), x, y, size, wght=620, wdth=125, track=0.15, fill=fill, anchor=anchor)


def plate(doc: Doc, fill: str = PANEL, glow: tuple[float, float] | None = None, radius: float = 14):
    w, h = doc.w, doc.h
    doc.add(f'<rect x=".5" y=".5" width="{w - 1:g}" height="{h - 1:g}" rx="{radius}" fill="{fill}" stroke="{SEAM_HI}"/>')
    if glow:
        doc.defs.append(
            f'<radialGradient id="glow" gradientUnits="userSpaceOnUse" cx="{glow[0]:g}" cy="{glow[1]:g}" r="{max(w, h) * .62:g}">'
            f'<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".13"/><stop offset=".55" stop-color="{SIGNAL}" stop-opacity=".03"/>'
            f'<stop offset="1" stop-color="{SIGNAL}" stop-opacity="0"/></radialGradient>'
        )
        doc.add(f'<rect x="1" y="1" width="{w - 2:g}" height="{h - 2:g}" rx="{radius - .5}" fill="url(#glow)"/>')
    # Faint machined top highlight.
    doc.add(f'<path d="M{radius} 1.5H{w - radius}" stroke="#fff" stroke-opacity=".06"/>')


def brand_mark(doc: Doc, x: float, y: float, size: float, stroke: float = 2.2):
    s = size / 24
    doc.add(
        f'<g transform="translate({x:g} {y:g}) scale({s:.4f})" fill="none" stroke-width="{stroke}">'
        f'<path d="M4.4 20.6 12 3.4l7.6 17.2" stroke="{TEXT}" stroke-linejoin="miter" stroke-miterlimit="12"/>'
        f'<path d="M4.9 14.6h14.2" stroke="{SIGNAL}"/></g>'
    )


def ext_arrow(doc: Doc, x: float, y: float, size: float, color: str):
    """North-east arrow (↗) for links that leave GitHub. (x, y) is the bottom-left corner."""
    doc.add(
        f'<path d="M{x:.1f} {y:.1f}L{x + size:.1f} {y - size:.1f}M{x + size * .3:.1f} {y - size:.1f}H{x + size:.1f}V{y - size * .7:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def badge(doc: Doc, code: str, x: float, cy: float, size: float = 9.5) -> float:
    label, fg, border, lamp, kind = STATES[code]
    text = label.upper()
    tw = measure(text, size, wght=640, wdth=118, track=0.1)
    h, pad_l, lamp_gap, pad_r = 22, 9, 8, 9
    w = pad_l + 6 + lamp_gap + tw + pad_r
    dash = ' stroke-dasharray="3 3"' if kind == "dashed" else ""
    doc.add(f'<rect x="{x + .5:.1f}" y="{cy - h / 2 + .5:.1f}" width="{w - 1:.1f}" height="{h - 1}" rx="4" fill="#000" fill-opacity=".3" stroke="{border}"{dash}/>')
    lx = x + pad_l + 3
    if kind == "solid":
        doc.add(f'<circle cx="{lx:.1f}" cy="{cy:.1f}" r="5" fill="{lamp}" fill-opacity=".18"/><circle cx="{lx:.1f}" cy="{cy:.1f}" r="3" fill="{lamp}"/>')
    else:
        doc.add(f'<circle cx="{lx:.1f}" cy="{cy:.1f}" r="2.6" fill="none" stroke="{lamp}" stroke-width="1.1"/>')
    doc.text(text, x + pad_l + 6 + lamp_gap, cy + size * .36, size, wght=640, wdth=118, track=0.1, fill=fg)
    return w


def hline(doc: Doc, x1: float, x2: float, y: float, color: str = SEAM):
    doc.add(f'<path d="M{x1:g} {y + .5:g}H{x2:g}" stroke="{color}"/>')


def vline(doc: Doc, x: float, y1: float, y2: float, color: str = SEAM):
    doc.add(f'<path d="M{x + .5:g} {y1:g}V{y2:g}" stroke="{color}"/>')


def inset(doc: Doc, x: float, y: float, w: float, h: float, fill: str = GROUND, radius: float = 10):
    doc.add(f'<rect x="{x + .5:g}" y="{y + .5:g}" width="{w - 1:g}" height="{h - 1:g}" rx="{radius}" fill="{fill}" stroke="{SEAM_HI}"/>')


def section_head(doc: Doc, key: str, y: float = 52, edge: float = EDGE, size: float = 30, body: float = 15) -> float:
    """Legend, statement, and optional lede at the top of a plate. Returns the last baseline."""
    code, title, lede = HEADS[key]
    width = min(700, doc.w - 2 * edge)
    legend(doc, code, edge, y, size=11 if size >= 30 else 10)
    y += 16 + size
    y = doc.lines(wrap(title, width, size, wght=560, wdth=112, track=-0.032), edge - 2, y, size, size * 1.12,
                  wght=560, wdth=112, track=-0.032)
    if lede:
        y = doc.lines(wrap(lede, width, body), edge, y + body * 2.25, body, body * 1.55, fill=TEXT_2)
    return y


# ---------------------------------------------------------------------------
# Assets


def hero():
    doc = Doc(W, 0, "ApexAi: web data and business communications",
              "ApexAi builds Scrapy and Communications. Operators, software through ApexAPI, and AI agents through "
              "ApexMCP reach each product through its own authority gate. Opening for business soon.")

    # Top bar: mark and wordmark, launch state.
    brand_mark(doc, EDGE - 5, 20, 26)
    doc.text("ApexAi", EDGE + 32, 40, 19, wght=640, wdth=118, track=-0.012)
    state_w = legend(doc, "Opening soon", W - EDGE, 38, fill=AMBER, anchor="end")
    lx = W - EDGE - state_w - 16
    doc.add(f'<circle cx="{lx:.1f}" cy="34" r="7" fill="{AMBER}" fill-opacity=".12"/>'
            f'<circle cx="{lx:.1f}" cy="34" r="4" fill="none" stroke="{AMBER}" stroke-width="1.5"/>')

    # Statement.
    head = ["Web data and business", "communications."]
    size = min(fit(head[0], 800, 64, wght=560, wdth=112, track=-0.042), 64)
    y = 88 + size
    for i, line in enumerate(head):
        doc.text(line, EDGE - 4, y + i * size * 1.0, size, wght=560, wdth=112, track=-0.042)
    y += size * 1.0
    y = doc.lines(wrap(HERO_LEDE, 640, 17), EDGE, y + 46, 17, 26, fill=TEXT_2)

    # Authority Path.
    px, py, pw = 24, y + 34, W - 48
    cols = {"caller": 24, "route": 214, "gate": 332, "product": 358, "exec": 580, "evidence": 716, "end": 856}
    header_h, row_c, row_p, foot_h = 36, 74, 111, 46
    body_h = row_c * 3
    ph = header_h + body_h + foot_h
    inset(doc, px, py, pw, ph)

    # Column heads.
    hy = py + 23
    for key, label in [("caller", "Caller"), ("route", "Route"), ("product", "Product gate"), ("exec", "Execution"), ("evidence", "Evidence")]:
        legend(doc, label, cols[key] + (20 if key != "route" else 18) - (26 if key == "product" else 0), hy, size=9.5)
    by = py + header_h
    hline(doc, px + 1, px + pw - 1, by - 1)
    for key in ("route", "gate", "exec", "evidence"):
        vline(doc, cols[key], by, by + body_h)
    vline(doc, cols["product"], by, by + body_h, SEAM)

    # Route field grid.
    doc.defs.append(
        '<pattern id="grid" width="18" height="18" patternUnits="userSpaceOnUse">'
        f'<path d="M18 0H0V18" fill="none" stroke="{SIGNAL}" stroke-opacity=".06"/></pattern>'
    )
    doc.add(f'<rect x="{cols["route"] + 1}" y="{by}" width="{cols["gate"] - cols["route"] - 1}" height="{body_h}" fill="url(#grid)"/>')

    # Callers.
    jacks = []
    for i, (name, via) in enumerate(CALLERS):
        cy = by + row_c * i + row_c / 2
        if i:
            hline(doc, cols["caller"] + 1, cols["route"], by + row_c * i - 1)
        doc.text(name, cols["caller"] + 20, cy - 2, 17, wght=600, wdth=114, track=-0.015)
        doc.text(via, cols["caller"] + 20, cy + 17, 10.5, face="mono", wdth=88, fill=TEXT_3)
        jacks.append((cols["route"], cy))

    # Products and their gates.
    sockets = {}
    for j, product in enumerate(PRODUCTS):
        top = by + row_p * j
        if j:
            hline(doc, cols["gate"], px + pw - 1, top - 1, SEAM_HI)
        # Gate strip.
        doc.add(f'<rect x="{cols["gate"] + 1}" y="{top + (1 if j else 0)}" width="{cols["product"] - cols["gate"] - 1}" '
                f'height="{row_p - 1}" fill="#fff" fill-opacity=".022"/>')
        gx = (cols["gate"] + cols["product"]) / 2
        doc.add(f'<rect class="gate" x="{gx - 1:.1f}" y="{top + 14}" width="2" height="{row_p - 28}" rx="1" fill="{SIGNAL}"/>')
        doc.add(f'<rect class="gate-glow" x="{gx - 4:.1f}" y="{top + 14}" width="8" height="{row_p - 28}" rx="4" fill="{SIGNAL}" fill-opacity=".16"/>')
        for k in range(3):
            sockets[(k, j)] = (cols["gate"], top + row_p * (2 * k + 1) / 6)
        # Nameplate.
        cx = cols["product"] + 20
        tag_w = measure(product["code"], 9, wght=640, wdth=118, track=0.1) + 14
        doc.add(f'<rect x="{cx + .5}" y="{top + 17.5}" width="{tag_w:.1f}" height="18" rx="3" fill="none" stroke="{SEAM_LIT}"/>')
        doc.text(product["code"], cx + 7, top + 30, 9, wght=640, wdth=118, track=0.1, fill=TEXT_2)
        name_size = fit("Communications", cols["exec"] - cols["product"] - 40, 26, wght=600, wdth=114, track=-0.02)
        doc.text(product["name"], cx, top + 66, name_size, wght=600, wdth=114, track=-0.02)
        doc.text(product["category"], cx, top + 88, 12, fill=TEXT_2)
        for key in ("execution", "evidence"):
            col = cols["exec" if key == "execution" else "evidence"]
            lines = product[key]
            start = top + row_p / 2 - (len(lines) - 1) * 9 + 4
            doc.lines(lines, col + 20, start, 10.5, 18, face="mono", wdth=88, fill=TEXT_2)

    # Routes: caller jack -> product socket. Planned routes are dashed amber.
    routes, pulses = [], []
    for i, (jx, jy) in enumerate(jacks):
        for j in range(len(PRODUCTS)):
            sx, sy = sockets[(i, j)]
            x1, x2 = jx + 6, sx - 6
            mid = (x1 + x2) / 2
            d = f"M{x1:.1f} {jy:.1f}C{mid:.1f} {jy:.1f} {mid:.1f} {sy:.1f} {x2:.1f} {sy:.1f}"
            if (i, j) in PLANNED_ROUTES:
                routes.append(f'<path d="{d}" fill="none" stroke="{AMBER}" stroke-opacity=".6" stroke-width="1.5" stroke-dasharray="3 5"/>')
            else:
                routes.append(f'<path d="{d}" fill="none" stroke="{ROUTE}" stroke-width="1.5"/>')
                pulses.append(f'<path class="pulse p{i}" d="{d}" pathLength="100"/>')
    doc.add(*routes, *pulses)
    for jx, jy in jacks:
        doc.add(f'<circle cx="{jx}" cy="{jy:.1f}" r="5.5" fill="{PANEL}" stroke="{SEAM_LIT}" stroke-width="1.5"/>')
    for (i, j), (sx, sy) in sockets.items():
        planned = (i, j) in PLANNED_ROUTES
        stroke = f'stroke="{AMBER}" stroke-opacity=".7" stroke-dasharray="2 2"' if planned else f'stroke="{SEAM_LIT}"'
        doc.add(f'<circle cx="{sx}" cy="{sy:.1f}" r="5" fill="{PANEL}" {stroke} stroke-width="1.5"/>')

    # Footer: the rule and the key.
    fy = by + body_h
    hline(doc, px + 1, px + pw - 1, fy)
    doc.text(HERO_RULE, px + 20, fy + 28, 12.5, fill=TEXT_2)
    kx = px + pw - 20
    w = doc.text("planned", kx, fy + 27.5, 10, face="mono", wdth=88, fill=TEXT_3, anchor="end")
    doc.add(f'<path d="M{kx - w - 30:.1f} {fy + 24.5}h20" stroke="{AMBER}" stroke-opacity=".8" stroke-width="1.5" stroke-dasharray="3 3"/>')
    kx -= w + 46
    w = doc.text("in the product", kx, fy + 27.5, 10, face="mono", wdth=88, fill=TEXT_3, anchor="end")
    doc.add(f'<path d="M{kx - w - 30:.1f} {fy + 24.5}h20" stroke="{SIGNAL}" stroke-width="1.5"/>')

    doc.h = py + ph + 24
    finish(doc, fill="#06090c", glow=(W * .2, 0))

    # One orchestrated moment: a single pulse per live route, then the gates light.
    doc.style = (
        f".pulse{{fill:none;stroke:{SIGNAL_HI};stroke-width:2.5;stroke-linecap:round;stroke-dasharray:9 200;stroke-dashoffset:9}}"
        ".pulse{animation:run 1.15s cubic-bezier(.2,.7,.2,1) both}"
        ".p0{animation-delay:.5s}.p1{animation-delay:.68s}.p2{animation-delay:.86s}"
        "@keyframes run{from{stroke-dashoffset:9}to{stroke-dashoffset:-100}}"
        ".gate,.gate-glow{animation:lit .5s ease-out 1.55s both}"
        f"@keyframes lit{{from{{fill:{SEAM_LIT};fill-opacity:1}}}}"
        "@media (prefers-reduced-motion:reduce){.pulse{animation:none;display:none}.gate,.gate-glow{animation:none}}"
    )
    doc.save("hero.svg")


def button(name: str, label: str, primary: bool):
    size, h = 14, 42
    tw = measure(label, size, wght=600, wdth=106, track=-0.005)
    w = round(18 + tw + 12 + 10 + 18)
    doc = Doc(w, h, label)
    if primary:
        doc.defs.append('<linearGradient id="metal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f5f8fa"/><stop offset="1" stop-color="#dde3e9"/></linearGradient>')
        doc.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="7" fill="url(#metal)" stroke="#c9d1d9"/>',
                f'<path d="M7 1.5H{w - 7}" stroke="#fff" stroke-opacity=".9"/>')
        color = VOID
    else:
        doc.defs.append('<linearGradient id="dark" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a222b"/><stop offset="1" stop-color="#121920"/></linearGradient>')
        doc.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="7" fill="url(#dark)" stroke="{SEAM_LIT}"/>',
                f'<path d="M7 1.5H{w - 7}" stroke="#fff" stroke-opacity=".07"/>')
        color = TEXT
    doc.text(label, 18, h / 2 + 5, size, wght=600, wdth=106, track=-0.005, fill=color)
    ext_arrow(doc, 18 + tw + 12, h / 2 + 4.5, 8.5, color)
    doc.save(f"button-{name}.svg")


def product_plate(product: dict):
    doc = Doc(W, 0, f"{product['name']}: {product['category'].lower()}",
              f"{product['thesis']} {product['job']} Workflow: " + ", then ".join(product["steps"]) + ".")
    n = len(product["steps"])
    cw = (W - 48) / n  # rail station width; the plate's columns snap to it
    legend(doc, f"{product['code']} · {product['category']}", EDGE, 52)
    doc.text(product["name"], EDGE - 7, 132, 76, wght=560, wdth=125, track=-0.042)

    y = 184
    half = cw * 3 - 40
    left = doc.lines(wrap(product["thesis"], half, 19, wght=450), EDGE, y, 19, 27, wght=450)
    right = doc.lines(wrap(product["job"], half, 14.5), 24 + cw * 3 + 20, y - 2, 14.5, 22.5, fill=TEXT_2)
    y = max(left, right) + 50

    # Stage rail: the product's workflow, in order, with its authority gate marked.
    legend(doc, product["workflow"], EDGE, y)
    ry = y + 18
    titles = [wrap(step, cw - 36, 13.5, wght=600, wdth=104) for step in product["steps"]]
    rh = 68 + 19 * (max(len(t) for t in titles) - 1) + 24
    inset(doc, 24, ry, W - 48, rh)
    doc.defs.append(
        '<linearGradient id="gatewash" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".09"/><stop offset=".75" stop-color="{SIGNAL}" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="lead" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{SIGNAL}"/><stop offset="1" stop-color="{SEAM_LIT}"/></linearGradient>'
    )
    rail_y = ry + 40
    for i, lines in enumerate(titles):
        x = 24 + cw * i
        if i == product["gate"]:
            doc.add(f'<rect x="{x + 1:.1f}" y="{ry + 1}" width="{cw - 1:.1f}" height="{rh - 2}" fill="url(#gatewash)"/>')
        if i:
            vline(doc, x, ry + 1, ry + rh - 1)
        doc.text(f"{i + 1:02d}", x + 20, ry + 24, 10, face="mono", wdth=88, fill=TEXT_3)
        seg = f'M{x + (25 if i == 0 else 1):.1f} {rail_y + .5}H{x + cw:.1f}'
        doc.add(f'<path d="{seg}" stroke="{"url(#lead)" if i == 0 else SEAM_LIT}"/>')
        nx = x + 25
        if i == product["gate"]:
            doc.add(f'<rect x="{nx - 6:.1f}" y="{rail_y - 10}" width="12" height="21" rx="3" fill="{SIGNAL}" fill-opacity=".16"/>'
                    f'<rect x="{nx - 2:.1f}" y="{rail_y - 8}" width="4" height="17" rx="2" fill="{SIGNAL}"/>')
            tag = "AUTHORITY"
            tw = measure(tag, 8, wght=640, wdth=118, track=0.1)
            tx = x + cw - 14 - tw - 10
            doc.add(f'<rect x="{tx + .5:.1f}" y="{ry + 12.5}" width="{tw + 10:.1f}" height="16" rx="3" fill="none" stroke="{SIGNAL}" stroke-opacity=".5"/>')
            doc.text(tag, tx + 5, ry + 23.5, 8, wght=640, wdth=118, track=0.1, fill=SIGNAL)
        elif i == 0:
            doc.add(f'<circle cx="{nx:.1f}" cy="{rail_y + .5}" r="9" fill="{SIGNAL}" fill-opacity=".14"/>'
                    f'<circle cx="{nx:.1f}" cy="{rail_y + .5}" r="5.5" fill="{SIGNAL}"/>')
        else:
            doc.add(f'<circle cx="{nx:.1f}" cy="{rail_y + .5}" r="5" fill="{GROUND}" stroke="{SIGNAL}" stroke-width="1.5"/>')
        doc.lines(lines, x + 20, ry + 70, 13.5, 19, wght=600, wdth=104)

    # Capabilities: a quiet grid aligned to pairs of rail stations.
    caps = product["capabilities"]
    top = ry + rh + 34
    for i, cap in enumerate(caps):
        x = 24 + cw * 2 * (i % 3)
        y = top + 26 * (i // 3)
        doc.add(f'<path d="M{x + 20.5:.1f} {y - 10}v13" stroke="{SEAM_LIT}"/>')
        doc.text(cap, x + 30, y, 12.5, fill=TEXT_2)
        assert measure(cap, 12.5) < cw * 2 - 40, cap
    doc.h = top + 26 * ((len(caps) - 1) // 3) + 34
    finish(doc)
    doc.save(f"{product['slug']}.svg")


def finish(doc: Doc, **kw):
    """Draw the plate behind everything once the document height is known."""
    doc.h = round(doc.h)
    plate_doc = Doc(doc.w, doc.h, "")
    plate(plate_doc, **kw)
    doc.body.insert(0, "".join(plate_doc.body))
    doc.defs.extend(plate_doc.defs)


def availability():
    rows = []
    for surface in SURFACES:
        cells = [AVAILABILITY[p["name"]][surface] for p in PRODUCTS]
        rows.append(f"{surface}: " + ", ".join(
            f"{p['name']} {STATES[c][0].lower() if c else 'not a surface'}" for p, c in zip(PRODUCTS, cells)))
    doc = Doc(W, 0, "Public availability of ApexAi products", ". ".join(rows) + ".")
    y = section_head(doc, "availability")
    ty = y + 34
    col = [24, 300, 578, 856]
    head_h, row_h = 46, 42
    th = head_h + row_h * len(SURFACES)
    inset(doc, 24, ty, W - 48, th, fill=GROUND)
    legend(doc, "Surface", col[0] + 20, ty + 28, size=9.5)
    for k, product in enumerate(PRODUCTS):
        doc.text(product["name"], col[k + 1] + 20, ty + 29, 15, wght=600, wdth=114, track=-0.015)
        vline(doc, col[k + 1], ty + 1, ty + th - 1)
    for r, surface in enumerate(SURFACES):
        top = ty + head_h + row_h * r
        hline(doc, 25, W - 25, top - 1, SEAM if r else SEAM_HI)
        cy = top + row_h / 2
        doc.text(surface, col[0] + 20, cy + 5, 14, wght=500)
        for k, product in enumerate(PRODUCTS):
            code = AVAILABILITY[product["name"]][surface]
            if code:
                badge(doc, code, col[k + 1] + 20, cy)
            else:
                doc.text("No such surface", col[k + 1] + 20, cy + 4, 10.5, face="mono", wdth=88, fill=TEXT_3)

    # Key: what each state means.
    y = ty + th + 36
    kw = (W - 48) / 3
    bottom = y
    for k, code in enumerate(STATES):
        x = EDGE + kw * k
        badge(doc, code, x, y)
        bottom = max(bottom, doc.lines(wrap(STATE_MEANING[code], kw - 26, 12.5), x, y + 32, 12.5, 19, fill=TEXT_2))
    doc.h = bottom + 34
    finish(doc)
    doc.save("availability.svg")


def access():
    doc = Doc(W, 0, "ApexAi access layers: ApexAPI, ApexMCP, and product plugins",
              " ".join(f"{a['name']} ({a['caller']}): {a['body']}" for a in ACCESS)
              + " Each product ships its own contracts; there is no shared gateway across products.")
    y = section_head(doc, "access")
    ty = y + 34
    cw = (W - 48) / 3
    name_size = min(fit(a["name"], cw - 40, 24, wght=600, wdth=118, track=-0.02) for a in ACCESS)
    bodies = [wrap(a["body"], cw - 40, 13.5) for a in ACCESS]
    body_h = 19.5 * max(len(b) for b in bodies)
    th = 96 + body_h + 30 + 2 * 44 + 8
    inset(doc, 24, ty, W - 48, th, fill=GROUND)
    for k, layer in enumerate(ACCESS):
        x = 24 + cw * k
        if k:
            vline(doc, x, ty + 1, ty + th - 1)
        doc.text(layer["name"], x + 20, ty + 48, name_size, wght=600, wdth=118, track=-0.02)
        doc.text(layer["caller"], x + 20, ty + 72, 10.5, face="mono", wdth=88, fill=TEXT_3)
        doc.lines(bodies[k], x + 20, ty + 104, 13.5, 19.5, fill=TEXT_2)
        sy = ty + 96 + body_h + 30
        hline(doc, x + 20, x + cw - 20, sy - 14, SEAM)
        for label, values in layer["specimen"]:
            legend(doc, label, x + 20, sy + 4, size=8.5)
            sy = doc.lines(values, x + 20, sy + 24, 11, 20, face="mono", wdth=88, fill=TEXT) + 20
    doc.h = ty + th + 24
    finish(doc)
    doc.save("access.svg")


def custom_orders():
    doc = Doc(W, 0, "ApexAi custom orders",
              "Bespoke software, scoped before it is built. "
              + " ".join(f"{title}: {', '.join(ex)}." for _, title, ex in FIT_AREAS)
              + " Each request is scoped individually and quoted after scope is agreed.")
    y = section_head(doc, "custom")
    ty = y + 34
    cw, ch = (W - 48) / 3, 150
    th = ch * 2
    inset(doc, 24, ty, W - 48, th, fill=GROUND)
    hline(doc, 25, W - 25, ty + ch - 1)
    for k, (code, title, examples) in enumerate(FIT_AREAS):
        x, top = 24 + cw * (k % 3), ty + ch * (k // 3)
        if k % 3:
            vline(doc, x, top + (1 if k < 3 else 0), top + ch - (0 if k < 3 else 1))
        legend(doc, code, x + 20, top + 34, fill=SIGNAL, size=10)
        doc.text(title, x + 20, top + 64, 15, wght=600, wdth=108, track=-0.01)
        doc.lines(examples, x + 20, top + 92, 12.5, 20, fill=TEXT_2)
    y = doc.lines(wrap(CUSTOM_NOTE, 792, 12.5), EDGE, ty + th + 34, 12.5, 19, fill=TEXT_3)
    doc.h = y + 30
    finish(doc)
    doc.save("custom-orders.svg")


def open_source_head(narrow: bool = False):
    doc = Doc(NW if narrow else W, 0, "Open source from ApexAi", HEADS["open"][1])
    y = section_head(doc, "open", y=40 if narrow else 44, edge=NEDGE if narrow else EDGE, size=21 if narrow else 24)
    doc.h = y + (24 if narrow else 28)
    finish(doc)
    doc.save("open-source-narrow.svg" if narrow else "open-source.svg")


def repo_card(name: str, kind: str, meta: str, desc: str, filename: str | None = None):
    w, h = 412, 150
    doc = Doc(w, h, f"{name}: {kind.lower()}", desc)
    legend(doc, kind, 24, 36, size=9.5)
    doc.text(meta, w - 24, 36, 10, face="mono", wdth=88, fill=TEXT_3, anchor="end")
    size = min(21, fit(name, w - 48, 21, wght=600, wdth=112, track=-0.02))
    doc.text(name, 23, 72, size, wght=600, wdth=112, track=-0.02)
    lines = wrap(desc, w - 48, 13.5)
    assert len(lines) <= 2, f"{name}: description needs {len(lines)} lines; shorten it"
    doc.lines(lines, 24, 102, 13.5, 20, fill=TEXT_2)
    doc.h = h
    finish(doc, radius=12)
    doc.save(filename or f"repo-{name}.svg")


def all_repos_card():
    w, h = 412, 150
    doc = Doc(w, h, "All ApexAi public repositories", "Browse every public repository from ApexAi on GitHub.")
    legend(doc, "Index", 24, 36, size=9.5)
    doc.text("All public repositories", 23, 72, 21, wght=600, wdth=112, track=-0.02)
    doc.lines(["Browse everything ApexAi publishes on GitHub,", "newest first."], 24, 102, 13.5, 20, fill=TEXT_2)
    ext_arrow(doc, w - 34, 44, 9, TEXT_3)
    doc.h = h
    finish(doc, radius=12)
    doc.save("repo-all.svg")


def footer(narrow: bool = False):
    w = NW if narrow else W
    doc = Doc(w, 0, "ApexAi", FOOTER_LINES[0])
    brand_mark(doc, w / 2 - 20, 34, 40)
    doc.text("ApexAi", w / 2, 118, 22, wght=640, wdth=118, track=-0.012, anchor="middle")
    y = 150
    for line in wrap(FOOTER_LINES[0], w - 2 * NEDGE, 14 if not narrow else 13):
        doc.text(line, w / 2, y, 14 if not narrow else 13, fill=TEXT_2, anchor="middle")
        y += 20
    doc.text(FOOTER_LINES[1], w / 2, y + 6, 12.5 if not narrow else 12, fill=TEXT_3, anchor="middle")
    doc.h = y + 38
    finish(doc, fill="#06090c", glow=(w / 2, 40))
    doc.save("footer-narrow.svg" if narrow else "footer.svg")


# ---------------------------------------------------------------------------
# Narrow variants (phones). Same content and vocabulary, restacked the way the website
# does below 60rem: callers become a row and routes collapse into sockets on each
# product gate, rails turn vertical, and matrices split into labelled rows.


def badge_width(code: str, size: float = 9.5) -> float:
    return 9 + 6 + 8 + measure(STATES[code][0].upper(), size, wght=640, wdth=118, track=0.1) + 9


def hero_narrow():
    doc = Doc(NW, 0, "ApexAi: web data and business communications",
              "ApexAi builds Scrapy and Communications. Operators, software through ApexAPI, and AI agents through "
              "ApexMCP reach each product through its own authority gate. Opening for business soon.")
    brand_mark(doc, NEDGE - 5, 18, 24)
    doc.text("ApexAi", NEDGE + 29, 36, 17, wght=640, wdth=118, track=-0.012)
    state_w = legend(doc, "Opening soon", NW - NEDGE, 34, fill=AMBER, size=10, anchor="end")
    lx = NW - NEDGE - state_w - 14
    doc.add(f'<circle cx="{lx:.1f}" cy="30.5" r="6.5" fill="{AMBER}" fill-opacity=".12"/>'
            f'<circle cx="{lx:.1f}" cy="30.5" r="3.6" fill="none" stroke="{AMBER}" stroke-width="1.4"/>')

    head = ["Web data and", "business", "communications."]
    size = fit(head[-1], NW - 2 * NEDGE + 4, 46, wght=560, wdth=112, track=-0.042)
    y = 70 + size
    for i, line in enumerate(head):
        doc.text(line, NEDGE - 3, y + i * size, size, wght=560, wdth=112, track=-0.042)
    y = doc.lines(wrap(HERO_LEDE, NW - 2 * NEDGE, 15), NEDGE, y + size * 2 + 38, 15, 22.5, fill=TEXT_2)

    px, py, pw = NIN, y + 30, NW - 2 * NIN
    cw = pw / 3
    centers = [px + cw * (i + .5) for i in range(3)]
    # Callers row.
    legend(doc, "Callers", NEDGE, py + 24, size=9)
    top = py + 38
    for i, (name, via) in enumerate(CALLERS):
        x = px + cw * i
        if i:
            vline(doc, x, top, top + 62)
        doc.text(name, centers[i], top + 24, 14, wght=600, wdth=114, track=-0.015, anchor="middle")
        doc.text(via.split(" · ")[0], centers[i], top + 42, 9.5, face="mono", wdth=88, fill=TEXT_3, anchor="middle")
    y = top + 62
    blocks = []
    for j, product in enumerate(PRODUCTS):
        # Gate with one socket per caller, aligned under that caller.
        gy = y + 22
        blocks.append((y, gy))
        doc.add(f'<rect x="{px + 16}" y="{gy - 1}" width="{pw - 32}" height="2" rx="1" fill="{SIGNAL}" class="gate"/>',
                f'<rect x="{px + 16}" y="{gy - 4}" width="{pw - 32}" height="8" rx="4" fill="{SIGNAL}" fill-opacity=".14" class="gate-glow"/>')
        for i, cx in enumerate(centers):
            if (i, j) in PLANNED_ROUTES:
                doc.add(f'<circle cx="{cx:.1f}" cy="{gy}" r="6" fill="{GROUND}" stroke="{AMBER}" stroke-width="1.5" stroke-dasharray="2 2"/>')
            else:
                doc.add(f'<circle cx="{cx:.1f}" cy="{gy}" r="6" fill="{GROUND}" stroke="{SIGNAL}" stroke-width="1.5"/>'
                        f'<circle cx="{cx:.1f}" cy="{gy}" r="3" fill="{SIGNAL}" class="socket"/>')
        tag_w = measure(product["code"], 9, wght=640, wdth=118, track=0.1) + 14
        doc.add(f'<rect x="{NEDGE + .5}" y="{gy + 22.5}" width="{tag_w:.1f}" height="18" rx="3" fill="none" stroke="{SEAM_LIT}"/>')
        doc.text(product["code"], NEDGE + 7, gy + 35, 9, wght=640, wdth=118, track=0.1, fill=TEXT_2)
        doc.text(product["category"], NEDGE + tag_w + 10, gy + 35.5, 12, fill=TEXT_2)
        doc.text(product["name"], NEDGE - 1, gy + 72, 25, wght=600, wdth=114, track=-0.02)
        ex_x, ev_x = NEDGE, NEDGE + (pw - 32) * .52
        legend(doc, "Execution", ex_x, gy + 100, size=8.5)
        legend(doc, "Evidence", ev_x, gy + 100, size=8.5)
        a = doc.lines(product["execution"], ex_x, gy + 119, 10.5, 17, face="mono", wdth=88, fill=TEXT_2)
        b = doc.lines(product["evidence"], ev_x, gy + 119, 10.5, 17, face="mono", wdth=88, fill=TEXT_2)
        y = max(a, b) + 24
    foot = y
    lines = wrap(HERO_RULE, pw - 32, 12)
    y = doc.lines(lines, NEDGE, foot + 26, 12, 18, fill=TEXT_2)
    ky = y + 26
    doc.add(f'<circle cx="{NEDGE + 5}" cy="{ky - 3.5}" r="5" fill="none" stroke="{SIGNAL}" stroke-width="1.4"/>'
            f'<circle cx="{NEDGE + 5}" cy="{ky - 3.5}" r="2.4" fill="{SIGNAL}"/>')
    w = doc.text("in the product", NEDGE + 16, ky, 10, face="mono", wdth=88, fill=TEXT_3)
    kx = NEDGE + 16 + w + 22
    doc.add(f'<circle cx="{kx + 5}" cy="{ky - 3.5}" r="5" fill="none" stroke="{AMBER}" stroke-width="1.4" stroke-dasharray="2 2"/>')
    doc.text("planned", kx + 16, ky, 10, face="mono", wdth=88, fill=TEXT_3)
    ph = ky + 20 - py
    # Panel and seams go underneath the content drawn above.
    under = Doc(NW, 0, "")
    inset(under, px, py, pw, ph)
    hline(under, px + 1, px + pw - 1, top - 1)
    hline(under, px + 1, px + pw - 1, top + 61, SEAM_HI)
    for j, (btop, _) in enumerate(blocks[1:], 1):
        hline(under, px + 1, px + pw - 1, btop - 1, SEAM_HI)
    hline(under, px + 1, px + pw - 1, foot)
    doc.body[:0] = under.body

    doc.h = py + ph + 16
    finish(doc, fill="#06090c", glow=(NW * .25, 0))
    doc.style = (
        ".gate,.gate-glow,.socket{animation:lit .6s ease-out .6s both}"
        f"@keyframes lit{{from{{fill:{SEAM_LIT}}}}}"
        "@media (prefers-reduced-motion:reduce){.gate,.gate-glow,.socket{animation:none}}"
    )
    doc.save("hero-narrow.svg")


def product_narrow(product: dict):
    doc = Doc(NW, 0, f"{product['name']}: {product['category'].lower()}",
              f"{product['thesis']} {product['job']} Workflow: " + ", then ".join(product["steps"]) + ".")
    width = NW - 2 * NEDGE
    legend(doc, f"{product['code']} · {product['category']}", NEDGE, 42, size=10)
    size = fit("Communications", width + 6, 60, wght=560, wdth=125, track=-0.042)
    y = 58 + size * .74
    doc.text(product["name"], NEDGE - 4, y, size, wght=560, wdth=125, track=-0.042)
    y = doc.lines(wrap(product["thesis"], width, 17, wght=450), NEDGE, y + 44, 17, 24, wght=450)
    y = doc.lines(wrap(product["job"], width, 13.5), NEDGE, y + 30, 13.5, 20.5, fill=TEXT_2)

    legend(doc, product["workflow"], NEDGE, y + 44, size=9.5)
    ry = y + 60
    row, pw = 42, NW - 2 * NIN
    rh = row * len(product["steps"]) + 8
    inset(doc, NIN, ry, pw, rh)
    nx = NIN + 58
    doc.defs.append(
        '<linearGradient id="gatewash" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".1"/><stop offset=".8" stop-color="{SIGNAL}" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="lead" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{SIGNAL}"/><stop offset="1" stop-color="{SEAM_LIT}"/></linearGradient>'
    )
    first = ry + 4 + row / 2
    last = first + row * (len(product["steps"]) - 1)
    gate_y = first + row * product["gate"]
    doc.add(f'<rect x="{NIN + 1}" y="{gate_y - row / 2}" width="{pw - 2}" height="{row}" fill="url(#gatewash)"/>',
            f'<path d="M{nx + .5} {first}V{first + row}" stroke="url(#lead)"/>',
            f'<path d="M{nx + .5} {first + row}V{last}" stroke="{SEAM_LIT}"/>')
    for i, step in enumerate(product["steps"]):
        cy = first + row * i
        if i:
            hline(doc, NIN + 1, NIN + pw - 1, cy - row / 2 - 1, SEAM)
        doc.text(f"{i + 1:02d}", NEDGE, cy + 3.5, 10, face="mono", wdth=88, fill=TEXT_3)
        if i == product["gate"]:
            doc.add(f'<rect x="{nx - 9.5}" y="{cy - 6}" width="21" height="12" rx="3" fill="{SIGNAL}" fill-opacity=".16"/>'
                    f'<rect x="{nx - 8}" y="{cy - 2}" width="17" height="4" rx="2" fill="{SIGNAL}"/>')
            tag = "AUTHORITY"
            tw = measure(tag, 8, wght=640, wdth=118, track=0.1)
            tx = NIN + pw - 14 - tw - 10
            doc.add(f'<rect x="{tx + .5:.1f}" y="{cy - 8.5}" width="{tw + 10:.1f}" height="16" rx="3" fill="none" stroke="{SIGNAL}" stroke-opacity=".5"/>')
            doc.text(tag, tx + 5, cy + 2.5, 8, wght=640, wdth=118, track=0.1, fill=SIGNAL)
        elif i == 0:
            doc.add(f'<circle cx="{nx + .5}" cy="{cy}" r="9" fill="{SIGNAL}" fill-opacity=".14"/><circle cx="{nx + .5}" cy="{cy}" r="5.5" fill="{SIGNAL}"/>')
        else:
            doc.add(f'<circle cx="{nx + .5}" cy="{cy}" r="5" fill="{GROUND}" stroke="{SIGNAL}" stroke-width="1.5"/>')
        doc.text(step, nx + 22, cy + 4.5, 13.5, wght=600, wdth=104)
    y = ry + rh + 34
    caps = product["capabilities"]
    for i, cap in enumerate(caps):
        yy = y + 23 * i
        doc.add(f'<path d="M{NEDGE + .5} {yy - 10}v13" stroke="{SEAM_LIT}"/>')
        doc.text(cap, NEDGE + 10, yy, 12.5, fill=TEXT_2)
    doc.h = y + 23 * (len(caps) - 1) + 30
    finish(doc)
    doc.save(f"{product['slug']}-narrow.svg")


def availability_narrow():
    doc = Doc(NW, 0, "Public availability of ApexAi products",
              ". ".join(f"{p['name']}: " + ", ".join(f"{s} {STATES[c][0].lower()}" for s, c in AVAILABILITY[p['name']].items() if c)
                        for p in PRODUCTS) + ".")
    y = section_head(doc, "availability", y=42, edge=NEDGE, size=24, body=13.5)
    pw, row = NW - 2 * NIN, 36
    for product in PRODUCTS:
        cells = [(s, AVAILABILITY[product["name"]][s]) for s in SURFACES if AVAILABILITY[product["name"]][s]]
        ty = y + 30
        th = 44 + row * len(cells)
        inset(doc, NIN, ty, pw, th)
        doc.text(product["name"], NEDGE, ty + 28, 15, wght=600, wdth=114, track=-0.015)
        for r, (surface, code) in enumerate(cells):
            top = ty + 44 + row * r
            hline(doc, NIN + 1, NIN + pw - 1, top - 1, SEAM if r else SEAM_HI)
            cy = top + row / 2
            doc.text(surface, NEDGE, cy + 4.5, 13, wght=500)
            badge(doc, code, NW - NEDGE - badge_width(code), cy)
        y = ty + th - 6
    y += 36
    for code in STATES:
        badge(doc, code, NEDGE, y)
        y = doc.lines(wrap(STATE_MEANING[code], NW - 2 * NEDGE, 12), NEDGE, y + 30, 12, 18, fill=TEXT_2) + 32
    if not all(AVAILABILITY["Scrapy"].values()):
        y = doc.lines(["Scrapy has no Web Admin surface."], NEDGE, y - 6, 12, 18, fill=TEXT_3) + 32
    doc.h = y - 8
    finish(doc)
    doc.save("availability-narrow.svg")


def access_narrow():
    doc = Doc(NW, 0, "ApexAi access layers: ApexAPI, ApexMCP, and product plugins",
              " ".join(f"{a['name']} ({a['caller']}): {a['body']}" for a in ACCESS)
              + " Each product ships its own contracts; there is no shared gateway across products.")
    y = section_head(doc, "access", y=42, edge=NEDGE, size=24, body=13.5)
    pw = NW - 2 * NIN
    ty = y + 30
    under = len(doc.body)
    y = ty
    for k, layer in enumerate(ACCESS):
        if k:
            hline(doc, NIN + 1, NIN + pw - 1, y)
        y += 38
        doc.text(layer["name"], NEDGE, y, 21, wght=600, wdth=118, track=-0.02)
        doc.text(layer["caller"], NW - NEDGE, y - 1, 10, face="mono", wdth=88, fill=TEXT_3, anchor="end")
        y = doc.lines(wrap(layer["body"], pw - 32, 13), NEDGE, y + 26, 13, 19, fill=TEXT_2)
        for label, values in layer["specimen"]:
            legend(doc, label, NEDGE, y + 30, size=8.5)
            y = doc.lines(values, NEDGE, y + 48, 11, 19, face="mono", wdth=88, fill=TEXT)
        y += 26
    panel = Doc(NW, 0, "")
    inset(panel, NIN, ty, pw, y - ty)
    doc.body[under:under] = panel.body
    doc.h = y + 16
    finish(doc)
    doc.save("access-narrow.svg")


def custom_orders_narrow():
    doc = Doc(NW, 0, "ApexAi custom orders",
              "Bespoke software, scoped before it is built. "
              + " ".join(f"{title}: {', '.join(ex)}." for _, title, ex in FIT_AREAS)
              + " Each request is scoped individually and quoted after scope is agreed.")
    y = section_head(doc, "custom", y=42, edge=NEDGE, size=24, body=13.5)
    pw = NW - 2 * NIN
    ty = y + 30
    under = len(doc.body)
    y = ty
    text_x = NEDGE + 46
    for k, (code, title, examples) in enumerate(FIT_AREAS):
        if k:
            hline(doc, NIN + 1, NIN + pw - 1, y)
        legend(doc, code, NEDGE, y + 30, fill=SIGNAL, size=9.5)
        doc.text(title, text_x, y + 30, 14.5, wght=600, wdth=108, track=-0.01)
        y = doc.lines(wrap(", ".join(examples), NW - NEDGE - text_x, 12.5), text_x, y + 52, 12.5, 18.5, fill=TEXT_2) + 22
    panel = Doc(NW, 0, "")
    inset(panel, NIN, ty, pw, y - ty)
    doc.body[under:under] = panel.body
    y = doc.lines(wrap(CUSTOM_NOTE, NW - 2 * NEDGE, 12), NEDGE, y + 30, 12, 18, fill=TEXT_3)
    doc.h = y + 26
    finish(doc)
    doc.save("custom-orders-narrow.svg")


def main():
    OUT.mkdir(exist_ok=True)
    hero()
    button("website", "Visit apexaiofficial.com", primary=True)
    button("updates", "Follow launch updates", primary=False)
    button("custom", "Request a custom build", primary=False)
    for product in PRODUCTS:
        product_plate(product)
    availability()
    access()
    custom_orders()
    open_source_head()
    for repo in REPOS:
        repo_card(*repo)
    all_repos_card()
    footer()

    hero_narrow()
    for product in PRODUCTS:
        product_narrow(product)
    availability_narrow()
    access_narrow()
    custom_orders_narrow()
    open_source_head(narrow=True)
    footer(narrow=True)


if __name__ == "__main__":
    main()
