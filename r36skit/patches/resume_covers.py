"""Features: (1) game covers in the GAMES list, (2) re-open the last game when the console is switched on.

Recursos: (1) capas dos jogos na lista de JOGOS, (2) reabrir o último jogo ao ligar o aparelho.

Four small pieces of code ("caves") live in ``FUN_0040a538`` (a function nothing calls, 1800 free bytes):

  cave3  hooked at the "open" key of the list (0x42f80c)
         records the game being opened in ``cubegm/lastgame.txt`` (folder + file name) through ``setlast.sh``.
  cave4  hooked in the main menu loop (0x4147b0)
         on the FIRST start after power-on (no ``/tmp/rkgame.boot`` marker yet) it presses "A" for you, unless
         **B** is held or there is no ``lastgame.txt``.  ``/tmp`` is erased when the console powers off, so coming
         back from the video/music/photo apps (which restart the program) does NOT re-open the game.
  cave5  hooked when the list is drawn for the first time (0x42eddc)
         reads ``lastgame.txt``, selects that game and jumps to the normal "open" code.
  cave7  hooked right before every screen refresh of the list (0x42f4a0)
         asks the firmware to draw ``roms/images/<game name>.png``; if there is none and the cursor is on a
         game (not on a folder) it draws ``roms/images/<no-cover>.png`` instead.

  cave8  hooked right after the game call returns (0x42fe70)
         the player left the game -> deletes ``lastgame.txt``.  So the game is only re-opened when the console was
         switched off WHILE playing (the program is killed and never gets here).  cave4 also deletes the file when a
         start does not resume (B held, restart after a video/music app, crash).

State flag ``FLAG`` (0x52e9ec, 4 free bytes): 0 = pending, 1 = "A" injected, 2 = finished.
"""
from __future__ import annotations

from .mips import asm, callabs, callslot, cstring, jabs, lia, place

BASE = 0x40A538  # unused function of the firmware (1800 bytes)
AREA_SIZE = 1800
FLAG = 0x52E9EC
FRAME = 0x300

HOOKS = {
    "cave4": (0x4147B0, "2598620224107002"),  # main menu: poll of the buttons
    "cave5": (0x42EDDC, "3009a28f01000324"),  # list: first draw / reload
    "cave3": (0x42F80C, "c9ffc0123009a28f"),  # list: "open" key
    "cave7": (0x42F4A0, "3c00e58e3481998f"),  # list: right before the screen refresh
    "cave8": (0x42FE70, "2330d3031800bc8f"),  # list: right after the game has ended (the call at 0x42fe68 returns)
}

# Forget the last game when the player has left it.  A power-off while playing never gets here, so the file stays.
FORGET_AFTER_GAME = b"rm -f /mnt/sdcard/cubegm/lastgame.txt; echo gameexit >> /mnt/sdcard/cubegm/rkgame.log; sync\x00"
FORGET_AT_START = b"rm -f /mnt/sdcard/cubegm/lastgame.txt; echo startclear >> /mnt/sdcard/cubegm/rkgame.log\x00"

LAST_GAME = b"/mnt/sdcard/cubegm/lastgame.txt\x00"
READ_BINARY = b"rb\x00"
LOG_PATH = b"/mnt/sdcard/cubegm/rkgame.log\x00"
APPEND = b"a\x00"
LOG_FORMAT = b"setlast rc=%d cmd=%s\n\x00"
BOOT_MARKER = b"/tmp/rkgame.boot\x00"
WRITE = b"w\x00"
SET_LAST = b'/bin/sh /mnt/sdcard/cubegm/setlast.sh "%s" "%s"\x00'

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


def cave3(A):
    return """
  .set noreorder
  beqz  $s6, ORIG3
  nop
  sll   $t1, $s0, 8
  addu  $t1, $t1, $s0
  sll   $t1, $t1, 2
  lw    $t2, 0x940($sp)
  addu  $t8, $t1, $t2
  lw    $t3, 0x100($t8)
  addiu $t4, $zero, 4
  beq   $t3, $t4, ORIG3
  nop
  lb    $t3, 0($t8)
  beqz  $t3, ORIG3
  nop
  addiu $sp, $sp, -%(F)d
  sw    $t8, 0x40($sp)
  lw    $t0, %(o990)d($sp)
  addiu $a2, $t0, -0x40f4
  lw    $a3, 0x40($sp)
  addiu $a0, $sp, 0x80
  %(fmt)s
  %(sprintf)s
  addiu $a0, $sp, 0x80
  %(system)s
%(logblk)s
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
ORIG3:
  beqz  $s6, GOTO0
  lw    $v0, 0x930($sp)
  %(jret)s
  nop
GOTO0:
  %(jzero)s
  nop
""" % dict(F=FRAME, o990=0x990 + FRAME,
           logblk=LOG_BLOCK % dict(lp=lia("$a0", A["logp"]), la=lia("$a1", A["amode"]), lf=lia("$a1", A["lfmt3"]), skip="SKIPLOG3"),
           fmt=lia("$a1", A["fmt3"]), sprintf=callslot(-0x15D8), system=callslot(-0xBD4),
           jret=jabs(0x42F814), jzero=jabs(0x42F734))


def cave4(A):
    return """
  .set noreorder
  or    $s3, $s3, $v0
  lui   $t0, 0x53
  lw    $t1, -0x1614($t0)
  bnez  $t1, DONE4
  nop
  %(mark)s
  move  $a1, $zero
  %(access)s
  lw    $gp, 0x28($sp)
  beqz  $v0, MARK2
  nop
  %(mark)s
  %(wmode)s
  %(fopen)s
  lw    $gp, 0x28($sp)
  beqz  $v0, AFTERMK
  nop
  or    $a0, $v0, $zero
  %(fclose)s
  lw    $gp, 0x28($sp)
AFTERMK:
  andi  $t2, $s3, 0x4000
  bnez  $t2, MARK2
  nop
  %(last)s
  move  $a1, $zero
  %(access)s
  lw    $gp, 0x28($sp)
  bnez  $v0, MARK2
  nop
  lui   $t0, 0x53
  addiu $t1, $zero, 1
  sw    $t1, -0x1614($t0)
  b     DONE4
  addiu $s3, $zero, 0x2000
MARK2:
  %(forget)s
  lw    $gp, 0x28($sp)
  lui   $t0, 0x53
  addiu $t1, $zero, 2
  sw    $t1, -0x1614($t0)
DONE4:
  and   $v0, $s3, $s0
  %(jret)s
  nop
""" % dict(last=lia("$a0", A["last"]), mark=lia("$a0", A["mark"]), wmode=lia("$a1", A["wmode"]), access=callslot(-0x14F4),
           fopen=callslot(-0x15D0), fclose=callslot(-0x15C8), jret=jabs(0x4147B8),
           forget=lia("$a0", A["forget_start"]) + "\n" + callslot(-0xBD4))


def cave8(A):
    """The game has ended and we are back in the list: the player is not playing any more -> forget the game."""
    return """
  .set noreorder
  lw    $gp, 0x18($sp)
  %(forget)s
  subu  $a2, $fp, $s3
  lw    $gp, 0x18($sp)
  %(jret)s
  nop
""" % dict(forget=lia("$a0", A["forget_exit"]) + "\n" + callslot(-0xBD4), jret=jabs(0x42FE78))


def cave5(A):
    return """
  .set noreorder
  lui   $t0, 0x53
  lw    $t1, -0x1614($t0)
  addiu $t2, $zero, 1
  bne   $t1, $t2, RESUME5
  nop
  addiu $t3, $zero, 2
  sw    $t3, -0x1614($t0)
  addiu $sp, $sp, -%(F)d
  %(last)s
  %(rb)s
  %(fopen)s
  beqz  $v0, FAIL5
  sw    $v0, 0x20($sp)
  addiu $a0, $sp, 0x40
  addiu $a1, $zero, 1
  addiu $a2, $zero, 0x200
  lw    $a3, 0x20($sp)
  %(fread)s
  sw    $v0, 0x24($sp)
  addu  $t0, $sp, $v0
  sb    $zero, 0x40($t0)
  lw    $a0, 0x20($sp)
  %(fclose)s
  addiu $t5, $sp, 0x40
L1:
  lb    $t0, 0($t5)
  beqz  $t0, FAIL5
  addiu $t1, $t0, -10
  beqz  $t1, L1END
  addiu $t1, $t0, -13
  beqz  $t1, L1END
  nop
  b     L1
  addiu $t5, $t5, 1
L1END:
  sb    $zero, 0($t5)
  addiu $t6, $t5, 1
  lb    $t0, 0($t6)
  addiu $t1, $t0, -10
  bnez  $t1, N0
  nop
  addiu $t6, $t6, 1
N0:
  move  $t7, $t6
L2:
  lb    $t0, 0($t7)
  beqz  $t0, L2END
  addiu $t1, $t0, -10
  beqz  $t1, L2END
  addiu $t1, $t0, -13
  beqz  $t1, L2END
  nop
  b     L2
  addiu $t7, $t7, 1
L2END:
  sb    $zero, 0($t7)
  lb    $t0, 0x40($sp)
  beqz  $t0, FAIL5
  nop
  lb    $t0, 0($t6)
  beqz  $t0, FAIL5
  nop
  sw    $t6, 0x28($sp)
  lw    $t0, %(o990)d($sp)
  addiu $a0, $t0, -0x40f4
  addiu $a1, $sp, 0x40
  %(strcpy)s
  lw    $a0, %(o940)d($sp)
  lw    $a1, 0x28($sp)
  %(strcpy)s
  lw    $t0, %(o940)d($sp)
  addiu $t1, $zero, 8
  sw    $t1, 0x100($t0)
  or    $s0, $zero, $zero
  or    $s5, $zero, $zero
  addiu $s6, $zero, 1
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
  %(jA)s
  nop
FAIL5:
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
RESUME5:
  lw    $v0, 0x930($sp)
  addiu $v1, $zero, 1
  %(jret)s
  nop
""" % dict(F=FRAME, o990=0x990 + FRAME, o940=0x940 + FRAME, last=lia("$a0", A["last"]), rb=lia("$a1", A["rb"]),
           fopen=callslot(-0x15D0), fread=callslot(-0x1398), fclose=callslot(-0x15C8), strcpy=callslot(-0x15A8),
           jA=jabs(0x42F80C), jret=jabs(0x42EDE4))


def cave7(A):
    return """
  .set noreorder
  beqz  $s6, RESUME7
  nop
  addiu $sp, $sp, -0x200
  lw    $t0, 0xb88($sp)
  lw    $t1, -0x4b30($t0)
  sw    $t1, 0x10($sp)
  sw    $s0, -0x4b30($t0)
  sw    $zero, -0x4b38($t0)
  sw    $zero, -0x4b2c($t0)
  %(thumb)s
  sll   $t1, $s0, 8
  addu  $t1, $t1, $s0
  sll   $t1, $t1, 2
  lw    $t2, 0xb40($sp)
  addu  $t8, $t1, $t2
  sw    $t8, 0x14($sp)
  lw    $t3, 0x100($t8)
  addiu $t4, $zero, 4
  beq   $t3, $t4, DONE7
  nop
  lb    $t3, 0($t8)
  beqz  $t3, DONE7
  nop
  lw    $t0, 0xb88($sp)
  lw    $t3, -0x4b2c($t0)
  bnez  $t3, DONE7
  nop
  addiu $a0, $sp, 0x80
  or    $a1, $t8, $zero
  %(strcpy)s
  lw    $a0, 0x14($sp)
  %(semcapa)s
  %(strcpy)s
  lw    $t0, 0xb88($sp)
  sw    $zero, -0x4b38($t0)
  sw    $zero, -0x4b2c($t0)
  %(thumb)s
  lw    $a0, 0x14($sp)
  addiu $a1, $sp, 0x80
  %(strcpy)s
DONE7:
  lw    $t0, 0xb88($sp)
  lw    $t1, 0x10($sp)
  sw    $t1, -0x4b30($t0)
  addiu $sp, $sp, 0x200
  lw    $gp, 0x18($sp)
RESUME7:
  lw    $a1, 0x3c($s7)
  lw    $t9, -0x7ecc($gp)
  %(jret)s
  nop
""" % dict(thumb=callabs(0x41E370), strcpy=callslot(-0x15A8), semcapa=lia("$a1", A["semcapa"]), jret=jabs(0x42F4A8))


CAVES = (("cave3", cave3), ("cave4", cave4), ("cave5", cave5), ("cave7", cave7), ("cave8", cave8))


def build(no_cover_stem: str = "_no_cover"):
    """Return ``({cave: (address, code)}, data_address, data_bytes)``.

    ``no_cover_stem``: file name (without extension) of the placeholder cover inside ``roms/images``.
    The firmware shows the picture of an entry called ``<stem>.x``, so the placeholder file is ``<stem>.png``.
    """
    strings = [("fmt3", SET_LAST), ("last", LAST_GAME), ("rb", READ_BINARY), ("logp", LOG_PATH), ("amode", APPEND),
               ("lfmt3", LOG_FORMAT), ("semcapa", cstring(no_cover_stem + ".x")), ("mark", BOOT_MARKER), ("wmode", WRITE),
               ("forget_exit", FORGET_AFTER_GAME), ("forget_start", FORGET_AT_START)]
    dummy = {name: 0x40A000 for name, _ in strings}
    layout, base = {}, BASE
    for name, fn in CAVES:
        size = len(asm(fn(dummy), base))
        layout[name] = (base, size)
        base += (size + 3) & ~3
    offsets, blob = place(strings)
    addr = {name: base + off for name, off in offsets.items()}
    caves = {}
    for name, fn in CAVES:
        start, size = layout[name]
        code = asm(fn(addr), start)
        assert len(code) == size
        caves[name] = (start, code)
    if base + len(blob) > BASE + AREA_SIZE:
        raise RuntimeError("resume/covers caves do not fit in the free area")
    return caves, base, blob
