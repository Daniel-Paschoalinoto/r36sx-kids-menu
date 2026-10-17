"""Drawing building blocks shared by all screens.  / Peças de desenho usadas por todas as telas.

Everything is drawn at 3x size and scaled down (anti-aliasing).  No third-party artwork or fonts are used:
the default font is the one bundled with Pillow, and the pictures are drawn with code.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 640, 480
WHITE = (255, 255, 255, 255)


class Theme:
    """Colours + fonts + texts + pictures for one build."""

    def __init__(self, cfg, strings):
        self.cfg = cfg
        self.t = strings
        p = cfg.palette
        self.sky_top, self.sky_bottom = p.sky_top, p.sky_bottom
        self.panel = p.panel
        self.accent = p.accent
        self.outline = p.outline
        self.highlight = p.highlight
        self.dark = tuple(min(255, int(c * 1.25) + 6) for c in p.outline)  # text on the accent-coloured pill
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}
        from .. import __version__
        self.version_label = "Kids Menu v%s" % __version__

    def deco(self, size: int) -> Image.Image:
        """Little decoration scattered on the screens (a star; subclasses may draw something else)."""
        return star(self, size)

    # ---- fonts -------------------------------------------------------------------------------
    def font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            path = self.cfg.font
            if path:
                self._font_cache[size] = ImageFont.truetype(str(path), size)
            else:
                self._font_cache[size] = ImageFont.load_default(size)
        return self._font_cache[size]

    def fit_font(self, text: str, size: int, max_w: int, min_size: int = 10):
        while size > min_size and self.font(size).getlength(text) > max_w:
            size -= 1
        return self.font(size)

    # ---- colours with alpha ------------------------------------------------------------------
    def rgba(self, name: str, alpha: int = 255):
        return tuple(getattr(self, name)) + (alpha,)


def ss(draw_fn, size, scale=3):
    im = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im), scale)
    return im.resize(size, Image.LANCZOS)


def gradient(top, bottom, w=W, h=H) -> Image.Image:
    t = np.linspace(0, 1, h)[:, None]
    top, bottom = np.array(top, float), np.array(bottom, float)
    col = (top + (bottom - top) * t)[:, None, :].repeat(w, axis=1)
    return Image.fromarray(col.astype(np.uint8), "RGB").convert("RGBA")


def sky(theme: Theme) -> Image.Image:
    """Gradient sky + soft clouds + a grassy hill at the bottom."""
    im = gradient(theme.sky_top, theme.sky_bottom)
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cl)
    for cx, cy, s in [(380, 60, 1.0), (560, 40, 0.7), (330, 150, 0.6)]:
        for dx, dy, r in [(-40, 10, 28), (0, 0, 38), (42, 8, 30), (-10, 14, 32), (20, 14, 30)]:
            d.ellipse((cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s),
                      fill=(255, 255, 255, 200))
    im = Image.alpha_composite(im, cl.filter(ImageFilter.GaussianBlur(2)))
    hill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(hill)
    d.ellipse((-120, 410, 420, 700), fill=(52, 170, 60, 255))
    d.ellipse((220, 430, 800, 720), fill=(66, 190, 70, 255))
    d.rectangle((0, 455, W, H), fill=(120, 72, 30, 255))
    for i in range(0, W, 40):
        d.rectangle((i, 455, i + 20, 467), fill=(150, 92, 40, 255))
    d.rectangle((0, 448, W, 456), fill=(60, 190, 66, 255))
    return Image.alpha_composite(im, hill)


def star(theme: Theme, size=40) -> Image.Image:
    """Little five-point star used as decoration."""
    def f(d, s):
        c, r1, r2 = size * s / 2, size * s * 0.48, size * s * 0.2
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = r1 if i % 2 == 0 else r2
            pts.append((c + r * math.cos(ang), c + r * math.sin(ang)))
        d.polygon(pts, fill=theme.rgba("accent"), outline=(255, 255, 255, 255))
        d.line(pts + [pts[0]], fill=(255, 255, 255, 255), width=int(1.5 * s), joint="curve")
    return ss(f, (size, size))


def add_stars(im, theme, pts):
    for x, y, s in pts:
        im.alpha_composite(theme.deco(s), (x, y))
    return im


def shadow(card, blur=8, alpha=120):
    pad = blur * 3
    sh = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    a = card.split()[3].point(lambda v: min(v, alpha))
    blk = Image.new("RGBA", card.size, (0, 0, 40, 255))
    blk.putalpha(a)
    sh.alpha_composite(blk, (pad, pad))
    return sh.filter(ImageFilter.GaussianBlur(blur)), pad


def framed_card(src: Image.Image, angle: float, border=7, radius=16) -> Image.Image:
    """Picture in a white rounded frame, tilted, with a drop shadow."""
    w, h = src.size
    S = 3
    cw, ch = w + border * 2, h + border * 2
    mask = Image.new("L", (cw * S, ch * S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw * S - 1, ch * S - 1), radius=(radius + 6) * S, fill=255)
    mask = mask.resize((cw, ch), Image.LANCZOS)
    m2 = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(m2).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=radius * S, fill=255)
    m2 = m2.resize((w, h), Image.LANCZOS)
    card = Image.new("RGBA", (cw, ch), WHITE)
    card.paste(src.convert("RGB"), (border, border), m2)
    card.putalpha(mask)
    card = card.rotate(angle, resample=Image.BICUBIC, expand=True)
    sh, pad = shadow(card)
    out = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (6, 8))
    out.alpha_composite(card, (pad, pad))
    return out


def outlined_text(im, xy, text, font, fill, outline, ow=4, anchor="lm"):
    ImageDraw.Draw(im).text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=ow, stroke_fill=outline)


def panel(im, box, fill, outline=WHITE, width=3, radius=22):
    S = 3
    w, h = box[2] - box[0], box[3] - box[1]
    p = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=radius * S, fill=fill, outline=outline,
                                        width=width * S)
    im.alpha_composite(p.resize((w, h), Image.LANCZOS), (box[0], box[1]))


# ---- pictures supplied by the user (or placeholders) -----------------------------------------------
def cover_crop(src: Image.Image, ratio: float, fx=0.5, fy=0.5, zoom=1.0) -> Image.Image:
    """Crop ``src`` to width/height == ratio around focus (fx, fy), then zoom in."""
    src = ImageOps.exif_transpose(src).convert("RGB")
    w, h = src.size
    cw, ch = (w, w / ratio) if w / h < ratio else (h * ratio, h)
    cw, ch = cw / zoom, ch / zoom
    x0 = min(max(fx * w - cw / 2, 0), w - cw)
    y0 = min(max(fy * h - ch / 2, 0), h - ch)
    return src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))


def placeholder_picture(theme: Theme, kind: str, size) -> Image.Image:
    """A drawn stand-in used when the user did not provide a picture.  kind: 'mascot' or 'photo'."""
    w, h = size
    im = gradient((255, 214, 120), (255, 140, 90), w, h)
    d = ImageDraw.Draw(im)
    if kind == "photo":  # person silhouette
        d.ellipse((w * 0.34, h * 0.14, w * 0.66, h * 0.46), fill=(255, 255, 255, 255))
        d.ellipse((w * 0.14, h * 0.52, w * 0.86, h * 1.25), fill=(255, 255, 255, 255))
    else:  # game pad
        d.rounded_rectangle((w * 0.12, h * 0.25, w * 0.88, h * 0.78), radius=int(h * 0.2), fill=(70, 80, 210, 255),
                            outline=WHITE, width=5)
        d.rectangle((w * 0.24, h * 0.46, w * 0.40, h * 0.54), fill=WHITE)
        d.rectangle((w * 0.29, h * 0.40, w * 0.35, h * 0.60), fill=WHITE)
        d.ellipse((w * 0.58, h * 0.42, w * 0.67, h * 0.51), fill=(255, 70, 70, 255))
        d.ellipse((w * 0.68, h * 0.50, w * 0.77, h * 0.59), fill=(70, 220, 90, 255))
    label = theme.t["placeholder.photo" if kind == "photo" else "placeholder.mascot"]
    f = theme.fit_font(label, 20, w - 16)
    d.text((w / 2, h - 18), label, font=f, fill=WHITE, anchor="mm", stroke_width=2, stroke_fill=(120, 50, 20))
    return im.convert("RGB")


def user_picture(path: Path | None, ratio: float, size, theme: Theme, kind: str, fx=0.5, fy=0.5, zoom=1.0):
    if path:
        try:
            with Image.open(path) as src:
                crop = cover_crop(src, ratio, fx, fy, zoom)
            return crop.resize(size, Image.LANCZOS)
        except Exception as exc:  # unreadable picture -> placeholder, but tell the user
            print("  ! cannot read %s (%s) -> using the placeholder / usando a imagem padrão" % (path, exc))
    return placeholder_picture(theme, kind, size)
