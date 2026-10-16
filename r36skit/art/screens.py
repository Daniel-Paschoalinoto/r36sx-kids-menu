"""All the full-screen pictures (640x480) and the little pieces cut out of them.

Todas as telas (640x480) e os recortes menores. The positions of the buttons/rows come from the
console's own ``.raw`` files (they contain the rectangles), so the layout always matches the firmware.
"""
from __future__ import annotations

import struct
import zipfile

from PIL import Image, ImageDraw

from .draw import (H, W, WHITE, Theme, add_stars, framed_card, gradient, outlined_text, panel, sky, ss,
                   user_picture)
from .rgb565 import enc


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def read_ents(d: bytes):
    """Entries of a .raw sheet: (offset, x0, y0, x1, y1).  Entry 0 is the full background."""
    header = struct.unpack_from("<I", d, 0)[0]
    out = []
    for i in range(header // 16):
        off, _size, a, b = struct.unpack_from("<4I", d, i * 16)
        out.append((off, a & 0xFFFF, a >> 16, b & 0xFFFF, b >> 16))
    return out


def mascot_card(theme: Theme, width: int, angle: float) -> Image.Image:
    size = (width, width * 3 // 4)
    pic = user_picture(theme.cfg.mascot, 4 / 3, size, theme, "mascot")
    return framed_card(pic, angle)


def photo_card(theme: Theme, width: int, angle: float) -> Image.Image:
    c = theme.cfg
    pic = user_picture(c.photo, 1.0, (width, width), theme, "photo", c.photo_focus[0], c.photo_focus[1], c.photo_zoom)
    return framed_card(pic, angle, border=8, radius=19)


# ---------------------------------------------------------------------------------------------
# small icons
# ---------------------------------------------------------------------------------------------
def icon_video(sz=46):
    def f(d, s):
        k = sz * s
        d.rounded_rectangle((3 * s, 8 * s, k - 3 * s, k - 8 * s), radius=8 * s, fill=(235, 50, 60, 255), outline=WHITE,
                            width=3 * s)
        d.polygon([(k * 0.40, k * 0.32), (k * 0.40, k * 0.68), (k * 0.70, k * 0.5)], fill=WHITE)
    return ss(f, (sz, sz))


def icon_music(sz=46):
    gold = (255, 205, 0, 255)

    def f(d, s):
        k = sz * s
        d.ellipse((k * 0.14, k * 0.60, k * 0.46, k * 0.88), fill=gold, outline=WHITE, width=2 * s)
        d.ellipse((k * 0.54, k * 0.50, k * 0.86, k * 0.78), fill=gold, outline=WHITE, width=2 * s)
        d.rectangle((k * 0.40, k * 0.18, k * 0.48, k * 0.74), fill=gold, outline=WHITE, width=2 * s)
        d.rectangle((k * 0.78, k * 0.08, k * 0.86, k * 0.64), fill=gold, outline=WHITE, width=2 * s)
        d.polygon([(k * 0.40, k * 0.18), (k * 0.86, k * 0.08), (k * 0.86, k * 0.26), (k * 0.40, k * 0.36)], fill=gold,
                  outline=WHITE)
    return ss(f, (sz, sz))


def icon_photo(sz=46):
    def f(d, s):
        k = sz * s
        d.rounded_rectangle((3 * s, 6 * s, k - 3 * s, k - 6 * s), radius=7 * s, fill=(120, 210, 255, 255), outline=WHITE,
                            width=3 * s)
        d.ellipse((k * 0.62, k * 0.20, k * 0.82, k * 0.40), fill=(255, 214, 40, 255))
        d.polygon([(k * 0.10, k * 0.80), (k * 0.38, k * 0.42), (k * 0.58, k * 0.68), (k * 0.70, k * 0.55),
                   (k * 0.90, k * 0.80)], fill=(60, 180, 70, 255))
    return ss(f, (sz, sz))


def icon_pad(sz=64):
    def f(d, s):
        k = sz * s
        d.rounded_rectangle((2 * s, k * 0.22, k - 2 * s, k * 0.80), radius=k * 0.22, fill=(60, 70, 200, 255),
                            outline=WHITE, width=3 * s)
        d.rectangle((k * 0.16, k * 0.45, k * 0.40, k * 0.56), fill=WHITE)
        d.rectangle((k * 0.22, k * 0.38, k * 0.34, k * 0.64), fill=WHITE)
        d.ellipse((k * 0.60, k * 0.40, k * 0.72, k * 0.52), fill=(255, 70, 70, 255))
        d.ellipse((k * 0.72, k * 0.50, k * 0.84, k * 0.62), fill=(70, 220, 90, 255))
    return ss(f, (sz, sz))


# ---------------------------------------------------------------------------------------------
# main menu (Movie / Music / Photo backgrounds) and GAMES page   ->  UI_Res.cpd
# ---------------------------------------------------------------------------------------------
ROWS = [140, 205, 270]  # centre Y of the three sidebar rows (same as the firmware)
ICONS = [icon_video, icon_music, icon_photo]


def sidebar(im, theme, selected):
    for i, cy in enumerate(ROWS):
        box = (14, cy - 28, 292, cy + 28)
        S = 3
        pill = Image.new("RGBA", ((box[2] - box[0]) * S, (box[3] - box[1]) * S), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        if i == selected:
            pd.rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), radius=28 * S, fill=theme.rgba("accent", 245),
                                 outline=WHITE, width=5 * S)
        else:
            pd.rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), radius=28 * S,
                                 fill=theme.rgba("panel", 120), outline=(255, 255, 255, 130), width=2 * S)
        im.alpha_composite(pill.resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS), (box[0], box[1]))
        im.alpha_composite(ICONS[i](46), (box[0] + 10, cy - 23))


def tips_box(im, theme, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    panel(im, box, theme.rgba("panel", 200), theme.rgba("accent"), 3, 16)
    d = ImageDraw.Draw(im)
    d.text((x0 + 14, y0 + 16), theme.t["tips.title"], font=theme.font(18), fill=theme.accent, anchor="lm")
    lines = theme.t["tips.lines"][:2]
    for i, line in enumerate(lines):
        text = "- " + line
        d.text((x0 + 14, y0 + 42 + i * 21), text, font=theme.fit_font(text, 16, w - 28), fill=WHITE, anchor="lm")


def screen_menu(theme, selected):
    im = sky(theme)
    add_stars(im, theme, [(330, 28, 34), (380, 430, 30), (600, 300, 28), (560, 110, 30)])
    im.alpha_composite(mascot_card(theme, 262, 4), (322, 80))
    add_stars(im, theme, [(300, 300, 34), (318, 360, 30)])
    sidebar(im, theme, selected)
    tips_box(im, theme, (14, 330, 292, 398))
    return im


def screen_games(theme):
    im = sky(theme)
    t = theme.t
    add_stars(im, theme, [(300, 250, 30), (270, 60, 30), (580, 20, 34)])
    im.alpha_composite(mascot_card(theme, 236, -5), (350, 120))
    im.alpha_composite(icon_pad(92), (270, 330))
    outlined_text(im, (22, 130), t["games.title"], theme.fit_font(t["games.title"], 96, 320), theme.accent,
                  theme.outline, 6)
    S = 3
    pill = Image.new("RGBA", (190 * S, 46 * S), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((0, 0, 190 * S - 1, 46 * S - 1), radius=23 * S, fill=(255, 255, 255, 240),
                                           outline=theme.rgba("accent"), width=4 * S)
    im.alpha_composite(pill.resize((190, 46), Image.LANCZOS), (24, 205))
    d = ImageDraw.Draw(im)
    d.ellipse((30, 211, 64, 245), fill=(235, 50, 60, 255), outline=WHITE, width=2)
    d.text((47, 228), "A", font=theme.font(22), fill=WHITE, anchor="mm")
    d.text((78, 228), t["games.enter"], font=theme.fit_font(t["games.enter"], 24, 100), fill=theme.dark, anchor="lm")
    for i, key in enumerate(("games.hint_line1", "games.hint_line2")):
        outlined_text(im, (24, 300 + 32 * i), t[key], theme.fit_font(t[key], 24, 230), WHITE, theme.outline, 3)
    return im


def build_ui_res_backgrounds(theme):
    """name -> BGRA raw bytes for the five full-screen pictures of UI_Res.cpd."""
    shots = {"MovieBg": screen_menu(theme, 0), "MusicBg": screen_menu(theme, 1), "PhotoBg": screen_menu(theme, 2),
             "E-BookBg": screen_menu(theme, 3), "DOWNLOAD": screen_games(theme)}
    return {name: to_bgra(im) for name, im in shots.items()}, shots


def to_bgra(im):
    im = im.convert("RGBA")
    assert im.size == (W, H)
    return im.tobytes("raw", "BGRA")


# ---------------------------------------------------------------------------------------------
# explorer (game list), loading screen, splash   ->  resource.cpd / xgame-logo.bmp
# ---------------------------------------------------------------------------------------------
def explorer_bg(theme):
    t = theme.t
    im = sky(theme)
    panel(im, (8, 8, 632, 72), theme.rgba("panel", 150), (255, 255, 255, 220), 3, 20)
    outlined_text(im, (26, 40), t["explorer.title"], theme.fit_font(t["explorer.title"], 40, 300), theme.accent,
                  theme.outline, 4)
    add_stars(im, theme, [(560, 20, 34), (596, 34, 26)])
    panel(im, (330, 84, 636, 438), theme.rgba("panel", 175), (255, 255, 255, 230), 3, 22)
    panel(im, (38, 141, 302, 405), theme.rgba("panel", 110), (255, 255, 255, 230), 3, 18)  # frame of the 240x240 cover
    outlined_text(im, (170, 430), t["explorer.hint"], theme.fit_font(t["explorer.hint"], 24, 280), WHITE, theme.outline,
                  3, anchor="mm")
    add_stars(im, theme, [(14, 408, 30), (300, 96, 28)])
    return im


def highlight(theme, bg, rect):
    x0, y0, x1, y1 = rect
    im = bg.convert("RGBA").crop(rect)
    w, h = x1 - x0, y1 - y0
    S = 3
    p = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((6 * S, 3 * S, (w - 6) * S, (h - 3) * S), radius=15 * S, fill=theme.rgba("highlight", 245),
                        outline=WHITE, width=2 * S)
    cy = h * S // 2
    d.polygon([(12 * S, cy - 6 * S), (22 * S, cy - 6 * S), (22 * S, cy - 11 * S), (33 * S, cy), (22 * S, cy + 11 * S),
               (22 * S, cy + 6 * S), (12 * S, cy + 6 * S)], fill=theme.rgba("accent"), outline=theme.rgba("outline"))
    im.alpha_composite(p.resize((w, h), Image.LANCZOS))
    return im


def build_menu_raw(theme, stock_menu_raw: bytes):
    d = bytearray(stock_menu_raw)
    ents = read_ents(d)
    bg = explorer_bg(theme).convert("RGB")
    d[ents[0][0]:ents[0][0] + W * H * 2] = enc(bg)
    for k, (off, x0, y0, x1, y1) in enumerate(ents[1:], 1):
        w, h = x1 - x0, y1 - y0
        img = highlight(theme, bg, (x0, y0, x1, y1)).convert("RGB") if k <= 10 else bg.crop((x0, y0, x1, y1))
        raw = enc(img)
        assert len(raw) == w * h * 2
        d[off:off + w * h * 2] = raw
    return bytes(d), bg


def load_bg(theme):
    im = sky(theme)
    add_stars(im, theme, [(60, 60, 40), (540, 80, 36), (100, 380, 36), (520, 360, 40)])
    im.alpha_composite(mascot_card(theme, 180, -4), (230, 20))
    panel(im, (130, 300, 510, 390), theme.rgba("panel", 190), (255, 255, 255, 240), 4, 30)
    text = theme.t["loading"]
    outlined_text(im, (320, 345), text, theme.fit_font(text, 46, 350), theme.accent, theme.outline, 4, anchor="mm")
    return im.convert("RGB")


def splash(theme):
    c, t = theme.cfg, theme.t
    im = sky(theme)
    add_stars(im, theme, [(30, 40, 40), (590, 30, 34), (300, 400, 34), (560, 300, 40), (36, 380, 30)])
    im.alpha_composite(photo_card(theme, 250, -4), (40, 70))
    outlined_text(im, (468, 150), c.splash_big, theme.fit_font(c.splash_big, 92, 330), theme.accent, theme.outline, 7,
                  anchor="mm")
    outlined_text(im, (468, 235), c.splash_small, theme.fit_font(c.splash_small, 54, 330), WHITE, theme.outline, 5,
                  anchor="mm")
    im.alpha_composite(mascot_card(theme, 120, 6), (410, 262))
    tag = t["splash.tagline"]
    outlined_text(im, (300, 446), tag, theme.fit_font(tag, 22, 560), WHITE, theme.outline, 3, anchor="mm")
    return im.convert("RGB")


def no_cover_image(theme):
    """240x240 picture shown for games that have no cover."""
    im = gradient(theme.panel, theme.sky_bottom, 240, 240)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, 233, 233), radius=20, outline=theme.accent, width=4)
    d.ellipse((90, 40, 150, 100), outline=WHITE, width=5)
    d.rectangle((105, 70, 135, 78), fill=WHITE)
    text = theme.t["explorer.no_cover"]
    d.text((120, 170), text, font=theme.fit_font(text, 30, 200), fill=WHITE, anchor="mm")
    return im.convert("RGB")


# ---------------------------------------------------------------------------------------------
# pause menu / save slots / dialogs   ->  resource.cpd + ui_*.cpd (game.raw)
# ---------------------------------------------------------------------------------------------
ROWC = [97, 162, 224, 288]  # centre Y of the 4 pause rows


def circle_key(d, theme, x, label):
    d.ellipse((x, 453, x + 24, 477), outline=WHITE, width=2)
    d.text((x + 12, 465), label, font=theme.font(15), fill=WHITE, anchor="mm")


def footer_bar(im, theme, items):
    """Bottom bar baked into the picture (y 450..480)."""
    im.alpha_composite(Image.new("RGBA", (W, 30), theme.rgba("panel", 235)), (0, 450))
    d = ImageDraw.Draw(im)
    d.line([(0, 450), (W, 450)], fill=(255, 255, 255, 220), width=2)
    for kind, label, x in items:
        if kind == "dpad":
            d.rectangle((x, 459, x + 22, 465), fill=WHITE)
            d.rectangle((x + 8, 452, x + 14, 472), fill=WHITE)
        else:
            circle_key(d, theme, x, kind)
        d.text((x + 32, 465), label, font=theme.fit_font(label, 17, 120), fill=WHITE, anchor="lm")


def pause_texts(theme):
    p = theme.t
    return [p["pause.resume"], p["pause.quit"], p["pause.load"], p["pause.save"]]


def pause_bg(theme):
    p = theme.t
    im = sky(theme)
    add_stars(im, theme, [(600, 14, 30), (20, 400, 30), (250, 20, 26)])
    panel(im, (8, 56, 284, 330), theme.rgba("panel", 175), (255, 255, 255, 230), 3, 22)
    panel(im, (278, 64, 612, 320), theme.rgba("panel", 140), (255, 255, 255, 230), 3, 18)
    outlined_text(im, (22, 30), p["pause.title"], theme.font(30), theme.accent, theme.outline, 4)
    for i, text in enumerate(pause_texts(theme)):
        outlined_text(im, (66, ROWC[i]), text, theme.fit_font(text, 21, 200), WHITE, theme.outline, 3)
    footer_bar(im, theme, [("X", p["pause.footer_delete"], 20), ("dpad", p["pause.footer_select"], 270),
                           ("A", p["pause.footer_ok"], 400), ("B", p["pause.footer_back"], 520)])
    return im.convert("RGB")


def row_patch(theme, bg, rect, k):
    x0, y0, x1, y1 = rect
    im = bg.convert("RGBA").crop(rect)
    w, h = x1 - x0, y1 - y0
    S = 3
    p = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((6 * S, 6 * S, (w - 8) * S, (h - 6) * S), radius=16 * S, fill=theme.rgba("highlight", 245),
                        outline=WHITE, width=2 * S)
    cy = h * S // 2
    d.polygon([(14 * S, cy - 7 * S), (26 * S, cy - 7 * S), (26 * S, cy - 12 * S), (40 * S, cy), (26 * S, cy + 12 * S),
               (26 * S, cy + 7 * S), (14 * S, cy + 7 * S)], fill=theme.rgba("accent"), outline=theme.rgba("outline"))
    im.alpha_composite(p.resize((w, h), Image.LANCZOS))
    text = pause_texts(theme)[k]
    outlined_text(im, (66, ROWC[k] - y0), text, theme.fit_font(text, 21, 200), WHITE, theme.outline, 3)
    return im


def slot_patch(theme, bg, rect, selected):
    x0, y0, x1, y1 = rect
    im = bg.convert("RGBA").crop(rect)
    w, h = x1 - x0, y1 - y0
    S = 3
    p = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle((2 * S, 2 * S, (w - 3) * S, (h - 3) * S), radius=10 * S,
                                        fill=theme.rgba("panel", 215),
                                        outline=theme.rgba("accent") if selected else (255, 255, 255, 200),
                                        width=(4 if selected else 2) * S)
    im.alpha_composite(p.resize((w, h), Image.LANCZOS))
    text = theme.t["pause.slot_empty"]
    ImageDraw.Draw(im).text((w // 2, h // 2), text, font=theme.fit_font(text, 15, w - 10),
                            fill=theme.accent if selected else WHITE, anchor="mm")
    return im


def dialog_patch(theme, bg, rect, lines):
    x0, y0, x1, y1 = rect
    im = bg.convert("RGBA").crop(rect)
    w, h = x1 - x0, y1 - y0
    p = theme.t
    panel(im, (0, 0, w, h), theme.rgba("panel", 240), theme.rgba("accent"), 4, 20)
    d = ImageDraw.Draw(im)
    d.polygon([(52, 22), (88, 84), (16, 84)], fill=theme.accent, outline=theme.outline)
    d.rectangle((50, 40, 54, 62), fill=theme.outline)
    d.ellipse((49, 68, 55, 74), fill=theme.outline)
    for i, line in enumerate(lines):
        d.text((110, 42 + 28 * i), line, font=theme.fit_font(line, 21, w - 120), fill=WHITE, anchor="lm")
    d.ellipse((260, 88, 284, 112), outline=theme.accent, width=2)
    d.text((272, 100), "Y", font=theme.font(15), fill=theme.accent, anchor="mm")
    d.text((292, 100), p["pause.yes"], font=theme.font(20), fill=theme.accent, anchor="lm")
    d.ellipse((370, 88, 394, 112), outline=WHITE, width=2)
    d.text((382, 100), "X", font=theme.font(15), fill=WHITE, anchor="mm")
    d.text((402, 100), p["pause.no"], font=theme.font(20), fill=WHITE, anchor="lm")
    return im


def build_game_raw(theme, stock_game_raw: bytes):
    p = theme.t
    d = bytearray(stock_game_raw)
    ents = read_ents(d)
    bg = pause_bg(theme)
    d[ents[0][0]:ents[0][0] + W * H * 2] = enc(bg)
    for k, (off, x0, y0, x1, y1) in enumerate(ents[1:], 1):
        w, h = x1 - x0, y1 - y0
        rect = (x0, y0, x1, y1)
        if 1 <= k <= 4:
            img = row_patch(theme, bg, rect, k - 1)
        elif 5 <= k <= 10:
            img = slot_patch(theme, bg, rect, False)
        elif 11 <= k <= 16:
            img = slot_patch(theme, bg, rect, True)
        elif k == 17:
            img = dialog_patch(theme, bg, rect, [p["pause.overwrite_line1"], p["pause.overwrite_line2"]])
        else:
            img = dialog_patch(theme, bg, rect, [p["pause.unused_favorite_line1"], p["pause.unused_favorite_line2"]])
        raw = enc(img.convert("RGB"))
        assert len(raw) == w * h * 2
        d[off:off + w * h * 2] = raw
    return bytes(d), bg


# ---------------------------------------------------------------------------------------------
# search keyboard   ->  resource.cpd (search.raw)
# ---------------------------------------------------------------------------------------------
KEYS = list("1234567890") + [" "] + list("ABCDEFGHIJKLMNOPQR") + list("STUV") + ["Clr"] + list("WXYZ") + ["<-"]


def keycap(theme, w, h, label, selected):
    S = 3
    p = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((S, S, (w - 2) * S, (h - 2) * S), radius=10 * S,
                        fill=theme.rgba("accent") if selected else (255, 255, 255, 245),
                        outline=WHITE if selected else theme.rgba("outline"), width=2 * S)
    p = p.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(p)
    col = theme.dark + (255,)
    if label == " ":
        d.line([(w * 0.3, h * 0.55), (w * 0.3, h * 0.68), (w * 0.7, h * 0.68), (w * 0.7, h * 0.55)], fill=col, width=3)
    elif label == "<-":
        d.line([(w * 0.3, h / 2), (w * 0.7, h / 2)], fill=col, width=3)
        d.line([(w * 0.3, h / 2), (w * 0.45, h * 0.35)], fill=col, width=3)
        d.line([(w * 0.3, h / 2), (w * 0.45, h * 0.65)], fill=col, width=3)
    else:
        d.text((w / 2, h / 2 + 1), label, font=theme.font(22 if len(label) == 1 else 18), fill=col, anchor="mm")
    return p


def search_bg(theme, ents):
    im = sky(theme)
    add_stars(im, theme, [(560, 400, 34), (596, 380, 26), (340, 440, 26)])
    im.alpha_composite(mascot_card(theme, 170, 4), (400, 130))
    panel(im, (254, 30, 540, 72), (60, 110, 200, 255), (255, 255, 255, 255), 3, 16)
    d = ImageDraw.Draw(im)
    d.ellipse((498, 40, 518, 60), outline=WHITE, width=3)
    d.line([(516, 58), (528, 68)], fill=WHITE, width=4)
    outlined_text(im, (22, 40), theme.t["search.title"], theme.font(32), theme.accent, theme.outline, 4)
    for k, (_off, x0, y0, x1, y1) in enumerate(ents[1:]):
        if k < len(KEYS):
            im.alpha_composite(keycap(theme, x1 - x0, y1 - y0, KEYS[k], False), (x0, y0))
    return im.convert("RGB")


def build_search_raw(theme, stock_search_raw: bytes):
    d = bytearray(stock_search_raw)
    ents = read_ents(d)
    bg = search_bg(theme, ents)
    d[ents[0][0]:ents[0][0] + W * H * 2] = enc(bg)
    for k, (off, x0, y0, x1, y1) in enumerate(ents[1:], 1):
        w, h = x1 - x0, y1 - y0
        base = bg.convert("RGBA").crop((x0, y0, x1, y1))
        if k - 1 < len(KEYS):
            base.alpha_composite(keycap(theme, w, h, KEYS[k - 1], True))
        raw = enc(base.convert("RGB"))
        assert len(raw) == w * h * 2
        d[off:off + w * h * 2] = raw
    return bytes(d), bg


# ---------------------------------------------------------------------------------------------
# footer of the game list (footbar3) with the "X = delete" hint   ->  resource.cpd
# ---------------------------------------------------------------------------------------------
FRAME_BYTES = 640 * 30 * 2


def build_footbar3(theme, stock_footbar3: bytes):
    """Add '(X) DELETE' on the left of every language frame of the list footer."""
    from .rgb565 import dec
    label = theme.t["list_footer.delete"]
    out = bytearray(stock_footbar3)
    for i in range(len(out) // FRAME_BYTES):
        fr = dec(bytes(out[i * FRAME_BYTES:(i + 1) * FRAME_BYTES]), 640, 30).convert("RGBA")
        d = ImageDraw.Draw(fr)
        d.ellipse((24, 3, 48, 27), outline=WHITE, width=2)
        d.text((36, 15), "X", font=theme.font(15), fill=WHITE, anchor="mm")
        d.text((56, 15), label, font=theme.fit_font(label, 17, 150), fill=WHITE, anchor="lm")
        out[i * FRAME_BYTES:(i + 1) * FRAME_BYTES] = enc(fr.convert("RGB"))
    return bytes(out)


# ---------------------------------------------------------------------------------------------
# language label sprites (same picture repeated for every language)   ->  cubegm/language/*.raw
# ---------------------------------------------------------------------------------------------
NLANG = 25


def text_sprite(theme, w, h, text, size, fill, outline=None, ow=3, x=0):
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = theme.fit_font(text, size * S, (w - x) * S - 4 * S, min_size=8 * S)
    kw = {"stroke_width": ow * S, "stroke_fill": outline} if outline else {}
    d.text((x * S + (ow * S if outline else 0), h * S // 2), text, font=f, fill=fill, anchor="lm", **kw)
    return im.resize((w, h), Image.LANCZOS)


def build_language_sprites(theme):
    dark = theme.dark + (255,)
    out_c = theme.outline + (255,)
    acc = theme.accent + (255,)
    s = theme.t
    blank = Image.new("RGBA", (240, 40), (0, 0, 0, 0))
    frames = {}
    for key, name in (("videos", "Movie"), ("music", "Music"), ("photos", "Photo")):
        text = s["sidebar." + key]
        frames[name] = text_sprite(theme, 240, 40, text, 27, dark)
        frames[name + "_"] = text_sprite(theme, 240, 40, text, 26, WHITE, out_c, 3)
    frames["E-Book"] = blank
    frames["E-Book_"] = blank
    for name in ("Title_Media", "Title_Game"):
        frames[name] = text_sprite(theme, 192, 40, theme.cfg.console_name, 21, acc, out_c, 3, 2)
    return {n + ".raw": fr.tobytes("raw", "BGRA") * NLANG for n, fr in frames.items()}
