#!/usr/bin/env python3
"""THE WORLD TODAY -- Thursday 26 November 2026, in one image.

Pure-stdlib Python 3.13. Draws a one-page newspaper front page summing
up the world's news of Thursday 26 November 2026 and writes it to
/output/entry.png (1024x1024 PNG, under 1 MiB). Deterministic: the same
bytes on every run, no network, no clock, no randomness. Text comes from
bitmap glyphs in font_data.py (DejaVu Sans Book + Bold at one 64px base
size, scaled at runtime with stroke-preserving max sampling so thin
strokes never drop out at small sizes).

Output directory: $MAKEFUN_OUTPUT_DIR, or "out" when unset.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from font_data import FONTS

W = 1024
H = 1024
PAPER = (247, 243, 232)
INK = (22, 22, 22)
RED = (172, 32, 26)
GRAY = (105, 100, 90)
NAVY = (24, 42, 72)
SKY = (176, 205, 226)
GOLD = (214, 158, 44)
ORANGE = (224, 110, 30)
WHITE = (245, 245, 240)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self):
        self.px = bytearray(W * H * 3)
        for i in range(0, len(self.px), 3):
            self.px[i] = PAPER[0]
            self.px[i + 1] = PAPER[1]
            self.px[i + 2] = PAPER[2]
        self.clip = (0, 0, W, H)

    def set_clip(self, x, y, w, h):
        self.clip = (x, y, x + w, y + h)

    def clear_clip(self):
        self.clip = (0, 0, W, H)

    def put(self, x, y, color):
        cx0, cy0, cx1, cy1 = self.clip
        if x < cx0 or x >= cx1 or y < cy0 or y >= cy1:
            return
        i = (y * W + x) * 3
        self.px[i] = color[0]
        self.px[i + 1] = color[1]
        self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            for xx in range(cx - dx, cx + dx + 1):
                self.put(xx, cy + dy, color)

    def ring(self, cx, cy, r, color, thick=2):
        self.disc(cx, cy, r, color)
        self.disc(cx, cy, r - thick, PAPER)

    def poly(self, pts, color):
        # Even-odd scanline fill.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.put(xx, y, color)

    def burst(self, cx, cy, r, color):
        # Explosion starburst: disc plus radiating spikes.
        self.disc(cx, cy, r, color)
        dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),
                (-1, 0), (-1, -1), (0, -1), (1, -1)]
        for dx, dy in dirs:
            x1 = cx + int(r * 1.7 * dx)
            y1 = cy + int(r * 1.7 * dy)
            self.line(cx, cy, x1, y1, color)
            self.line(cx + 1, cy, x1 + 1, y1, color)


# ------------------------------------------------------------------- text
_cache = {}


def scaled_glyph(font, code, size):
    key = (font, code, size)
    got = _cache.get(key)
    if got is not None:
        return got
    adv, yoff, rows = FONTS[font][code]
    w = 0
    for r in rows:
        if r.bit_length() > w:
            w = r.bit_length()
    if not rows or w == 0:
        out = (adv * size // 64, 0, [], 0)
        _cache[key] = out
        return out
    h = len(rows)
    ow = max(1, (w * size + 63) // 64)
    oh = max(1, (h * size + 63) // 64)
    out_rows = []
    for oy in range(oh):
        sy0 = oy * 64 // size
        sy1 = (oy + 1) * 64 // size
        if sy1 <= sy0:
            sy1 = sy0 + 1
        if sy1 > h:
            sy1 = h
        bits = 0
        for ox in range(ow):
            sx0 = ox * 64 // size
            sx1 = (ox + 1) * 64 // size
            if sx1 <= sx0:
                sx1 = sx0 + 1
            if sx1 > w:
                sx1 = w
            mask = ((1 << (sx1 - sx0)) - 1) << (w - sx1)
            inked = False
            for sy in range(sy0, sy1):
                if rows[sy] & mask:
                    inked = True
                    break
            if inked:
                bits |= 1 << (ow - 1 - ox)
        out_rows.append(bits)
    out = (adv * size // 64, yoff * size // 64, out_rows, ow)
    _cache[key] = out
    return out


def text_width(s, font, size):
    total = 0
    for ch in s:
        total += scaled_glyph(font, ord(ch), size)[0]
    return total


def draw_text(cv, x, y_baseline, s, font, size, color):
    cx = x
    for ch in s:
        adv, yoff, rows, ow = scaled_glyph(font, ord(ch), size)
        if rows:
            top = y_baseline + yoff
            for dy, bits in enumerate(rows):
                b = bits
                while b:
                    low = b & -b
                    ox = ow - 1 - (low.bit_length() - 1)
                    cv.put(cx + ox, top + dy, color)
                    b ^= low
        cx += adv
    return cx


def draw_centered(cv, cx, y_baseline, s, font, size, color):
    draw_text(cv, cx - text_width(s, font, size) // 2, y_baseline, s,
              font, size, color)


def wrap(s, font, size, width):
    lines = []
    cur = ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, font, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y_first, s, font, size, width, leading, color=INK):
    y = y_first
    for line in wrap(s, font, size, width):
        draw_text(cv, x, y, line, font, size, color)
        y += leading
    return y


# -------------------------------------------------------------------- art
def jet(cv, cx, cy, s, color):
    # Simple top-view jet silhouette, nose pointing right.
    pts = [
        (cx - 3 * s, cy),
        (cx - 2 * s, cy - s),
        (cx + 2 * s, cy - s),
        (cx + 4 * s, cy),
        (cx + 2 * s, cy + s),
        (cx - 2 * s, cy + s),
    ]
    cv.poly(pts, color)
    cv.line(cx - 3 * s, cy, cx - 5 * s, cy - 2 * s, color)
    cv.line(cx - 3 * s, cy, cx - 5 * s, cy + 2 * s, color)


def lead_art(cv, x, y, w, h):
    cv.set_clip(x, y, w, h)
    cv.rect(x, y, w, h, NAVY)
    stars = [(18, 12), (52, 30), (96, 10), (140, 26), (188, 14),
             (232, 32), (276, 12), (318, 28), (348, 10), (74, 44),
             (210, 48), (300, 44)]
    for sx, sy in stars:
        cv.put(x + sx, y + sy, WHITE)
        cv.put(x + sx + 1, y + sy, WHITE)
    # Ground and runway.
    cv.rect(x, y + h - 26, w, 26, (52, 48, 44))
    cv.line(x, y + h - 26, x + w, y + h - 40, (200, 196, 186))
    cv.line(x, y + h - 18, x + w, y + h - 32, (150, 146, 136))
    # Jets on the ground.
    jet(cv, x + 60, y + h - 12, 4, (210, 206, 196))
    jet(cv, x + 150, y + h - 14, 4, (210, 206, 196))
    jet(cv, x + 250, y + h - 12, 4, (210, 206, 196))
    # Two hits: bursts and smoke.
    cv.burst(x + 105, y + 58, 10, ORANGE)
    cv.disc(x + 105, y + 58, 6, GOLD)
    cv.burst(x + 265, y + 42, 8, ORANGE)
    cv.disc(x + 265, y + 42, 5, GOLD)
    cv.disc(x + 118, y + 40, 9, (120, 118, 112))
    cv.disc(x + 132, y + 30, 7, (140, 138, 132))
    cv.disc(x + 278, y + 26, 8, (120, 118, 112))
    cv.clear_clip()


def space_art(cv, x, y, w, h):
    cv.set_clip(x, y, w, h)
    cv.rect(x, y, w, h, NAVY)
    stars = [(14, 10), (44, 26), (80, 8), (120, 22), (160, 12),
             (200, 28), (240, 10), (276, 24), (60, 46), (180, 48),
             (230, 52), (30, 60), (110, 60)]
    for sx, sy in stars:
        cv.put(x + sx, y + sy, WHITE)
    # Orbit arc.
    cv.ring(x + w // 2, y + h + 130, 170, (150, 170, 205), 2)
    # Three satellites: body plus panels.
    for sx, sy in [(52, 34), (150, 22), (238, 40)]:
        cv.rect(x + sx - 16, y + sy - 3, 10, 6, SKY)
        cv.rect(x + sx - 2, y + sy - 5, 8, 10, GOLD)
        cv.rect(x + sx + 8, y + sy - 3, 10, 6, SKY)
        cv.line(x + sx - 16, y + sy, x + sx + 18, y + sy, WHITE)
    # Earth arc at the bottom.
    cv.disc(x + w // 2, y + h + 118, 150, (52, 96, 148))
    cv.disc(x + w // 2, y + h + 118, 138, NAVY)
    cv.clear_clip()


# ------------------------------------------------------------------ page
def build():
    cv = Canvas()
    MX = 36
    CW = 952  # 36..988
    # Masthead.
    cv.hline(MX, 26, CW, INK, 2)
    draw_centered(cv, 512, 96, "THE WORLD TODAY", "bold", 60, INK)
    draw_centered(cv, 512, 126,
                  "THURSDAY, 26 NOVEMBER 2026  -  THE DAY'S NEWS IN ONE PAGE",
                  "bold", 17, INK)
    cv.hline(MX, 136, CW, INK, 4)
    cv.hline(MX, 143, CW, INK, 1)

    # Lead story: Ukraine strikes the Savasleyka airbase.
    draw_text(cv, MX, 178, "WAR IN UKRAINE", "bold", 16, RED)
    draw_text(cv, MX, 216, "UKRAINE HITS RUSSIAN AIRBASE,", "bold", 33, INK)
    draw_text(cv, MX, 256, "FIVE WARPLANES DAMAGED", "bold", 33, INK)
    draw_text(cv, MX, 290,
              "Kyiv says the jets were used to fire missiles at Ukraine; Moscow hits back at the capital.",
              "book", 18, GRAY)
    body = ("Ukrainian forces struck the Savasleyka airbase deep inside Russia, "
            "damaging five military jets, Kyiv said. The base is home to MiG-31 "
            "jets that launch Kinzhal missiles at Ukraine. Russia answered with "
            "ballistic missiles on Kyiv as its strikes on the power grid killed "
            "at least five people.")
    para(cv, MX, 326, body, "book", 16, 556, 21)
    lead_art(cv, 624, 300, 364, 124)
    draw_text(cv, 624, 442,
              "Savasleyka airbase: Kyiv says five jets were hit.",
              "book", 12, GRAY)
    cv.hline(MX, 458, CW, INK, 2)

    # Three columns.
    cols = [
        (36, "ISRAEL",
         ["JUDGES URGE DROP", "OF NETANYAHU", "BRIBERY CASE"],
         "Israeli judges recommended prosecutors drop the most serious "
         "bribery charge against caretaker prime minister Benjamin "
         "Netanyahu, saying there was little chance of conviction in the "
         "case known as Case 4000."),
        (362, "SPACE",
         ["U.S. CLEARS SPACEX", "PLAN FOR A MILLION", "SATELLITES"],
         "Regulators approved SpaceX's Starmind constellation of up to one "
         "million satellites to serve as orbital data centres, the largest "
         "network of its kind ever cleared."),
        (688, "AFRICA",
         ["30 KILLED IN", "NIGERIA ATTACK;", "EBOLA CREWS RESCUED"],
         "Suspected militants killed at least 30 people in Nigeria's "
         "Niger state, residents said. In eastern Congo, UN peacekeepers "
         "evacuated Ebola response workers trapped by fighting."),
    ]
    for cx, kicker, head, body in cols:
        draw_text(cv, cx, 500, kicker, "bold", 14, RED)
        hy = 528
        for line in head:
            draw_text(cv, cx, hy, line, "bold", 21, INK)
            hy += 26
    # Space art sits between the headline and the body of column 2.
    space_art(cv, 362, 596, 301, 104)
    para(cv, 36, 606, cols[0][3], "book", 15, 301, 20)
    para(cv, 688, 606, cols[2][3], "book", 15, 301, 20)
    para(cv, 362, 720, cols[1][3], "book", 15, 301, 20)
    cv.hline(MX, 806, CW, INK, 2)

    # Asia strip.
    draw_text(cv, MX, 830, "ASIA", "bold", 14, RED)
    draw_text(cv, MX, 862,
              "KIM CALLS FOR MORE NUCLEAR WEAPONS; SEOUL RAISES RATES",
              "bold", 23, INK)
    para(cv, MX, 892,
         "North Korea's Kim Jong Un called for wider deployment of tactical "
         "nuclear weapons across several domains, state media said. South "
         "Korea's central bank raised interest rates and lifted its 2027 "
         "growth outlook.",
         "book", 15, CW, 20)
    cv.hline(MX, 928, CW, INK, 1)

    # Also line.
    draw_text(cv, MX, 954, "ALSO TODAY: ", "bold", 14, INK)
    ax = MX + text_width("ALSO TODAY: ", "bold", 14)
    para(cv, ax, 954,
         "Duran Duran guitarist Andy Taylor dies at 65. South Africa's "
         "Ramaphosa wins reprieve from the Farmgate impeachment inquiry. "
         "Bangladesh raises garment workers' pay 36%. Macy's postpones its "
         "Thanksgiving parade as storms hit the U.S.",
         "book", 14, CW - (ax - MX), 19)

    # Footer.
    draw_centered(cv, 512, 1006,
                  "THE WORLD TODAY - THURSDAY, 26 NOVEMBER 2026",
                  "book", 12, GRAY)
    return cv


def encode_png(cv):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    for tag, data in ((b"IHDR", ihdr),
                      (b"IDAT", zlib.compress(bytes(raw), 9)),
                      (b"IEND", b"")):
        out += struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return bytes(out)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
