# How it works (for tinkerers)

🇧🇷 [Português](../pt-BR/COMO-FUNCIONA.md)

You do **not** need any of this to use the project.

## The console

`icube` starts `rkgame`, a 32-bit little-endian **MIPS** ELF program that draws the whole UI and runs the emulator cores (`cubegm/cores/*.so`). Pictures live in zip files with the extension `.cpd`:

| File | Contents |
|---|---|
| `UI_Res.cpd` | Full-screen backgrounds, raw **BGRA** 640×480 (`MovieBg`, `MusicBg`, `PhotoBg`, `DOWNLOAD` = the Games page) |
| `resource.cpd` | Game list (`menu.raw`), pause menu (`game.raw`), search keyboard (`search.raw`), loading screen, footers. Sheets are **RGB565** with a header listing each piece's rectangle |
| `ui_<lang>.cpd` | The pause-menu sheet (`game.raw`) for each of the 25 languages |
| `language/*.raw` | Text labels, 25 frames (one per language) of BGRA |
| `xgame-logo.bmp` | Start screen (32-bit BMP) |

`r36skit/art/` redraws those pictures with Pillow. It reads the rectangles from the console's own sheets, so positions always match.

## The code patches (`r36skit/patches/`)

The program is changed by **hooks**: a `j cave; nop` placed over one instruction, jumping into unused space (a "cave") inside functions that are never called. The cave runs our code (assembled with Keystone) and jumps back.

| Module | What it does |
|---|---|
| `menu_lock.py` | Only 3 media buttons + Games; hides settings / e-books / console list |
| `listfilter.py` | Hides `.bin` and the `images` folder in the game list |
| `resume_covers.py` | Cover thumbnails (+ "no cover" picture), opens the last game at power-on |
| `deletegame.py` | X → confirm → run `delgame.sh` (which deletes game, cue files, same-name files, covers) |
| `deletesave.py` | X on a save slot → confirm → delete |
| `apply.py` | Runs all of them; checks the SHA-256 first |

`elfpatch.py` writes by virtual address and verifies the original bytes before replacing them ("patch only if it looks like what we expect, or is already patched"). Shell scripts run through `system()`, which works on the device.

## Adding support for another firmware

1. Open `rkgame` in Ghidra (MIPS, 32-bit, little-endian).
2. Find each hook address and cave; update the constants at the top of each patch module (`HOOK`, `CAVE`, original bytes).
3. Add the new SHA-256 to `SUPPORTED_RKGAME_SHA256` (make it a list) and test on a real device. Send a pull request.

## Tests

`python -m pytest` checks texts in all languages, picture sizes, the config error messages and (if you put your stock files in `stock/`) that the patches apply.
