"""Generate the Kaggle Writeup cover banner for Course Architect.

Two variants at 1200x630 (standard cover/social ratio), using the project's
deck theme colours (navy 1F3A5F, blue 2E86C1) and the EQV eagle as a brand mark.
  cover_light.png  - white/corporate (matches the deck's title slide)
  cover_navy.png   - navy hero (pops harder as a gallery thumbnail)
Run:  python make_cover.py
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EAGLE = r"C:\Projects\EQV Courses\_Assets\_Brand\Eagle emblem with laurel wreath.png"
W, H = 1200, 630

NAVY  = (31, 58, 95)
BLUE  = (46, 134, 193)
BODY  = (34, 40, 49)
MUTED = (107, 114, 128)
WHITE = (255, 255, 255)
LIGHTBLUE = (150, 200, 235)

F = "C:/Windows/Fonts/"
def font(name, size): return ImageFont.truetype(F + name, size)
TITLE = lambda s: font("calibrib.ttf", s)
BODYF = lambda s: font("calibri.ttf", s)
LIGHT = lambda s: font("calibril.ttf", s)


def eagle_rgba(white_logo=False):
    """Eagle with its white background knocked out; optionally recoloured white."""
    im = Image.open(EAGLE).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r > 238 and g > 238 and b > 238:
                px[x, y] = (0, 0, 0, 0)              # drop near-white bg
            elif white_logo:
                px[x, y] = (255, 255, 255, a)        # recolour mark to white
    return im


def tracked(draw, xy, text, fnt, fill, spacing=2):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_visual(d, x, y, dark_bg):
    """outline card -> AI arrow -> slide deck."""
    line_c = WHITE if dark_bg else NAVY
    card_fill = (255, 255, 255, 255) if not dark_bg else (255, 255, 255)
    # outline card
    d.rounded_rectangle([x, y, x + 210, y + 150], radius=10,
                        fill=WHITE, outline=BLUE, width=3)
    d.rectangle([x + 22, y + 26, x + 150, y + 38], fill=NAVY)        # title line
    for i in range(3):
        yy = y + 60 + i * 26
        d.ellipse([x + 24, yy, x + 34, yy + 10], fill=BLUE)          # bullet
        d.rectangle([x + 44, yy + 1, x + 186, yy + 9], fill=MUTED)
    # arrow + AI label
    ax0, ax1, ay = x + 230, x + 330, y + 75
    d.line([ax0, ay, ax1, ay], fill=BLUE, width=6)
    d.polygon([(ax1, ay - 12), (ax1 + 20, ay), (ax1, ay + 12)], fill=BLUE)
    d.ellipse([x + 258, ay - 46, x + 302, ay - 2], fill=NAVY)
    aif = TITLE(20)
    d.text((x + 280 - d.textlength("AI", font=aif) / 2, ay - 40), "AI",
           font=aif, fill=WHITE)
    # slide deck (stacked)
    bx, by = x + 372, y + 8
    for i in range(2, -1, -1):
        ox, oy = bx + i * 16, by + i * 16
        d.rounded_rectangle([ox, oy, ox + 200, oy + 134], radius=8,
                            fill=WHITE, outline=NAVY, width=3)
        d.rounded_rectangle([ox, oy, ox + 200, oy + 26], radius=8, fill=BLUE)
        d.rectangle([ox, oy + 18, ox + 200, oy + 26], fill=BLUE)
        if i == 0:
            for k in range(3):
                yy = oy + 50 + k * 22
                d.ellipse([ox + 18, yy, ox + 26, yy + 8], fill=BLUE)
                d.rectangle([ox + 34, yy + 1, ox + 176, yy + 7], fill=MUTED)


def build(dark_bg: bool, out: str):
    bg = NAVY if dark_bg else WHITE
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    title_c = WHITE if dark_bg else NAVY
    body_c  = (220, 230, 240) if dark_bg else BODY
    eyebrow_c = LIGHTBLUE if dark_bg else BLUE

    # top accent bar (like the deck content slides)
    d.rectangle([0, 0, W, 12], fill=BLUE)

    # eyebrow
    tracked(d, (64, 58), "GOOGLE  ×  KAGGLE   ·   5-DAY AI AGENTS INTENSIVE   ·   AGENTS FOR BUSINESS",
            BODYF(20), eyebrow_c, spacing=2)

    # title
    d.text((60, 96), "Course Architect", font=TITLE(96), fill=title_c)

    # tagline (wrapped)
    tag = ("An AI agent that turns a short outline into a finished, branded "
           "course deck — and checks every point landed. 100% coverage.")
    yy = 232
    for ln in wrap(d, tag, BODYF(33), 760):
        d.text((64, yy), ln, font=BODYF(33), fill=body_c)
        yy += 44

    # the outline -> deck visual
    draw_visual(d, 64, 360, dark_bg)

    # eagle brand mark (bottom-right). The emblem already carries the
    # "EQV - Your Learning Partner" wordmark, so no extra caption.
    eg = eagle_rgba(white_logo=dark_bg)
    side = 248
    eg = eg.resize((side, side), Image.LANCZOS)
    img.paste(eg, (W - side - 40, H - side - 22), eg)

    img.save(os.path.join(HERE, out))
    print("wrote", out)


if __name__ == "__main__":
    build(dark_bg=False, out="cover_light.png")
    build(dark_bg=True,  out="cover_navy.png")
