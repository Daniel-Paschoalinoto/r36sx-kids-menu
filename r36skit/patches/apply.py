"""Apply every code patch to a stock ``rkgame`` and return the patched program.

Aplica todos os patches de código num ``rkgame`` original e devolve o programa alterado.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..elfpatch import Elf, PatchError, jump
from . import deletegame, deletesave, listfilter, menu_lock, resume_covers

# sha256 of the ``rkgame`` these patches were written for (1,178,732 bytes, "cubegm" firmware, HiChip HC16xx)
SUPPORTED_RKGAME_SHA256 = "57d8b4fd85e0aab44d17a51d209879c3f98130d066b622142736b42ad08ddcb9"

# Thumbnail box of the GAMES list: x=50, y=153, 240x240 (stock: x=10, 320x240).  Covers are square.
THUMBNAIL_BOX = [
    (0x41B880, "0a000224", "32000224", "thumbnail box x = 50"),
    (0x41B890, "40010224", "f0000224", "thumbnail box width = 240"),
]


@dataclass
class Options:
    resume_last_game: bool = True  # re-open the last game when the console is switched on
    delete_game: bool = True  # X on a game -> delete it
    delete_save: bool = True  # X on a slot of the pause menu's LOAD/SAVE screens -> delete the save
    hide_bin: bool = True  # do not list .bin files
    no_cover_name: str = "_no_cover"  # placeholder cover: roms/images/<name>.png


def apply_all(elf: Elf, texts: dict, options: Options | None = None, check_hash: bool = True) -> Elf:
    """``texts``: dialog strings (see ``strings.py``): ``delete_game_*``, ``delete_save_*``, ``confirm_*``."""
    options = options or Options()
    if check_hash and elf.sha256() != SUPPORTED_RKGAME_SHA256:
        raise PatchError(
            "This 'rkgame' is not the build these patches were made for.\n"
            "Este 'rkgame' não é a versão para a qual os patches foram feitos.\n"
            "  found / encontrado : %s\n  expected / esperado: %s" % (elf.sha256(), SUPPORTED_RKGAME_SHA256)
        )

    menu_lock.apply(elf)
    listfilter.apply(elf, hide_bin=options.hide_bin)

    # --- covers (+ optional "open the last game") -------------------------------------------------
    caves, data_addr, data = resume_covers.build(no_cover_stem=options.no_cover_name)
    for name, (addr, code) in caves.items():
        elf.write(addr, code)
    elf.write(data_addr, data)
    enabled = ["cave7"] + (["cave3", "cave4", "cave5", "cave8"] if options.resume_last_game else [])
    for name in enabled:
        va, original = resume_covers.HOOKS[name]
        elf.hook(va, original, caves[name][0], name)

    # --- delete game ---------------------------------------------------------------------------
    if options.delete_game:
        image = deletegame.build(
            {"title": texts["delete_game_title"], "sub": texts["delete_game_sub"],
             "yes": texts["confirm_yes"], "no": texts["confirm_cancel"]})
        elf.write(deletegame.CAVE, image)
        elf.hook(deletegame.HOOK, deletegame.HOOK_ORIGINAL, deletegame.CAVE, "delete game")

    # --- delete save ---------------------------------------------------------------------------
    if options.delete_save:
        built = deletesave.build(
            {"title": texts["delete_save_title"], "sub": texts["delete_save_sub"],
             "yes": texts["confirm_yes"], "no": texts["confirm_cancel"]})
        elf.write(*built["common"])
        elf.write(*built["stubs"])
        for key, (va, original, _tag) in deletesave.HOOKS.items():
            elf.hook(va, original, built["entries"][key], "delete save (%s)" % key)

    for va, expected, new, what in THUMBNAIL_BOX:
        elf.patch(va, expected, new, what)
    return elf
