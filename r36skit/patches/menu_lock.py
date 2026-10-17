"""The "kids menu": GAMES, VIDEOS, MUSIC, PHOTOS and a SETTINGS page with only volume, brightness and controls.

O "menu infantil": JOGOS, VÍDEOS, MÚSICAS, FOTOS e uma página de AJUSTES só com volume, brilho e controles.

How the stock program is organised / Como o programa original é organizado
  mode 0  carousel of 18 entries (All games, MAME, PS1, ..., DOWNLOAD (= the ``roms`` folder), Favorites, History)
  mode 1  media list: Movie, Music, Photo, E-Book
  mode 2  settings: row 0 volume, 1 brightness, 2 language, 3 screen size, 4 key map (controls), 5 factory reset
  L / R shoulder buttons cycle the three pages.

What we change / O que mudamos
  * the program always starts in mode 0 on the DOWNLOAD entry (index 15) and ignores up/down in the carousel;
  * the media list has 3 rows (Movie, Music, Photo) and wraps around after the third;
  * the page dots on the right edge of the carousel are not drawn;
  * the settings page always starts on row 0 and up/down only visit rows 0, 1 and 4 (volume, brightness, controls);
    language, screen size and factory reset can never be selected;
  * the label of the "controls" row is drawn on the third slot (y = 0xdc) instead of the fifth.
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
    (0x413FB4, "000063a2", "000060a2", "settings page: always start on row 0 (volume)"),
    (0x413FBC, "000044a2", "000040a2", "start with media index 0"),
    (0x4147D4, "fd006212", "00000000", "mode 0: ignore up (carousel)"),
    (0x4147E0, "f4006216", "f4000010", "mode 0: ignore down (carousel)"),
    (0x4149B0, "03004230", "01004230", "media list: 2 rows (will become 3 below)"),
    (0x4155BC, "03000224", "01000224", "media list: wrap to the last row"),
    (0x412BA8, "edfe1104", "00000000", "hide the page-dot column"),
    (0x412BF0, "dbfe1104", "00000000", "hide the selected page dot"),
    (0x413130, "3c010224", "dc000224", "settings: label of the 'controls' row on the third slot (y=0xdc, was 0x13c)"),
]

# Free space: FUN_00418b4c (712 bytes, nothing calls it).
MENU_AREA = 0x418B4C
MENU_AREA_ORIGINAL = "d8ffbd27"  # addiu sp,sp,-40: the function prologue

PHOTOS_CAVE = MENU_AREA  # 16 bytes
SETTINGS_DOWN = MENU_AREA + 16  # 28 bytes
SETTINGS_UP = MENU_AREA + 48  # 24 bytes


def _j(target: int) -> str:
    return struct.pack("<I", 0x08000000 | ((target >> 2) & 0x3FFFFFF)).hex()


# Third row ("Photos"): wrap 0->1->2->0 using a tiny routine.
PHOTOS = [
    (0x4149AC, "9bff0010", _j(PHOTOS_CAVE), "media list, down: jump to our routine"),
    (0x4149B0, "01004230", "00000000", "delay slot"),
    (0x4155BC, "01000224", "02000224", "media list, up: first row wraps to the last (2 = Photos)"),
]
PHOTOS_ROUTINE = "03004838" + "0a100800" + _j(0x41481C) + "00000000"  # xori t0,v0,3 ; movz v0,zero,t0 ; j back ; nop

# Settings page: rows 0 (volume), 1 (brightness), 4 (controls) only.
#   down (stock: "b 0x414ebc" with "addiu v0,v0,1" in the delay slot):   0 -> 1, 1 -> 4, 4 -> 4
#   up   (stock: lbu v0,(s0) ... addiu v0,v0,-1):                         1 -> 0, 4 -> 1  (0 is blocked by the stock code)
def _settings_code() -> tuple[bytes, bytes]:
    """Machine code of the two small routines (assembled with Keystone at import time of the caller)."""
    from .mips import asm

    down = asm(
        """
        .set noreorder
        sltiu $t0, $v0, 1
        sll   $t1, $t0, 1
        addu  $t1, $t1, $t0
        addiu $v0, $zero, 4
        subu  $v0, $v0, $t1
        .word 0x%08x
        nop
        """ % (0x08000000 | (0x414EBC >> 2)),
        SETTINGS_DOWN,
    )
    up = asm(
        """
        .set noreorder
        lbu   $v0, 0($s0)
        lw    $a0, 0($a0)
        addiu $t0, $v0, -4
        sltiu $v0, $t0, 1
        .word 0x%08x
        nop
        """ % (0x08000000 | (0x414EBC >> 2)),
        SETTINGS_UP,
    )
    assert len(down) == 28 and len(up) == 24, (len(down), len(up))
    return down, up


SETTINGS_HOOKS = [
    (0x414F28, "e4ff0010", _j(SETTINGS_DOWN), "settings, down: jump to the row-skipping routine"),
    (0x414F2C, "01004224", "00000000", "delay slot"),
    (0x414EAC, "00000292", _j(SETTINGS_UP), "settings, up: jump to the row-skipping routine (delay slot keeps 'lw t9')"),
]


def apply(elf: Elf) -> None:
    for va, expected, new, what in KIDS_MENU:
        elf.patch(va, expected, new, what)
    if elf.read(MENU_AREA, 4) != bytes.fromhex(MENU_AREA_ORIGINAL) and elf.read(PHOTOS_CAVE, 16) != bytes.fromhex(PHOTOS_ROUTINE):
        raise RuntimeError("free area at 0x%x is not what we expect" % MENU_AREA)
    elf.write(PHOTOS_CAVE, bytes.fromhex(PHOTOS_ROUTINE))
    down, up = _settings_code()
    elf.write(SETTINGS_DOWN, down)
    elf.write(SETTINGS_UP, up)
    for va, expected, new, what in PHOTOS:
        elf.patch(va, expected, new, what)
    for va, expected, new, what in SETTINGS_HOOKS:
        elf.patch(va, expected, new, what)
