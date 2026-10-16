"""Clean file list: only things the console can open are shown (no ``.bin``, ``.sav``, ``.txt``, ``images`` folder...).

Lista de arquivos limpa: só aparece o que o aparelho abre (sem ``.bin``, ``.sav``, ``.txt``, pasta ``images``...).

The GAMES list is a plain file browser: it calls ``scandir(folder, &list, 0, alphasort)`` with *no filter*.
We pass a filter function (``scandir`` calls it for every entry; non-zero = keep it):

  * folders are kept, except a folder named ``images`` (it holds the covers);
  * a file is kept only if its extension is in the firmware's own table of supported extensions
    (39 entries at 0x52c084, 68 bytes each, upper case);
  * ``.bin`` is removed from that table on purpose (see ``hide_bin``): a PlayStation game is started from its
    ``.cue`` and the ``.bin`` next to it only confuses people.  Mega Drive ROMs just need the extension ``.md``.

The filter lives in dead code (0x414c88 and 0x415134 - the old "go to settings" handlers).
Its address is stored in a spare word (0x52e9e8) and loaded by the ``scandir`` call.
"""
from __future__ import annotations

from ..elfpatch import Elf
from .mips import asm

FILTER_AT = 0x414C88
FILTER_ORIGINAL = "4800a28f"  # dead code: first instruction of the old handler
IMAGES_AT = 0x415134
IMAGES_ORIGINAL = "b4004524"
KEEP, DROP = 0x414D1C, 0x414D24
POINTER_SLOT = 0x52E9E8  # 4 spare bytes, read with ``lw a2,-0x7ff8(gp)``
EXT_TABLE_BIN = 0x52C618  # the "BIN" entry of the extension table

SCANDIR_CALLS = (0x4214E0, 0x41FAC0)  # the 2nd one is inside a function nothing calls; patched for symmetry

FILTER = """
  .set noreorder
  lbu   $t0, 10($a0)
  andi  $t0, $t0, 4
  bnez  $t0, keep
  addiu $a0, $a0, 11
  move  $t2, $zero
scan:
  lbu   $t3, 0($a0)
  beqz  $t3, scandone
  addiu $t4, $t3, -46
  bnez  $t4, scan_next
  nop
  move  $t2, $a0
scan_next:
  b     scan
  addiu $a0, $a0, 1
scandone:
  beqz  $t2, drop
  addiu $t2, $t2, 1
  lui   $t5, 0x52
  ori   $t5, $t5, 0xc084
entry:
  lbu   $t6, 0($t5)
  beqz  $t6, drop
  move  $t7, $t2
  move  $t8, $t5
cmp:
  lbu   $t9, 0($t7)
  addiu $t0, $t9, -97
  sltiu $t0, $t0, 26
  beqz  $t0, noup
  nop
  addiu $t9, $t9, -32
noup:
  lbu   $t1, 0($t8)
  bne   $t9, $t1, nextentry
  nop
  beqz  $t9, keep
  nop
  addiu $t7, $t7, 1
  b     cmp
  addiu $t8, $t8, 1
nextentry:
  b     entry
  addiu $t5, $t5, 0x44
keep:
  jr    $ra
  addiu $v0, $zero, 1
drop:
  jr    $ra
  move  $v0, $zero
"""

# folders: keep everything except a folder literally called "images" (any case)
IMAGES = """
  .set noreorder
  lbu   $t1, 0($a0)
  ori   $t1, $t1, 0x20
  xori  $t1, $t1, 0x69
  bnez  $t1, Lkeep
  lbu   $t1, 1($a0)
  ori   $t1, $t1, 0x20
  xori  $t1, $t1, 0x6d
  bnez  $t1, Lkeep
  lbu   $t1, 2($a0)
  ori   $t1, $t1, 0x20
  xori  $t1, $t1, 0x61
  bnez  $t1, Lkeep
  lbu   $t1, 3($a0)
  ori   $t1, $t1, 0x20
  xori  $t1, $t1, 0x67
  bnez  $t1, Lkeep
  lbu   $t1, 4($a0)
  ori   $t1, $t1, 0x20
  xori  $t1, $t1, 0x65
  bnez  $t1, Lkeep
  lbu   $t1, 5($a0)
  ori   $t1, $t1, 0x20
  xori  $t1, $t1, 0x73
  bnez  $t1, Lkeep
  lbu   $t1, 6($a0)
  bnez  $t1, Lkeep
  nop
  b     Ldrop
  nop
Lkeep:
  nop
  nop
Ldrop:
  nop
  nop
"""


def _jump_word(target: int) -> bytes:
    return (0x08000000 | (target >> 2)).to_bytes(4, "little")


def filter_code() -> bytes:
    code = bytearray(asm(FILTER, FILTER_AT))
    # 3rd instruction (bnez t0,...): folders go to the 'images' check instead of straight to 'keep'
    offset = (IMAGES_AT - (FILTER_AT + 8 + 4)) // 4
    word = int.from_bytes(code[8:12], "little")
    assert (word >> 26) == 5 and ((word >> 21) & 31) == 8
    code[8:12] = ((word & 0xFFFF0000) | (offset & 0xFFFF)).to_bytes(4, "little")
    return bytes(code)


def images_code() -> bytes:
    code = bytearray(asm(IMAGES, IMAGES_AT))
    code[-16:-8] = _jump_word(KEEP) + bytes(4)
    code[-8:] = _jump_word(DROP) + bytes(4)
    return bytes(code)


def apply(elf: Elf, hide_bin: bool = True) -> None:
    if hide_bin:
        elf.patch(EXT_TABLE_BIN, "42494e00", "58494e00", "extension table: BIN -> XIN (never matches)")
    filt, images = filter_code(), images_code()
    for va, original, blob in ((FILTER_AT, FILTER_ORIGINAL, filt), (IMAGES_AT, IMAGES_ORIGINAL, images)):
        if elf.read(va, 4) != bytes.fromhex(original) and elf.read(va, len(blob)) != blob:
            raise RuntimeError("dead-code area at 0x%x is not what we expect" % va)
        elf.write(va, blob)
    elf.write(POINTER_SLOT, FILTER_AT.to_bytes(4, "little"))
    for va in SCANDIR_CALLS:
        elf.patch(va, "25300000", "088086" + "8f", "scandir: pass our filter (lw a2,-0x7ff8(gp))")
