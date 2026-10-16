"""Feature: press **X** on a game in the GAMES list -> "Delete this game?" -> A = yes, B = cancel.

Recurso: tecla **X** sobre um jogo na lista de JOGOS -> "Excluir este jogo?" -> A = sim, B = cancelar.

How it works / Como funciona
  * The file browser of ``rkgame`` ignores unknown keys (jump at ``HOOK``).  We hook that spot.
  * If the cursor is on a regular file and X was pressed, we draw the confirmation box with the firmware's own
    drawing routines, then run ``/bin/sh <cubegm>/delgame.sh "<folder>/<file>"`` (``system()`` works on the device).
  * The script removes the game, the files listed in a ``.cue`` sheet, files with the same name and the covers.
    It never touches save files.
  * The code lives in ``FUN_0044116c``, a function of the firmware that nothing calls (1700 free bytes).
"""
from __future__ import annotations

from .mips import asm, cstring, jabs, lia, place

CAVE = 0x44116C  # unused function of the firmware (1700 bytes)
CAVE_SIZE = 1700
HOOK = 0x42F470  # "unknown key" fallback of the file browser
HOOK_ORIGINAL = "9080838f0000638c"
RET_ORIG = 0x42F478
RELOAD = 0x42EDDC  # reload the list (same target the browser uses when coming back from a game)
FRAME = 0x300

LOG_PATH = b"/mnt/sdcard/cubegm/rkgame.log\x00"
APPEND = b"a\x00"
LOG_FORMAT = b"delete rc=%d cmd=%s\n\x00"
COMMAND = b'/bin/sh /mnt/sdcard/cubegm/delgame.sh "%s/%s" >> /mnt/sdcard/cubegm/delgame.log 2>&1\x00'

# shared "append one line to rkgame.log" block (keeps a trace of what the device did)
LOG_BLOCK = """
  sw    $v0, 0x48($sp)
  %(lp)s
  %(la)s
  lui   $t9, 0x53
  lw    $t9, -0x15d0($t9)
  jalr  $t9
  nop
  beqz  $v0, %(skip)s
  sw    $v0, 0x4c($sp)
  or    $a0, $v0, $zero
  %(lf)s
  lw    $a2, 0x48($sp)
  addiu $a3, $sp, 0x80
  lui   $t9, 0x53
  lw    $t9, -0x15f0($t9)
  jalr  $t9
  nop
  lw    $a0, 0x4c($sp)
  lui   $t9, 0x53
  lw    $t9, -0x15c8($t9)
  jalr  $t9
  nop
%(skip)s:
"""

PROLOGUE = """
  addiu $t0, $zero, 0x1000
  bne   $v0, $t0, ORIG
  nop
  beqz  $s6, ORIG
  nop
  addiu $sp, $sp, -%(F)d
  sll   $t1, $s0, 8
  addu  $t1, $t1, $s0
  sll   $t1, $t1, 2
  lw    $t2, %(o940)d($sp)
  addu  $t8, $t1, $t2
  lw    $t3, 0x100($t8)
  addiu $t4, $zero, 4
  beq   $t3, $t4, EXITRESTORE
  nop
  lb    $t3, 0($t8)
  beqz  $t3, EXITRESTORE
  nop
  sw    $t8, 0x40($sp)
  lw    $t7, %(o990)d($sp)
  sw    $t7, 0x44($sp)
  addiu $t5, $sp, 0x20
  addiu $t6, $zero, 0xf0
  sw    $t6, 4($t5)
  addiu $t6, $zero, 0xb4
  sw    $t6, 8($t5)
  addiu $t6, $zero, 0x266
  sw    $t6, 0xc($t5)
  addiu $t6, $zero, 0x12c
  sw    $t6, 0x10($t5)
  lw    $t6, 0x3c($s7)
  sll   $t6, $t6, 1
  sw    $t6, 0x14($t5)
  lw    $t6, -0x40f8($t7)
  addiu $t9, $zero, -3
  and   $t6, $t6, $t9
  sw    $t6, -0x40f8($t7)
  addiu $a0, $sp, 0x20
  lui   $t9, 0x42
  ori   $t9, $t9, 0x62f8
  jalr  $t9
  nop
  lw    $t7, 0x44($sp)
  addiu $t7, $t7, -0x424c
  addiu $t6, $zero, 0xf0
  sw    $t6, 8($t7)
  addiu $t6, $zero, 0xb4
  sw    $t6, 0xc($t7)
  addiu $t6, $zero, 0x266
  sw    $t6, 0x10($t7)
  addiu $t6, $zero, 0x12c
  sw    $t6, 0x14($t7)
"""

TEXT_CALL = """
  lw    $a0, 0x38($s7)
  addiu $a1, $zero, %d
  addiu $a2, $zero, %d
  addiu $a3, $zero, %d
  lui   $t0, 0x0
  ori   $t0, $t0, 0x%x
  sw    $t0, 0x10($sp)
  %s
  sw    $t0, 0x14($sp)
  lui   $t9, 0x41
  ori   $t9, $t9, 0xd22c
  jalr  $t9
  nop
"""

EPILOGUE = """
  lw    $a0, 0x38($s7)
  lw    $a1, 0x3c($s7)
  lw    $a2, 0x40($s7)
  sll   $a3, $a1, 1
  lui   $t9, 0x53
  lw    $t9, -0x14ec($t9)
  jalr  $t9
  nop
  lui   $t9, 0x41
  ori   $t9, $t9, 0xdb00
  jalr  $t9
  nop
  lw    $t0, %(o988)d($sp)
  sw    $zero, 0x57ec($t0)
  lui   $t9, 0x41
  ori   $t9, $t9, 0xab28
  jalr  $t9
  nop
  lw    $t0, %(o988)d($sp)
  sw    $v0, 0x57f0($t0)
LOOP:
  lui   $t9, 0x41
  ori   $t9, $t9, 0xdb00
  jalr  $t9
  nop
  addiu $t0, $zero, 0x2000
  beq   $v0, $t0, DELETE
  nop
  addiu $t0, $zero, 0x4000
  beq   $v0, $t0, CANCEL
  nop
  lui   $t9, 0x41
  ori   $t9, $t9, 0xdb34
  jalr  $t9
  nop
  b     LOOP
  nop
DELETE:
  addiu $a0, $sp, 0x80
  %(fmt)s
  lw    $t0, 0x44($sp)
  addiu $a2, $t0, -0x40f4
  lw    $a3, 0x40($sp)
  lui   $t9, 0x53
  lw    $t9, -0x15d8($t9)
  jalr  $t9
  nop
  addiu $a0, $sp, 0x80
  lui   $t9, 0x53
  lw    $t9, -0xbd4($t9)
  jalr  $t9
  nop
%(logblk)s
  addiu $a0, $sp, 0x20
  lui   $t9, 0x42
  ori   $t9, $t9, 0x66dc
  jalr  $t9
  nop
  or    $s5, $zero, $zero
  or    $s0, $zero, $zero
  b     RELOADP
  nop
CANCEL:
  addiu $a0, $sp, 0x20
  lui   $t9, 0x42
  ori   $t9, $t9, 0x66dc
  jalr  $t9
  nop
RELOADP:
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
  %(jreload)s
  nop
EXITRESTORE:
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
ORIG:
  lw    $v1, -0x7f70($gp)
  lw    $v1, 0($v1)
  %(jorig)s
  nop
"""


def _source(addr: dict) -> str:
    text = ".set noreorder\n"
    text += PROLOGUE % dict(F=FRAME, o940=0x940 + FRAME, o990=0x990 + FRAME)
    for x, y, size, color, key in ((255, 200, 0x18, 0xFA08, "title"), (255, 232, 0x14, 0xFFFF, "sub"),
                                   (255, 262, 0x14, 0xFFFF, "yes"), (390, 262, 0x14, 0xFFFF, "no")):
        text += TEXT_CALL % (x, y, size, color, lia("$t0", addr[key]))
    text += EPILOGUE % dict(
        o988=0x988 + FRAME, F=FRAME, fmt=lia("$a1", addr["fmt"]),
        logblk=LOG_BLOCK % dict(lp=lia("$a0", addr["log"]), la=lia("$a1", addr["amode"]), lf=lia("$a1", addr["lfmt"]), skip="SKIPLOG"),
        jreload=jabs(RELOAD), jorig=jabs(RET_ORIG))
    return text


def build(texts: dict):
    """Return (machine code + strings placed at CAVE, address table).  ``texts``: title, sub, yes, no."""
    strings = [("title", cstring(texts["title"])), ("sub", cstring(texts["sub"])), ("yes", cstring(texts["yes"])),
               ("no", cstring(texts["no"])), ("fmt", COMMAND), ("log", LOG_PATH), ("amode", APPEND), ("lfmt", LOG_FORMAT)]
    dummy = {name: 0x440000 for name, _ in strings}
    code_len = len(asm(_source(dummy), CAVE))
    data_base = (CAVE + code_len + 3) & ~3
    offsets, blob = place(strings)
    addr = {name: data_base + off for name, off in offsets.items()}
    code = asm(_source(addr), CAVE)
    assert len(code) == code_len
    image = code + bytes(data_base - (CAVE + code_len)) + blob
    if len(image) > CAVE_SIZE:
        raise RuntimeError("delete-game cave is too big (%d > %d bytes); shorten the texts" % (len(image), CAVE_SIZE))
    return image
