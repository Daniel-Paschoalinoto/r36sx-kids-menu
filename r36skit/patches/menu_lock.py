"""The "kids menu": only GAMES, VIDEOS, MUSIC and PHOTOS.  Everything else is made unreachable.

O "menu infantil": só JOGOS, VÍDEOS, MÚSICAS e FOTOS.  O resto fica inalcançável.

How the stock program is organised / Como o programa original é organizado
  mode 0  carousel of 18 entries (All games, MAME, PS1, ..., DOWNLOAD (= the ``roms`` folder), Favorites, History)
  mode 1  media list: Movie, Music, Photo, E-Book
  mode 2  settings (volume, brightness, language, screen, key map, factory reset)
  L/R shoulder buttons cycle 0 -> 1 -> 2 -> 0.

What we change / O que mudamos
  * the program always starts in mode 0 on the DOWNLOAD entry (index 15) and ignores up/down in the carousel;
  * L/R toggle between mode 0 and mode 1 (settings are never reached);
  * the media list has 3 rows (Movie, Music, Photo) and wraps around after the third;
  * the page dots on the right edge of the carousel are not drawn.
All edits are checked: if the bytes are not what we expect the build stops instead of corrupting the program.
"""
from __future__ import annotations

import struct

from ..elfpatch import Elf

# (address, expected bytes, new bytes, description)
KIDS_MENU = [
    (0x413F78, "000082a0", "0f000224", "li v0,15: always the DOWNLOAD (roms) entry"),
    (0x413F7C, "12000224", "000082a0", "store it as the carousel index"),
    (0x413FB0, "000025a2", "000020a2", "start in mode 0 (carousel)"),
    (0x413FBC, "000044a2", "000040a2", "start with media index 0"),
    (0x4147D4, "fd006212", "00000000", "mode 0: ignore up (carousel)"),
    (0x4147E0, "f4006216", "f4000010", "mode 0: ignore down (carousel)"),
    (0x414894, "fc006212", "d8006212", "mode 0: R button goes to the media list (not to settings)"),
    (0x414974, "eb010212", "ce010212", "mode 1: L button goes back to the carousel (not to settings)"),
    (0x4149B0, "03004230", "01004230", "media list: 2 rows (will become 3 below)"),
    (0x4155BC, "03000224", "01000224", "media list: wrap to the last row"),
    (0x412BA8, "edfe1104", "00000000", "hide the page-dot column"),
    (0x412BF0, "dbfe1104", "00000000", "hide the selected page dot"),
]

PHOTOS_CAVE = 0x415124  # dead code of the old "media -> settings" transition


def _j(target: int) -> str:
    return struct.pack("<I", 0x08000000 | ((target >> 2) & 0x3FFFFFF)).hex()


# Third row ("Photos"): wrap 0->1->2->0 using a tiny routine placed in dead code.
PHOTOS = [
    (0x4149AC, "9bff0010", _j(PHOTOS_CAVE), "media list, down: jump to our routine"),
    (0x4149B0, "01004230", "00000000", "delay slot"),
    (0x4155BC, "01000224", "02000224", "media list, up: first row wraps to the last (2 = Photos)"),
    (0x415124, "4800a28f01000424dc83998fc7331104", "03004838" + "0a100800" + _j(0x41481C) + "00000000",
     "routine: xori t0,v0,3 ; movz v0,zero,t0 ; j back ; nop"),
]


def apply(elf: Elf) -> None:
    for va, expected, new, what in KIDS_MENU:
        elf.patch(va, expected, new, what)
    for va, expected, new, what in PHOTOS:
        elf.patch(va, expected, new, what)
