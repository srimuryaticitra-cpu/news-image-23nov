#!/usr/bin/env python3
"""One-page newspaper image: world news of Monday 23 November 2026.

Pure Python 3.13 standard library. Draws a 1024x1024 broadsheet front
page (masthead + lead story + eight supporting panels + footer strip)
and writes it as a deterministic PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png by default).

No network, no randomness without a fixed seed, no external files.
"""
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (244, 238, 224)
INK = (18, 20, 26)
NAVY = (13, 27, 54)
NAVY2 = (24, 48, 88)
GOLD = (201, 162, 60)
GOLD_LT = (232, 196, 110)
RED = (178, 34, 28)
RED_DK = (122, 18, 16)
WHITE = (250, 248, 242)
GREY = (88, 90, 96)
GREY_LT = (210, 204, 190)
SKY1 = (246, 178, 92)
SKY2 = (232, 120, 66)
SKY3 = (196, 74, 62)
SEA = (28, 68, 110)
SEA2 = (18, 48, 84)
TEAL = (16, 110, 104)
ORANGE = (224, 110, 32)
SMOKE = (120, 118, 112)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '1' = ink.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "00000", "00100"),
    ',': ("00000", "00000", "00000", "00000", "00000", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    ':': ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    ';': ("00000", "00100", "00000", "00000", "00000", "00100", "01000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '=': ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '$': ("00100", "01110", "10101", "01110", "00101", "01110", "00100"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(buf, x, y, s, scale, color):
    """Draw uppercase text (lowercase is uppercased) at scale."""
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT['?']
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    _fill(buf, cx + col * scale, y + row * scale,
                          scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines."""
    lines = []
    for para in s.split('\n'):
        words = para.split(' ')
        cur = ''
        for w in words:
            trial = (cur + ' ' + w).strip()
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def draw_para(buf, x, y, s, scale, color, max_w, leading=None):
    if leading is None:
        leading = 7 * scale + 3 * scale
    lines = wrap_text(s, scale, max_w)
    for ln in lines:
        draw_text(buf, x, y, ln, scale, color)
        y += leading
    return y


# ---------------------------------------------------------------- canvas
def new_canvas():
    buf = bytearray(W * H * 3)
    for i in range(0, len(buf), 3):
        buf[i] = PAPER[0]
        buf[i + 1] = PAPER[1]
        buf[i + 2] = PAPER[2]
    return buf


def _fill(buf, x, y, w, h, color):
    if w <= 0 or h <= 0:
        return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = color
    row = bytes((r, g, b)) * (x1 - x0)
    for yy in range(y0, y1):
        off = (yy * W + x0) * 3
        buf[off:off + len(row)] = row


def _px(buf, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        off = (y * W + x) * 3
        buf[off] = color[0]
        buf[off + 1] = color[1]
        buf[off + 2] = color[2]


def _hline(buf, x0, x1, y, color):
    if x1 < x0:
        x0, x1 = x1, x0
    _fill(buf, x0, y, x1 - x0 + 1, 1, color)


def _vline(buf, x, y0, y1, color):
    if y1 < y0:
        y0, y1 = y1, y0
    _fill(buf, x, y0, 1, y1 - y0 + 1, color)


def _circle(buf, cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        _fill(buf, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def _ring(buf, cx, cy, r, color, thick=3):
    for t in range(thick):
        rr = r - t
        for a in range(360):
            import math
            x = int(cx + rr * math.cos(a * 0.0174533))
            y = int(cy + rr * math.sin(a * 0.0174533))
            _px(buf, x, y, color)


def _triangle(buf, x0, y0, x1, y1, x2, y2, color):
    # scanline fill of a triangle
    ys = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = ys
    def edge(xa, ya, xb, yb, y):
        if yb == ya:
            return xa
        return xa + (xb - xa) * (y - ya) / (yb - ya)
    for y in range(ay, cy + 1):
        if y < by:
            xa = edge(ax, ay, bx, by, y)
            xb = edge(ax, ay, cx, cy, y)
        else:
            xa = edge(bx, by, cx, cy, y)
            xb = edge(ax, ay, cx, cy, y)
        _hline(buf, int(min(xa, xb)), int(max(xa, xb)), y, color)


def _shade(c, f):
    return (max(0, min(255, int(c[0] * f))),
            max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))))


def _mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def _vgrad(buf, x, y, w, h, top, bot):
    for i in range(h):
        t = i / max(1, h - 1)
        _fill(buf, x, y + i, w, 1, _mix(top, bot, t))


def _dots(buf, x, y, w, h, color, step=7, seed=11):
    """Deterministic halftone-ish dot texture inside a region."""
    for yy in range(y, y + h, step):
        for xx in range(x, x + w, step):
            if ((xx * 31 + yy * 17 + seed) % 13) < 5:
                _fill(buf, xx, yy, 2, 2, color)


def _waves(buf, x, y, w, h, color, seed=3):
    for yy in range(y, y + h, 6):
        for xx in range(x, x + w, 9):
            if ((xx * 7 + yy * 13 + seed) % 11) < 6:
                _fill(buf, xx, yy, 5, 2, color)


# ---------------------------------------------------------------- scenes
def scene_antalya(buf, x, y, w, h):
    """Sunset over Antalya bay, empty summit hall silhouette, cracked sun."""
    _vgrad(buf, x, y, w, h, SKY1, SKY3)
    _dots(buf, x, y, w, h // 2, (255, 220, 160), step=9, seed=5)
    # sun low on the horizon, half-cracked
    sx, sy, sr = x + w - 150, y + 54, 38
    _circle(buf, sx, sy, sr, (255, 236, 180))
    _circle(buf, sx, sy, sr - 7, (255, 214, 130))
    # single diagonal crack through the sun
    for i in range(0, 2 * sr, 3):
        _fill(buf, sx - sr + i, sy - sr + i, 5, 4, SKY3)
    # distant mountains
    _triangle(buf, x, y + h - 60, x + 130, y + h - 118, x + 260, y + h - 60,
              _shade(SKY3, 0.75))
    _triangle(buf, x + 200, y + h - 60, x + 330, y + h - 126, x + 470, y + h - 60,
              _shade(SKY3, 0.62))
    _triangle(buf, x + 420, y + h - 60, x + 540, y + h - 110, x + w, y + h - 60,
              _shade(SKY3, 0.7))
    # sea
    _vgrad(buf, x, y + h - 60, w, 60, SEA, SEA2)
    for i in range(0, w, 26):
        _fill(buf, x + i, y + h - 44 + (i % 3) * 6, 16, 2, (120, 170, 210))
    # empty summit hall silhouette on the shore
    hx, hy = x + 24, y + h - 60
    _fill(buf, hx, hy - 46, 150, 46, (16, 20, 30))
    _triangle(buf, hx - 8, hy - 46, hx + 75, hy - 78, hx + 158, hy - 46,
              (16, 20, 30))
    for i in range(6):
        _fill(buf, hx + 10 + i * 23, hy - 38, 12, 20, GOLD_LT)
    # a few empty chairs / flags outside the hall
    for i in range(5):
        fx = x + w - 130 + i * 24
        _vline(buf, fx, hy - 34, hy - 6, (30, 32, 40))
        _fill(buf, fx, hy - 34, 16, 10, (200, 60, 50) if i % 2 == 0 else (40, 90, 160))
    # big NO DEAL stamp
    draw_text(buf, x + 26, y + 18, "NO DEAL", 7, RED_DK)
    draw_text(buf, x + 24, y + 16, "NO DEAL", 7, WHITE)


def scene_ship(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (58, 90, 120), (20, 44, 74))
    sea_y = y + h - 16
    _vgrad(buf, x, sea_y, w, 16, SEA, SEA2)
    _waves(buf, x, sea_y, w, 16, (140, 185, 220), seed=7)
    # listing warship hull, bow above water
    hull_y = sea_y - 12
    _fill(buf, x + 18, hull_y, 130, 12, (96, 102, 110))
    _triangle(buf, x + 148, hull_y, x + 172, hull_y, x + 148, hull_y + 12,
              (96, 102, 110))
    _fill(buf, x + 40, hull_y - 12, 80, 12, (120, 126, 134))
    _fill(buf, x + 60, hull_y - 22, 8, 10, (66, 70, 76))
    _fill(buf, x + 120, hull_y - 8, 22, 6, (150, 40, 34))
    # smoke + fireball
    _circle(buf, x + 110, y + 14, 15, (200, 90, 40))
    _circle(buf, x + 110, y + 14, 8, (250, 190, 60))
    _circle(buf, x + 80, y + 8, 10, SMOKE)
    _circle(buf, x + 140, y + 8, 9, SMOKE)
    # small drone boat on the water
    _fill(buf, x + w - 56, sea_y + 4, 30, 6, (30, 30, 34))
    _fill(buf, x + w - 48, sea_y - 4, 6, 8, (30, 30, 34))


def scene_kyiv(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (40, 44, 58), (18, 20, 30))
    # apartment block, middle floors collapsed
    bx, by, bw, bh = x + 22, y + 6, 96, h - 14
    _fill(buf, bx, by, bw, bh, (96, 88, 80))
    for r in range(2):
        for c in range(3):
            _fill(buf, bx + 8 + c * 30, by + 6 + r * 16, 18, 10,
                  (250, 210, 110) if (r + c) % 2 else (40, 42, 50))
    # collapsed section: dark gap + rubble at the foot
    _fill(buf, bx + 34, by + 8, 26, bh - 16, (20, 20, 26))
    _fill(buf, bx + 10, by + bh - 8, 76, 8, (120, 112, 100))
    # fire glow + smoke
    _circle(buf, bx + 47, by + 18, 10, (230, 120, 40))
    _circle(buf, bx + 47, by + 18, 5, (250, 200, 80))
    _circle(buf, bx + 20, y + 2, 9, SMOKE)
    # rescue lights
    _fill(buf, x + w - 58, y + h - 20, 32, 8, RED)
    _fill(buf, x + w - 50, y + h - 28, 16, 8, (250, 250, 240))


def scene_hormuz(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (30, 74, 96), (14, 40, 62))
    sea_y = y + h - 18
    _vgrad(buf, x, sea_y, w, 18, SEA, SEA2)
    # supertanker
    hull_y = sea_y - 12
    _fill(buf, x + 14, hull_y, 170, 12, (140, 44, 36))
    _fill(buf, x + 150, hull_y - 22, 34, 22, (230, 226, 214))
    _fill(buf, x + 20, hull_y - 4, 120, 4, (90, 26, 22))
    # fire on deck
    _circle(buf, x + 80, hull_y - 8, 11, (240, 130, 40))
    _circle(buf, x + 80, hull_y - 8, 5, (250, 210, 90))
    _circle(buf, x + 60, hull_y - 22, 9, SMOKE)
    # spiky sea mine
    mx, my = x + w - 52, y + 30
    _circle(buf, mx, my, 12, (30, 32, 36))
    _hline(buf, mx - 19, mx + 19, my, (30, 32, 36))
    _vline(buf, mx, my - 19, my + 19, (30, 32, 36))
    _hline(buf, mx - 13, mx + 13, my - 13, (30, 32, 36))
    _hline(buf, mx - 13, mx + 13, my + 13, (30, 32, 36))
    _fill(buf, mx - 2, my - 2, 4, 4, RED)
    draw_text(buf, x + 12, y + 8, "UNVERIFIED CLAIM", 1, (255, 220, 160))


def scene_factory(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (52, 48, 44), (24, 22, 20))
    # factory block + sawtooth roof
    fx, fy = x + 16, y + 18
    fh = h - 30
    _fill(buf, fx, fy, 170, fh, (120, 100, 78))
    for i in range(4):
        _triangle(buf, fx + i * 43, fy, fx + i * 43 + 21, fy - 14,
                  fx + i * 43 + 43, fy, (96, 80, 62))
    for i in range(5):
        _fill(buf, fx + 10 + i * 32, fy + 10, 18, 16, (250, 200, 90))
    _fill(buf, fx + 176, fy - 22, 14, fh + 10, (90, 76, 60))
    # flames licking the roof
    for (ox, oy, r) in [(40, 6, 10), (90, 2, 12), (140, 6, 9)]:
        _circle(buf, x + ox, y + oy, r, (235, 120, 35))
        _circle(buf, x + ox, y + oy + 3, max(3, r - 5), (250, 200, 80))
    _circle(buf, x + 90, y + 2, 10, SMOKE)


def scene_sudan(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (70, 60, 88), (28, 24, 40))
    ground = y + h - 8
    # city skyline at night
    for i, frac in enumerate([0.45, 0.65, 0.5, 0.75, 0.58, 0.42]):
        bh = int(h * frac)
        bx = x + 12 + i * 30
        _fill(buf, bx, ground - bh, 24, bh, (24, 22, 34))
        for wy in range(0, bh - 10, 12):
            _fill(buf, bx + 5, ground - bh + 6 + wy, 5, 6, (250, 210, 120))
    # drone + blast
    _fill(buf, x + w - 70, y + 12, 40, 6, (200, 200, 205))
    _fill(buf, x + w - 52, y + 6, 6, 18, (200, 200, 205))
    _circle(buf, x + w - 50, y + 34, 12, (240, 130, 40))
    _circle(buf, x + w - 50, y + 34, 6, (250, 210, 90))
    _circle(buf, x + 40, y + 10, 9, SMOKE)
    # stars
    for (sx, sy) in [(20, 12), (70, 26), (120, 10), (170, 30), (210, 14)]:
        _fill(buf, x + sx, y + sy, 2, 2, WHITE)


def scene_westbank(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (96, 78, 60), (48, 40, 32))
    # row of cars, two burning
    car_y = y + h - 22
    for i in range(4):
        cx = x + 14 + i * 52
        _fill(buf, cx, car_y, 44, 12, (60, 64, 70) if i % 2 else (140, 140, 135))
        _fill(buf, cx + 8, car_y - 10, 26, 10, (40, 44, 50))
        _circle(buf, cx + 10, car_y + 12, 4, (20, 20, 22))
        _circle(buf, cx + 34, car_y + 12, 4, (20, 20, 22))
    for fx in (x + 30, x + 134):
        _circle(buf, fx, car_y - 20, 10, (235, 120, 35))
        _circle(buf, fx, car_y - 17, 5, (250, 200, 80))
    _circle(buf, x + 90, y + 8, 10, SMOKE)
    # olive trees
    for tx in (x + w - 44, x + w - 66):
        _vline(buf, tx, y + 30, y + 58, (52, 40, 26))
        _circle(buf, tx, y + 24, 12, (70, 110, 52))


def scene_mercury(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (10, 12, 24), (26, 22, 44))
    for (sx, sy) in [(16, 14), (60, 30), (110, 10), (170, 26), (220, 12),
                      (40, 60), (150, 52), (200, 66)]:
        _fill(buf, x + sx, y + sy, 2, 2, WHITE)
    # Mercury: cratered disc
    mx, my, mr = x + w // 2, y + h // 2 + 2, min(24, h // 2 - 4)
    _circle(buf, mx, my, mr, (178, 164, 148))
    _circle(buf, mx - 8, my - 6, 6, (140, 126, 110))
    _circle(buf, mx + 7, my + 5, 7, (150, 136, 120))
    _circle(buf, mx + 2, my - 11, 4, (140, 126, 110))
    _circle(buf, mx - 11, my + 9, 3, (160, 146, 130))
    _circle(buf, mx + 11, my - 1, 3, (140, 126, 110))
    # terminator shading: darker crescent on the right edge
    for dy in range(-mr, mr + 1):
        dx = int((mr * mr - dy * dy) ** 0.5)
        _fill(buf, mx + dx - 7, my + dy, 7, 1, (150, 136, 120))
    # spacecraft with panels
    _fill(buf, x + 16, y + 16, 26, 12, (210, 210, 200))
    _fill(buf, x + 42, y + 20, 22, 4, (60, 90, 170))
    _fill(buf, x + 4, y + 20, 12, 4, (60, 90, 170))


def scene_exam(buf, x, y, w, h):
    _vgrad(buf, x, y, w, h, (36, 58, 92), (18, 30, 56))
    # exam hall desks + laptop
    desk_y = y + h - 16
    for i in range(3):
        dx = x + 16 + i * 62
        _fill(buf, dx, desk_y, 52, 8, (150, 120, 84))
        _fill(buf, dx + 8, desk_y - 20, 36, 20, (30, 34, 44))
        _fill(buf, dx + 12, desk_y - 16, 28, 12, (150, 210, 240))
    # big AI chip / robot eye above
    _fill(buf, x + w - 92, y + 8, 76, 40, (16, 20, 34))
    _fill(buf, x + w - 86, y + 12, 64, 32, (20, 60, 90))
    draw_text(buf, x + w - 78, y + 20, "AI", 4, (120, 220, 255))
    _fill(buf, x + w - 92, y + 48, 76, 4, RED)


# ---------------------------------------------------------------- panels
def panel(buf, x, y, w, h, tag, tag_bg, headline, body, scene=None,
          scene_h=70):
    _fill(buf, x, y, w, h, WHITE)
    _fill(buf, x, y, w, 3, tag_bg)
    # border
    _hline(buf, x, x + w - 1, y + h - 1, GREY_LT)
    _vline(buf, x + w - 1, y, y + h - 1, GREY_LT)
    _vline(buf, x, y, y + h - 1, GREY_LT)
    ty = y + 10
    if scene is not None:
        sh = scene_h
        scene(buf, x + 8, ty + 18, w - 16, sh)
        _fill(buf, x + 8, ty, text_width(tag, 1) + 12, 16, tag_bg)
        draw_text(buf, x + 14, ty + 4, tag, 1, WHITE)
        hy = ty + 18 + sh + 8
    else:
        _fill(buf, x + 8, ty, text_width(tag, 1) + 12, 16, tag_bg)
        draw_text(buf, x + 14, ty + 4, tag, 1, WHITE)
        hy = ty + 26
    hy = draw_para(buf, x + 10, hy, headline, 2, INK, w - 20, leading=17)
    draw_para(buf, x + 10, hy + 3, body, 1, (52, 54, 60), w - 20, leading=11)


def build():
    buf = new_canvas()
    # ---- masthead
    _fill(buf, 0, 0, W, 118, NAVY)
    _vgrad(buf, 0, 0, W, 118, NAVY2, NAVY)
    _fill(buf, 0, 114, W, 4, GOLD)
    draw_text(buf, 16, 14, "THE WORLD IN ONE DAY", 3, GOLD_LT)
    draw_text(buf, 16, 52, "MONDAY 23 NOVEMBER 2026", 5, WHITE)
    _fill(buf, 16, 104, 90, 3, GOLD)
    draw_text(buf, 760, 16, "ONE PAGE . ONE DAY", 2, (180, 190, 210))
    draw_text(buf, 760, 40, "THE FRONT PAGE", 2, (180, 190, 210))
    draw_text(buf, 760, 64, "NO. 327 . PRICE: THE NEWS", 1, (150, 160, 180))
    # ---- ticker bar
    _fill(buf, 0, 118, W, 26, (232, 224, 204))
    draw_text(buf, 16, 125, "15 STORIES . 7 REGIONS . ANTALYA . BENGHAZI . KYIV . HORMUZ . CIKANDE . KHARTOUM",
              1, INK)
    _hline(buf, 0, W - 1, 144, INK)
    # ---- lead story
    lx, ly, lw, lh = 16, 152, 628, 330
    _fill(buf, lx, ly, lw, lh, WHITE)
    _fill(buf, lx, ly, lw, 3, RED)
    scene_antalya(buf, lx + 8, ly + 8, lw - 16, 168)
    draw_text(buf, lx + 16, ly + 186, "CLIMATE . ANTALYA, TURKIYE", 1, RED)
    hy = draw_para(buf, lx + 12, ly + 208, "COP31 COLLAPSES: NO DEAL", 4, INK,
                   lw - 24, leading=34)
    hy = draw_para(buf, lx + 12, hy + 2,
                   "TWO DAYS OF OVERTIME END WITH NO PACT", 2, INK,
                   lw - 24, leading=18)
    draw_para(buf, lx + 12, hy + 6,
              "EU, UK and island states reject a draft that drops fossil "
              "fuels entirely; $120bn adaptation fund cut; first collapse "
              "since Copenhagen 2009. Ethiopia takes COP32.",
              1, (52, 54, 60), lw - 24, leading=11)
    # ---- right column panels
    panel(buf, 660, 152, 348, 160, "LIBYA . BENGHAZI", NAVY2,
          "RUSSIAN WARSHIP SUNK AT ANCHOR",
          "Corvette Merkury hit by up to six sea drones on Sunday; hull "
          "capsized, bow only above water. Two cargo ships also attacked.",
          scene=scene_ship, scene_h=52)
    panel(buf, 660, 322, 348, 160, "UKRAINE . KYIV", RED_DK,
          "KYIV BLOCK HIT, 14 MISSING",
          "Russian drone flattens a five-storey block in Dymer; 2 dead, "
          "rescuers dig through floors 1 to 5. Zelensky urges Patriot aid.",
          scene=scene_kyiv, scene_h=52)
    # ---- middle row
    panel(buf, 16, 492, 322, 186, "GULF . HORMUZ", TEAL,
          "IRAN SAYS TWO TANKERS HIT MINES",
          "Tehran claims two supertankers struck mines near Ghanam island "
          "and caught fire. Not independently verified; operators silent.",
          scene=scene_hormuz)
    panel(buf, 350, 492, 322, 186, "INDONESIA . CIKANDE", ORANGE,
          "CANDY FACTORY FIRE: 24 BODIES FOUND",
          "Bodies recovered after the Cikande blaze in Banten; dozens still "
          "missing as searchers return on Monday. Toll unconfirmed.",
          scene=scene_factory)
    panel(buf, 684, 492, 324, 186, "SUDAN . KHARTOUM", (70, 60, 88),
          "DRONES HIT KHARTOUM: 4 DEAD",
          "Pre-dawn strikes damage a UN building with staff inside; a home "
          "in Omdurman destroyed, a 10-year-old among the dead.",
          scene=scene_sudan)
    # ---- lower row
    panel(buf, 16, 688, 322, 186, "WEST BANK . RAMALLAH", (96, 78, 60),
          "SETTLERS TORCH 12 CARS, TALKS STALL",
          "Palestinian cars burned in four villages overnight; Israel's "
          "opposition calls it Jewish terrorism. Coalition talks fail.",
          scene=scene_westbank)
    panel(buf, 350, 688, 322, 186, "SPACE . MERCURY", (20, 30, 60),
          "BEPICOLOMBO REACHES MERCURY",
          "After eight years and a 37-minute burn, the ESA-JAXA craft is "
          "only the second mission ever to orbit Mercury. Science in 2027.",
          scene=scene_mercury)
    panel(buf, 684, 688, 324, 186, "SOUTH KOREA . SEOUL", (36, 58, 92),
          "MINISTER QUITS OVER AI EXAM CHEAT",
          "Education minister resigns as an AI-assisted exam cheating "
          "scandal spreads; the test system faces a credibility crisis.",
          scene=scene_exam)
    # ---- footer strip
    fx, fy, fw, fh = 16, 884, 992, 124
    _fill(buf, fx, fy, fw, fh, NAVY)
    _fill(buf, fx, fy, fw, 3, GOLD)
    draw_text(buf, fx + 12, fy + 12, "ALSO TODAY", 2, GOLD_LT)
    draw_text(buf, fx + 150, fy + 14, "HOUTHI CLAIM STRIKE ON RABIGH REFINERY, SAUDI ARABIA",
              1, WHITE)
    draw_text(buf, fx + 150, fy + 30, "ENGLAND TO BE CONFIRMED AS 2035 WOMEN'S WORLD CUP HOST",
              1, WHITE)
    draw_text(buf, fx + 150, fy + 46, "SHURI CASTLE MAIN HALL REOPENS IN OKINAWA, 7 YEARS AFTER FIRE",
              1, WHITE)
    draw_text(buf, fx + 12, fy + 66, "LAHORE WORLD'S MOST POLLUTED CITY, AQI 538",
              1, WHITE)
    draw_text(buf, fx + 12, fy + 82, "NIGERIA BOAT ACCIDENT DEATH TOLL RISES TO 24",
              1, WHITE)
    draw_text(buf, fx + 12, fy + 98, "US DEFENCE CHIEF CURBS TIES WITH CANADA IN SECRET MEMO",
              1, WHITE)
    draw_text(buf, fx + 560, fy + 66, "15 STORIES . 7 REGIONS", 2, GOLD_LT)
    draw_text(buf, fx + 560, fy + 92, "MONDAY 23 NOVEMBER 2026", 2, WHITE)
    # ---- grain: deterministic paper texture over the whole page
    _grain(buf)
    return buf


def _grain(buf):
    for y in range(H):
        base = y * W * 3
        for x in range(W):
            if (x + y) & 1:
                continue
            h = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
            h ^= (h >> 13)
            n = ((h >> 8) & 3) - 1
            if n:
                off = base + x * 3
                for k in range(3):
                    v = buf[off + k] + n
                    buf[off + k] = 255 if v > 255 else (0 if v < 0 else v)


# ---------------------------------------------------------------- PNG out
def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return c


def write_png(buf, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    buf = build()
    n = write_png(buf, path)
    print(f"wrote {path} ({n} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
