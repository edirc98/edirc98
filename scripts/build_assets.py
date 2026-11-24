#!/usr/bin/env python3
"""
Generates every SVG used by the profile README into ../assets.

Visual language: Marathon-style acid/black, brutalist blocks, terminal UI.
Edit the CONTENT section, then run:

    python3 scripts/build_assets.py

No dependencies (stdlib only).
"""
import random
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

# ───────────────────────────────── palette ──────────────────────────────────
VOID = "#0A0A0A"
PANEL = "#0E0E0E"
GRID = "#151515"
LINE = "#2A2A2A"
DIM = "#6E6E6E"
SOFT = "#B9B7B0"
BONE = "#E8E6DF"
ACID = "#C8FF00"
HOT = "#FF2E63"
CYAN = "#00E0FF"

MONO = ("ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono',monospace")

BASE_CSS = f"""
text{{font-family:{MONO};white-space:pre}}
.b{{font-weight:700}}
.px{{animation:on .04s steps(1) backwards}}
.show{{animation:on .01s steps(1) backwards}}
.blink{{animation:blink 1s steps(1) infinite}}
.spin{{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}}
.spinr{{transform-box:fill-box;transform-origin:center;animation:spin 7s linear infinite reverse}}
@keyframes on{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
"""

# ─────────────────────────────── pixel font ─────────────────────────────────
# Squared 5x7 bitmap glyphs — brutalist, deterministic on every OS.
FONT = {
    "A": ["#####", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "#####", "#...#", "#...#", "#####"],
    "C": ["#####", "#....", "#....", "#....", "#....", "#....", "#####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": ["#####", "#....", "#....", "#.###", "#...#", "#...#", "#####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["....#", "....#", "....#", "....#", "....#", "#...#", "#####"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#####"],
    "P": ["#####", "#...#", "#...#", "#####", "#....", "#....", "#...."],
    "Q": ["#####", "#...#", "#...#", "#...#", "#.#.#", "#..##", "#####"],
    "R": ["#####", "#...#", "#...#", "#####", "#.#..", "#..#.", "#...#"],
    "S": ["#####", "#....", "#....", "#####", "....#", "....#", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#####"],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", "#...#", "#####", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": ["#####", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#####"],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "2": ["#####", "....#", "....#", "#####", "#....", "#....", "#####"],
    "3": ["#####", "....#", "....#", ".####", "....#", "....#", "#####"],
    "4": ["#...#", "#...#", "#...#", "#####", "....#", "....#", "....#"],
    "5": ["#####", "#....", "#....", "#####", "....#", "....#", "#####"],
    "6": ["#####", "#....", "#....", "#####", "#...#", "#...#", "#####"],
    "7": ["#####", "....#", "....#", "...#.", "..#..", "..#..", "..#.."],
    "8": ["#####", "#...#", "#...#", "#####", "#...#", "#...#", "#####"],
    "9": ["#####", "#...#", "#...#", "#####", "....#", "....#", "#####"],
    "#": [".#.#.", "#####", ".#.#.", ".#.#.", "#####", ".#.#.", "....."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    ":": [".", "#", ".", ".", ".", "#", "."],
}


def pixel_width(s, cell):
    w = 0
    for ch in s.upper():
        w += 3 * cell if ch == " " else (len(FONT[ch][0]) + 1) * cell
    return w - cell


def pixel_text(s, x, y, cell, block, fill, boot=None, extra=""):
    """Draw text as blocks. boot=(rng, max_delay) staggers each block's reveal."""
    out = [f'<g fill="{fill}" {extra}>']
    cx = x
    for ch in s.upper():
        if ch == " ":
            cx += 3 * cell
            continue
        rows = FONT[ch]
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v != "#":
                    continue
                attrs = ""
                if boot:
                    rng, maxd = boot
                    attrs = f' class="px" style="animation-delay:{rng.uniform(0, maxd):.2f}s"'
                out.append(f'<rect x="{cx + c * cell}" y="{y + r * cell}" '
                           f'width="{block}" height="{block}"{attrs}/>')
        cx += (len(rows[0]) + 1) * cell
    out.append("</g>")
    return "".join(out)


# ─────────────────────────────── primitives ─────────────────────────────────
def svg(w, h, body, title, css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" xml:space="preserve" role="img" aria-label="{escape(title)}">'
            f"<title>{escape(title)}</title><style>{BASE_CSS}{css}</style>"
            f"{body}</svg>")


def t(x, y, s, size=12, fill=BONE, anchor="start", cls="", ls=0, extra=""):
    c = f' class="{cls}"' if cls else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}"{a}{l}{c} {extra}>'
            f"{escape(s)}</text>")


def barcode(x, y, w, h, seed, fill=BONE):
    rng = random.Random(seed)
    out, cx = [], x
    while cx < x + w:
        bw = rng.choice([1, 1, 2, 2, 3, 4])
        if rng.random() > 0.35 and cx + bw <= x + w:
            out.append(f'<rect x="{cx}" y="{y}" width="{bw}" height="{h}"/>')
        cx += bw + rng.choice([1, 2, 2, 3])
    return f'<g fill="{fill}">{"".join(out)}</g>'


def crop_marks(w, h, inset=8, ln=14, color=ACID, sw=2):
    p = []
    for (x, y, dx, dy) in [(inset, inset, 1, 1), (w - inset, inset, -1, 1),
                           (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)]:
        p.append(f"M{x} {y + dy * ln}V{y}H{x + dx * ln}")
    return f'<path d="{"".join(p)}" fill="none" stroke="{color}" stroke-width="{sw}"/>'


def hazard_defs(pid, color=ACID, size=16):
    return (f'<pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><rect width="{size // 2}" height="{size}" '
            f'fill="{color}"/></pattern>')


def ticks(x0, x1, y, step=10, h=4, color=LINE, major=50, mh=8):
    p = []
    for x in range(x0, x1 + 1, step):
        hh = mh if (x - x0) % major == 0 else h
        p.append(f"M{x} {y}v{-hh}")
    return f'<path d="{"".join(p)}" stroke="{color}" stroke-width="1"/>'


def write(name, content):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content, encoding="utf-8")
    print(f"  ✓ assets/{name}  ({len(content.encode()) / 1024:.1f} KB)")


# ───────────────────────────────── CONTENT ──────────────────────────────────
NAME = "EDGAR"
SURNAME = "RODRÍGUEZ DE LA CALLE"
ROLE = "UNITY DEVELOPER // VR // GAMES"
HANDLE = "EDIRC98"

TERMINAL = [
    ("cmd", "whoami"),
    ("out", [("edgar rodríguez de la calle", BONE, True), ("  // unity developer · barcelona", DIM, False)]),
    ("gap",),
    ("cmd", "cat about.txt"),
    ("out", [("5+ years building interactive VR apps & games with Unity / C#.", BONE, False)]),
    ("out", [("pro   ", ACID, True), ("→ unity dev in a clinical VR research lab (IDIBAPS)", SOFT, False)]),
    ("out", [("side  ", ACID, True), ("→ indie games · 3d printing · fpv drones · electronics", SOFT, False)]),
    ("out", [("core  ", ACID, True), ("→ design patterns · SOLID · clean, scalable architecture", SOFT, False)]),
    ("gap",),
    ("cmd", "ls ./interests"),
    ("out", [("ai/   computer-graphics/   3d-printing/   game-tech/   photography/", ACID, False)]),
    ("gap",),
    ("cmd", "./status --now"),
    ("out", [("[LIVE] ", ACID, True), ("balanz-it   ·  out on App Store + Google Play", BONE, False)]),
    ("out", [("[DEV]  ", HOT, True), ("jump-frog   ·  physics platformer, in development", BONE, False)]),
    ("prompt",),
]

SECTIONS = [
    ("01", "WHOAMI", "// who is behind the visor"),
    ("02", "OPERATIONS", "// featured projects · click a card to open"),
    ("03", "LOADOUT", "// engine, languages, modules & tools"),
    ("04", "ARCHIVE", "// previous ops, labs & experiments"),
]

OPS = [
    dict(slug="balanzit", idx="01", cat="MOBILE GAME", status="LIVE", color=ACID,
         title="BALANZ-IT",
         desc="Physics-based mobile puzzle game. Stack and balance geometric "
              "shapes on a moving platform against the clock.",
         meta="PLATFORMS: iOS · ANDROID", tags=["UNITY", "C#", "iOS", "ANDROID"],
         cta="PLAY ↗"),
    dict(slug="jumpfrog", idx="02", cat="PLATFORMER", status="IN DEV", color=HOT,
         title="JUMP-FROG",
         desc="Physics-based platformer inspired by Jump King. Co-developed "
              "with mikelghedina, currently in development.",
         meta="TARGET PLATFORMS: iOS · ANDROID", tags=["UNITY", "C#", "iOS", "ANDROID"],
         cta="IN DEVELOPMENT"),
    dict(slug="xrpain", idx="03", cat="CLINICAL VR", status="RCT VALIDATED", color=BONE,
         title="XR-PAIN",
         desc="VR application for chronic pain management, developed at IDIBAPS "
              "and validated in a randomized controlled trial with 100 patients.",
         meta="RCT · n=100 PATIENTS", tags=["UNITY", "META XR SDK", "C#"],
         cta="IDIBAPS // RESEARCH"),
    dict(slug="vrpuzzle", idx="04", cat="VR + MOCAP", status="R&D", color=CYAN,
         title="VR-PUZZLE",
         desc="Hand-tracked puzzle game (grab, throw, place) with OptiTrack mocap "
              "suit integration for an AI motion-reconstruction dataset.",
         meta="INPUT: HAND TRACKING · OPTITRACK", tags=["UNITY", "C#", "META XR", "OPTITRACK"],
         cta="SOURCE ↗"),
    dict(slug="hapticvr", idx="05", cat="VR + ROBOTICS", status="IN DEV", color=HOT,
         title="HAPTIC-VR",
         desc="VR integration with a 3D Systems Touch haptic robot to simulate "
              "the weight of virtual objects, used as experimental conditions in research.",
         meta="DEVICE: 3D SYSTEMS TOUCH · FORCE FEEDBACK", tags=["UNITY", "META XR SDK", "ROBOTICS"],
         cta="IDIBAPS // RESEARCH"),
    dict(slug="watermark", idx="06", cat="PHOTO TOOLING", status="LIVE", color=ACID,
         title="WATERMARK",
         desc="Batch watermarking tool: stamps a custom-designed watermark across "
              "entire photo sets in a single run.",
         meta="BATCH PROCESSING · PYTHON + PILLOW", tags=["PYTHON", "PILLOW"],
         cta="SOURCE ↗"),
]

# (slug, index, label, brand colour, text colour on brand)
BUTTONS = [
    ("linkedin", "in", "LINKEDIN", "#0A66C2", "#FFFFFF"),
    ("portfolio", "~/", "WEBPAGE", "#FD985E", VOID),
]

LOADOUT_PRIMARY = [("PRIMARY // ENGINE", "A1", "UNITY"), ("PRIMARY // LANGUAGE", "A2", "C#")]
LOADOUT_COLUMNS = [
    ("LANG.SECONDARY", "B1", ["C++", "PYTHON"]),
    ("PLATFORMS", "B2", ["ANDROID", "iOS", "META QUEST", "DESKTOP"]),
    ("FABRICATION", "B3", ["BLENDER", "3DS MAX", "FIGMA"]),
    ("UTILITIES", "B4", ["GIT / GITHUB", "RIDER", "VISUAL STUDIO", "VS CODE", "TRELLO", "SLACK"]),
]
AI = ["AGENTIC PROGRAMMING", "CLAUDE CODE", "PROMPT ENGINEERING", "AI-ASSISTED WORKFLOWS"]
MODS = ["STATE MACHINE", "OBSERVER / EVENTS", "MVC", "OBJECT POOLING", "SCRIPTABLE OBJECTS",
        "DEPENDENCY INJECTION", "SINGLETON", "SOLID", "CLEAN ARCHITECTURE"]

MARQUEE = "EDIRC98 /// UNITY /// VIRTUAL REALITY /// INDIE GAMES /// BARCELONA /// "


# ───────────────────────────────── header ───────────────────────────────────
def build_header():
    W, H = 900, 380
    rng = random.Random(7)
    b = [f'<defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse">'
         f'<path d="M20 0H0V20" fill="none" stroke="{GRID}"/></pattern>{hazard_defs("hz")}'
         f'</defs>',
         f'<rect width="{W}" height="{H}" fill="{VOID}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#g)"/>']

    # meta bar
    b += [t(40, 32, "RUNNER.PROFILE / 001", 11, DIM, ls=2),
          t(450, 32, f"ID://{HANDLE}", 11, ACID, "middle", "b", ls=2),
          t(860, 32, "41.3874°N  2.1686°E · BCN", 11, DIM, "end", ls=1),
          f'<path d="M40 44H860" stroke="{LINE}"/>',
          f'<rect x="40" y="42" width="64" height="4" fill="{ACID}"/>',
          f'<rect x="796" y="42" width="64" height="4" fill="{HOT}"/>']

    # giant name, glitch copies behind
    cell, block, nx, ny = 20, 17, 40, 70
    b.append(pixel_text(NAME, nx, ny, cell, block, ACID, boot=(rng, 0.9)))

    # reticle
    cx, cy = 762, 146
    b += [f'<circle cx="{cx}" cy="{cy}" r="82" fill="none" stroke="{LINE}"/>',
          f'<circle class="spin" cx="{cx}" cy="{cy}" r="68" fill="none" stroke="{ACID}" '
          f'stroke-width="2" stroke-dasharray="2 7"/>',
          f'<g class="spinr"><circle cx="{cx}" cy="{cy}" r="54" fill="none" stroke="none"/>'
          f'<path d="M{cx} {cy - 54}A54 54 0 0 1 {cx + 47} {cy - 27}" fill="none" '
          f'stroke="{HOT}" stroke-width="4"/>'
          f'<path d="M{cx} {cy + 54}A54 54 0 0 1 {cx - 47} {cy + 27}" fill="none" '
          f'stroke="{BONE}" stroke-width="4"/></g>',
          f'<circle cx="{cx}" cy="{cy}" r="22" fill="none" stroke="{BONE}" stroke-width="2"/>',
          f'<path d="M{cx - 104} {cy}H{cx - 30}M{cx + 30} {cy}H{cx + 104}'
          f'M{cx} {cy - 104}V{cy - 30}M{cx} {cy + 30}V{cy + 104}" stroke="{BONE}"/>',
          f'<rect class="blink" x="{cx - 4}" y="{cy - 4}" width="8" height="8" fill="{HOT}"/>',
          t(cx + 58, cy - 72, "TGT.LOCK", 10, ACID, cls="b", ls=1),
          t(cx - 58, cy + 82, "R-082 · VR/XR", 10, DIM, "end", ls=1)]

    # surname + role
    b += [t(40, 250, SURNAME, 21, BONE, cls="b", ls=7),
          f'<rect x="40" y="268" width="420" height="38" fill="{ACID}"/>',
          t(56, 293, ROLE, 15, VOID, cls="b", ls=3),
          f'<rect x="472" y="269" width="134" height="36" fill="none" stroke="{HOT}" stroke-width="2"/>',
          f'<rect class="blink" x="486" y="282" width="10" height="10" fill="{HOT}"/>',
          t(506, 293, "ONLINE", 14, HOT, cls="b", ls=4)]

    # barcode + serial
    b += [barcode(680, 258, 180, 36, "edirc98"),
          t(680, 312, "SN 45-44-47-41-52 / 2026", 10, DIM, ls=1)]

    # hazard band (scrolling)
    b += ['<g clip-path="url(#band)"><clipPath id="band"><rect y="330" width="900" height="22"/></clipPath>',
          f'<g class="slide"><rect x="-40" y="330" width="980" height="22" fill="url(#hz)"/></g></g>',
          f'<rect x="200" y="330" width="500" height="22" fill="{VOID}"/>',
          t(450, 345, "SECTOR: BARCELONA ─ CLASS: UNITY/VR ─ 5+ YRS", 11, ACID, "middle", "b", ls=2),
          t(40, 372, "> ./boot --profile edirc98 ............ OK", 10, DIM, ls=1),
          t(860, 372, "PROFILE_V5 // HAND-BUILT SVG", 10, DIM, "end", ls=1)]

    # vertical label, crop marks
    b += [t(0, 0, "■ EDIRC98 · RUNNER · ACTIVE", 9, DIM, ls=3,
            extra=f'transform="translate(884 64) rotate(90)"'),
          crop_marks(W, H)]

    css = """
.slide{animation:slide 1.2s linear infinite}
@keyframes slide{to{transform:translateX(22.627px)}}
"""
    write("header.svg", svg(W, H, "".join(b), f"{NAME} {SURNAME} — {ROLE}", css))


# ──────────────────────────────── buttons ───────────────────────────────────
def build_buttons():
    W, H = 214, 46
    for slug, idx, label, col, ink in BUTTONS:
        b = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="{VOID}" stroke="{col}" stroke-width="2"/>',
             f'<rect x="0" y="0" width="40" height="{H}" fill="{col}"/>',
             t(20, 28, idx, 13, ink, "middle", "b"),
             t(54, 28, label, 13, BONE, cls="b", ls=2),
             t(W - 14, 28, "↗", 15, col, "end", "b")]
        write(f"btn-{slug}.svg", svg(W, H, "".join(b), label))


# ─────────────────────────────── terminal ───────────────────────────────────
def build_terminal():
    W = 900
    size, lh, x0 = 15, 25, 30
    char_w = size * 0.62
    y = 78
    body, t_now = [], 0.5

    for item in TERMINAL:
        kind = item[0]
        if kind == "gap":
            y += lh // 2
            continue
        if kind == "cmd":
            cmd = item[1]
            n = len(cmd)
            dur = max(0.25, n * 0.055)
            cover_w = n * char_w + 6
            cx = x0 + 2 * char_w
            body.append(f'<g class="show" style="animation-delay:{t_now:.2f}s">'
                        f'<text x="{x0}" y="{y}" font-size="{size}">'
                        f'<tspan fill="{ACID}" font-weight="700">$ </tspan>'
                        f'<tspan fill="{BONE}">{escape(cmd)}</tspan></text>'
                        # cover sits just right of the text; animation slides it from over the text
                        f'<rect x="{cx + cover_w:.1f}" y="{y - size}" width="{cover_w:.1f}" height="{lh}" '
                        f'fill="{PANEL}" class="type" style="--w:-{cover_w:.1f}px;'
                        f'animation-duration:{dur:.2f}s;animation-delay:{t_now + 0.15:.2f}s;'
                        f'animation-timing-function:steps({n})"/></g>')
            t_now += 0.15 + dur + 0.2
        elif kind == "out":
            bold_attr = ' font-weight="700"'
            spans = "".join(
                f'<tspan fill="{c}"{bold_attr if bold else ""}>{escape(s)}</tspan>'
                for s, c, bold in item[1])
            body.append(f'<text x="{x0 + 2 * char_w:.1f}" y="{y}" font-size="{size}" class="show" '
                        f'style="animation-delay:{t_now:.2f}s">{spans}</text>')
            t_now += 0.12
        elif kind == "prompt":
            body.append(f'<g class="show" style="animation-delay:{t_now:.2f}s">'
                        f'<text x="{x0}" y="{y}" font-size="{size}" fill="{ACID}" font-weight="700">$</text>'
                        f'<rect class="blink" x="{x0 + 2 * char_w:.1f}" y="{y - size + 2}" '
                        f'width="{char_w:.1f}" height="{size + 2}" fill="{ACID}"/></g>')
        y += lh

    H = y + 14
    frame = [f'<rect width="{W}" height="{H}" fill="{PANEL}"/>',
             f'<rect x="0" y="0" width="{W}" height="34" fill="{ACID}"/>',
             f'<rect x="14" y="12" width="10" height="10" fill="{VOID}"/>',
             f'<rect x="30" y="12" width="10" height="10" fill="none" stroke="{VOID}" stroke-width="2"/>',
             f'<rect x="46" y="12" width="10" height="10" fill="none" stroke="{VOID}" stroke-width="2"/>',
             t(74, 22, "edgar: ~/profile — zsh", 12, VOID, cls="b", ls=1),
             t(W - 16, 22, "TTY/01 · 900×42 · UTF-8", 11, VOID, "end", ls=1),
             f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{ACID}" stroke-width="2"/>',
             f'<rect x="{W - 10}" y="44" width="4" height="{H - 60}" fill="{GRID}"/>',
             f'<rect x="{W - 10}" y="44" width="4" height="60" fill="{LINE}"/>']
    css = """
.type{animation-name:type;animation-fill-mode:backwards}
@keyframes type{from{transform:translateX(var(--w))}to{transform:translateX(0)}}
"""
    alt = ("Terminal: whoami — Edgar Rodríguez de la Calle, Unity developer in Barcelona. "
           "5+ years building VR apps and games with Unity/C#.")
    write("terminal.svg", svg(W, H, "".join(frame + body), alt, css))


# ─────────────────────────────── sections ───────────────────────────────────
def build_sections():
    W, H = 900, 86
    for num, title, sub in SECTIONS:
        nw = pixel_width(num, 9)
        tx = 40 + nw + 24
        b = [f'<rect width="{W}" height="{H}" fill="{VOID}"/>',
             pixel_text(num, 40, 10, 9, 8, ACID),
             pixel_text(title, tx, 12, 4, 4, BONE),
             t(tx, 62, sub, 12, DIM, ls=1),
             t(860, 24, f"SEC.{num}/{SECTIONS[-1][0]}", 11, ACID, "end", "b", ls=2),
             barcode(740, 34, 120, 26, f"sec{num}", DIM),
             ticks(40, 860, 82),
             f'<path d="M40 82H860" stroke="{LINE}"/>',
             f'<rect x="40" y="80" width="{nw}" height="4" fill="{ACID}"/>']
        write(f"sec-{num}.svg", svg(W, H, "".join(b), f"{num} // {title}"))


# ──────────────────────────────── op cards ──────────────────────────────────
def build_ops():
    W, H = 440, 270
    for op in OPS:
        col = op["color"]
        b = [f'<rect width="{W}" height="{H}" fill="{VOID}"/>',
             pixel_text(op["idx"], W - pixel_width(op["idx"], 16) - 14, H - 126, 16, 16, "#131313"),
             f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{LINE}" stroke-width="2"/>',
             f'<rect width="{W}" height="30" fill="{col}"/>',
             t(14, 20, f"OP-{op['idx']} // {op['cat']}", 12, VOID, cls="b", ls=2),
             f'<rect class="blink" x="{W - 24}" y="11" width="8" height="8" fill="{VOID}"/>',
             t(W - 32, 20, f"STATUS: {op['status']}", 12, VOID, "end", "b", ls=1),
             pixel_text(op["title"], 22, 50, 6, 5, BONE),
             barcode(W - 64, 50, 42, 42, op["slug"], DIM)]
        for i, line in enumerate(textwrap.wrap(op["desc"], 48, break_on_hyphens=False)):
            b.append(t(22, 126 + i * 19, line, 13, SOFT))
        b.append(t(22, 196, op["meta"], 11, col, cls="b", ls=1))
        x = 22
        for tag in op["tags"]:
            tw = len(tag) * 7 + 18
            b += [f'<rect x="{x}" y="210" width="{tw}" height="24" fill="none" stroke="{DIM}"/>',
                  t(x + tw / 2, 226, tag, 11, BONE, "middle", ls=0.5)]
            x += tw + 6
        b += [f'<path d="M22 250H{W - 22}" stroke="{LINE}"/>',
              t(W - 22, 264, op["cta"], 11, ACID if "↗" in op["cta"] else DIM, "end", "b", ls=2),
              t(22, 264, f"0x{op['idx']}F{len(op['title']):02X}", 10, DIM, ls=1)]
        write(f"op-{op['slug']}.svg", svg(W, H, "".join(b), f"{op['title']} — {op['desc']}"))


# ──────────────────────────────── loadout ───────────────────────────────────
def build_loadout():
    W = 900
    b = []
    # primary slots
    for i, (label, slot, name) in enumerate(LOADOUT_PRIMARY):
        x, w = 40 + i * 415, 405
        b += [f'<rect x="{x}" y="10" width="{w}" height="120" fill="{PANEL}" stroke="{ACID}" stroke-width="2"/>',
              f'<rect x="{x}" y="10" width="{w}" height="24" fill="{ACID}"/>',
              t(x + 12, 27, label, 11, VOID, cls="b", ls=2),
              t(x + w - 12, 27, f"SLOT {slot}", 11, VOID, "end", "b", ls=2),
              pixel_text(name, x + 22, 52, 8, 7, BONE),
              f'<rect class="blink" x="{x + w - 104}" y="104" width="8" height="8" fill="{ACID}"/>',
              t(x + w - 14, 112, "EQUIPPED", 11, ACID, "end", "b", ls=2),
              barcode(x + w - 104, 50, 90, 36, name, LINE)]
    # columns
    y0 = 162
    max_items = max(len(c[2]) for c in LOADOUT_COLUMNS)
    for i, (label, slot, items) in enumerate(LOADOUT_COLUMNS):
        x = 40 + i * 208
        b += [f'<rect x="{x}" y="{y0 - 10}" width="8" height="8" fill="{ACID}"/>',
              t(x + 14, y0 - 2, label, 11, ACID, cls="b", ls=2),
              t(x + 196, y0 - 2, slot, 11, DIM, "end"),
              f'<path d="M{x} {y0 + 8}H{x + 196}" stroke="{LINE}"/>']
        for j, it in enumerate(items):
            yy = y0 + 32 + j * 24
            b.append(f'<text x="{x}" y="{yy}" font-size="14"><tspan fill="{DIM}">› </tspan>'
                     f'<tspan fill="{BONE}">{escape(it)}</tspan></text>')
        for j in range(len(items), max_items):
            yy = y0 + 32 + j * 24
            b.append(t(x, yy, "› ----------", 14, LINE))
    # chip rows: AI + architecture mods
    def chip_row(top, label, items, col, sym):
        rows = [f'<rect x="40" y="{top}" width="8" height="8" fill="{col}"/>',
                t(54, top + 8, label, 11, col, cls="b", ls=2),
                f'<path d="M40 {top + 18}H860" stroke="{LINE}"/>']
        x, yy = 40, top + 32
        for m in items:
            w = len(m) * 7.6 + 34
            if x + w > 860:
                x, yy = 40, yy + 36
            rows += [f'<rect x="{x}" y="{yy}" width="{w:.0f}" height="26" fill="none" stroke="{BONE}"/>',
                     t(x + 10, yy + 18, sym, 12, col, cls="b"),
                     t(x + 24, yy + 18, m, 12, BONE, ls=0.5)]
            x += w + 8
        return rows, yy + 26

    top = y0 + 32 + max_items * 24 + 14
    rows, bottom = chip_row(top, "AI.CORE // AGENTIC DEVELOPMENT", AI, CYAN, "◆")
    b += rows
    rows, bottom = chip_row(bottom + 30, "MODS // ARCHITECTURE & DESIGN PATTERNS", MODS, HOT, "+")
    b += rows
    H = bottom + 16
    b.insert(0, f'<rect width="{W}" height="{H}" fill="{VOID}"/>')
    alt = ("Loadout: Unity, C#, C++, Python. Platforms: Android, iOS, Meta Quest, Desktop. "
           "Blender, 3ds Max, Figma, Git. AI: agentic programming, Claude Code.")
    write("loadout.svg", svg(W, H, "".join(b), alt))


# ──────────────────────────────── footer ────────────────────────────────────
def build_footer():
    W, H = 900, 190
    msg = "END OF TRANSMISSION"
    cell = 4
    pw = pixel_width(msg, cell)
    b = [f'<defs>{hazard_defs("hz2")}</defs>',
         f'<rect width="{W}" height="{H}" fill="{VOID}"/>',
         f'<rect y="0" width="{W}" height="12" fill="url(#hz2)"/>',
         pixel_text(msg, (W - pw) // 2, 44, cell, cell, BONE),
         t(W / 2, 96, "thanks for scanning this profile — signal lost in 3..2..1", 12, DIM, "middle", ls=1),
         f'<rect y="114" width="{W}" height="36" fill="{ACID}"/>',
         '<g class="mq">',
         t(0, 138, MARQUEE * 2, 14, VOID, cls="b", extra='textLength="1240" lengthAdjust="spacingAndGlyphs"'),
         t(1240, 138, MARQUEE * 2, 14, VOID, cls="b", extra='textLength="1240" lengthAdjust="spacingAndGlyphs"'),
         '</g>',
         t(40, 178, "© EDIRC98 · BARCELONA", 10, DIM, ls=1),
         t(860, 178, "[ CONNECTION CLOSED ]", 10, HOT, "end", "b", ls=2)]
    css = ".mq{animation:mq 18s linear infinite}@keyframes mq{to{transform:translateX(-1240px)}}"
    write("footer.svg", svg(W, H, "".join(b), "End of transmission", css))


if __name__ == "__main__":
    print("building assets →", OUT)
    build_header()
    build_buttons()
    build_terminal()
    build_sections()
    build_ops()
    build_loadout()
    build_footer()
