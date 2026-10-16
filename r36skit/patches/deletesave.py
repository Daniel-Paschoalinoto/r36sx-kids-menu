"""Feature: in the pause menu's LOAD and SAVE screens press **X** on a slot -> "Delete this save?".

Recurso: nas telas CARREGAR e SALVAR do menu de pausa, tecla **X** sobre um slot -> "Excluir este save?".

Only the chosen slot file is removed (``states/<system>/<game>.sv<slot>``) with ``rm -f``; nothing else is touched.
Empty slots are ignored.  After deleting, the slot is redrawn as empty.

The code is split in two free (never called) functions of the firmware:
  * COMMON (``FUN_0043cfc0``, 1392 bytes): the dialog + deletion, shared by both screens;
  * STUB   (``FUN_00464854``, 1340 bytes): one tiny entry point per screen + the text strings.

LOAD screen  hook 0x4280c0: slot = $s1, slot flags = $s8 + 4*slot
SAVE screen  hook 0x4277f4: slot = $s2, slot flags = $s3 + 0x230 + 4*slot
In both, $s0 is the firmware's drawing context (buffer 0x38, width 0x3c, height 0x40, UI resource 0x5c).

Frame of the cave (FRAME bytes): 0x20 popup rectangle, 0x40 work path, 0x48/0x4c log, 0x60 slot, 0x64 slot flag pointer,
0x68 FLIP target, 0x6c CONT target, 0x70 ORIG target, 0x100 state file path, 0x1c0 shell command.
"""
from __future__ import annotations

from .mips import asm, callabs, callslot, cstring, jabs, lia, place

COMMON = 0x43CFC0
COMMON_SIZE = 1392
STUB = 0x464854
STUB_SIZE = 1340
FRAME = 0x300

HOOKS = {
    "load": (0x4280C0, "1000028e6b004014", "LD"),
    "save": (0x4277F4, "1000028e5b004014", "SV"),
}

STATE_PATH = b"%s/states/%s/%s.sv%d\x00"
COMMAND = b'rm -f "%s" >> /mnt/sdcard/cubegm/delgame.log 2>&1\x00'
LOG_PATH = b"/mnt/sdcard/cubegm/rkgame.log\x00"
APPEND = b"a\x00"
LOG_FORMAT = b"delsave rc=%d cmd=%s\n\x00"


def _text(x, y, size, color, addr):
    return """
  lw    $a0, 0x38($s0)
  addiu $a1, $zero, %d
  addiu $a2, $zero, %d
  addiu $a3, $zero, %d
  ori   $t0, $zero, 0x%x
  sw    $t0, 0x10($sp)
  %s
  sw    $t0, 0x14($sp)
  %s
""" % (x, y, size, color, lia("$t0", addr), callabs(0x41D22C))


def _stub(name, slot_reg, flag_ptr_asm, flip, cont):
    return """
%(n)s:
  addiu $t0, $zero, 0x1000
  bne   $v0, $t0, %(n)sORIG
  nop
  addiu $sp, $sp, -%(F)d
  sw    %(slot)s, 0x60($sp)
  %(arr)s
  sw    $t2, 0x64($sp)
  %(lflip)s
  sw    $t0, 0x68($sp)
  %(lcont)s
  sw    $t0, 0x6c($sp)
  %(lorig)s
  sw    $t0, 0x70($sp)
  %(jcommon)s
  nop
%(n)sORIG:
  lw    $v0, 0x10($s0)
  beqz  $v0, %(n)sCONT
  nop
  %(jflip)s
  nop
%(n)sCONT:
  %(jcont)s
  nop
""" % dict(n=name, F=FRAME, slot=slot_reg, arr=flag_ptr_asm, lflip=lia("$t0", flip), lcont=lia("$t0", cont),
           lorig="%(lorig_" + name + ")s", jcommon=jabs(COMMON), jflip=jabs(flip), jcont=jabs(cont))


def _stubs_source():
    text = ".set noreorder\n"
    text += _stub("LD", "$s1", "sll $t2, $s1, 2\n  addu $t2, $t2, $s8", 0x428274, 0x4280CC)
    text += _stub("SV", "$s2", "sll $t2, $s2, 2\n  addu $t2, $t2, $s3\n  addiu $t2, $t2, 0x230", 0x427968, 0x427800)
    return text


def _common_source(A):
    texts = (_text(255, 200, 0x18, 0xFA08, A["title"]) + _text(255, 232, 0x14, 0xFFFF, A["sub"]) +
             _text(255, 262, 0x14, 0xFFFF, A["yes"]) + _text(390, 262, 0x14, 0xFFFF, A["no"]))
    return """
  .set noreorder
COMMON:
  %(callwp)s
  sw    $v0, 0x40($sp)
  %(callgt)s
  sll   $v0, $v0, 2
  lui   $t1, 0x53
  lw    $t1, -0x10c0($t1)
  addu  $t1, $t1, $v0
  lw    $t1, 0($t1)
  sll   $t1, $t1, 2
  lui   $t2, 0x53
  lw    $t2, -0x1298($t2)
  addu  $t2, $t2, $t1
  lw    $a3, 0($t2)
  lui   $t3, 0x53
  lw    $t3, -0x11c8($t3)
  sw    $t3, 0x10($sp)
  lw    $t4, 0x60($sp)
  sw    $t4, 0x14($sp)
  addiu $a0, $sp, 0x100
  %(fpath)s
  lw    $a2, 0x40($sp)
  %(sprintf)s
  addiu $a0, $sp, 0x100
  or    $a1, $zero, $zero
  %(access)s
  bnez  $v0, EXITC
  nop
  addiu $t5, $sp, 0x20
  addiu $t6, $zero, 0xf0
  sw    $t6, 4($t5)
  addiu $t6, $zero, 0xb4
  sw    $t6, 8($t5)
  addiu $t6, $zero, 0x266
  sw    $t6, 0xc($t5)
  addiu $t6, $zero, 0x12c
  sw    $t6, 0x10($t5)
  lw    $t6, 0x3c($s0)
  sll   $t6, $t6, 1
  sw    $t6, 0x14($t5)
  lui   $t7, 0x53
  lw    $t7, -0x1604($t7)
  lw    $t6, -0x40f8($t7)
  addiu $t9, $zero, -3
  and   $t6, $t6, $t9
  sw    $t6, -0x40f8($t7)
  addiu $a0, $sp, 0x20
  %(popwin)s
%(texts)s
  lw    $a0, 0x38($s0)
  lw    $a1, 0x3c($s0)
  lw    $a2, 0x40($s0)
  sll   $a3, $a1, 1
  lui   $t9, 0x53
  lw    $t9, -0x14ec($t9)
  jalr  $t9
  nop
  %(rj)s
  lui   $t0, 0x53
  lw    $t0, -0x1600($t0)
  sw    $zero, 0x57ec($t0)
  %(gticks)s
  lui   $t0, 0x53
  lw    $t0, -0x1600($t0)
  sw    $v0, 0x57f0($t0)
LOOPC:
  %(rj)s
  addiu $t0, $zero, 0x2000
  beq   $v0, $t0, DELC
  nop
  addiu $t0, $zero, 0x4000
  beq   $v0, $t0, CANCELC
  nop
  %(wnmi)s
  b     LOOPC
  nop
DELC:
  addiu $a0, $sp, 0x1c0
  %(fcmd)s
  addiu $a2, $sp, 0x100
  %(sprintf)s
  addiu $a0, $sp, 0x1c0
  %(system)s
  sw    $v0, 0x48($sp)
  %(lp)s
  %(la)s
  %(fopen)s
  beqz  $v0, NOLOGC
  sw    $v0, 0x4c($sp)
  or    $a0, $v0, $zero
  %(lf)s
  lw    $a2, 0x48($sp)
  addiu $a3, $sp, 0x1c0
  lui   $t9, 0x53
  lw    $t9, -0x15f0($t9)
  jalr  $t9
  nop
  lw    $a0, 0x4c($sp)
  %(fclose)s
NOLOGC:
  lw    $t2, 0x64($sp)
  sw    $zero, 0($t2)
  addiu $a0, $sp, 0x20
  %(popoff)s
  lw    $t8, 0x60($sp)
  lw    $a0, 0x38($s0)
  lw    $a1, 0x3c($s0)
  sll   $a1, $a1, 1
  lw    $a2, 0x5c($s0)
  addiu $a3, $t8, 0xb
  %(redraw)s
  lw    $t8, 0x60($sp)
  or    $a0, $t8, $zero
  or    $a1, $t8, $zero
  %(tumble)s
  b     FLIPC
  nop
CANCELC:
  addiu $a0, $sp, 0x20
  %(popoff)s
FLIPC:
  lw    $t9, 0x68($sp)
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
  jr    $t9
  nop
EXITC:
  lw    $t9, 0x70($sp)
  addiu $sp, $sp, %(F)d
  lw    $gp, 0x18($sp)
  jr    $t9
  nop
""" % dict(F=FRAME, callwp=callabs(0x41985C), callgt=callabs(0x4329B8), fpath=lia("$a1", A["path"]),
           sprintf=callslot(-0x15D8), access=callslot(-0x14F4), popwin=callabs(0x4262F8), popoff=callabs(0x4266DC),
           rj=callabs(0x41DB00), wnmi=callabs(0x41DB34), gticks=callabs(0x41AB28), system=callslot(-0xBD4),
           fopen=callslot(-0x15D0), fclose=callslot(-0x15C8), fcmd=lia("$a1", A["cmd"]), lp=lia("$a0", A["log"]),
           la=lia("$a1", A["amode"]), lf=lia("$a1", A["lfmt"]), texts=texts, redraw=callabs(0x41895C),
           tumble=callabs(0x4270C0))


def build(texts: dict):
    """Return ``{"common": (addr, bytes), "stubs": (addr, bytes), "entries": {...}}``.  ``texts``: title, sub, yes, no."""
    strings = [("title", cstring(texts["title"])), ("sub", cstring(texts["sub"])), ("yes", cstring(texts["yes"])),
               ("no", cstring(texts["no"])), ("path", STATE_PATH), ("cmd", COMMAND), ("log", LOG_PATH),
               ("amode", APPEND), ("lfmt", LOG_FORMAT)]

    def stubs(orig_ld, orig_sv, markers=False):
        text = _stubs_source().replace("%(lorig_LD)s", lia("$t0", orig_ld)).replace("%(lorig_SV)s", lia("$t0", orig_sv))
        if markers:  # measuring pass: find where the labels end up
            nl = chr(10)
            for label, mark in (("LDORIG", 0xDEAD0001), ("SV", 0xDEAD0002), ("SVORIG", 0xDEAD0003)):
                text = text.replace(nl + label + ":" + nl, nl + label + ":" + nl + "  .word 0x%08x" % mark + nl, 1)
        return asm(text, STUB)

    measured = stubs(0x464000, 0x464000, markers=True)
    find = lambda mark: measured.index(mark.to_bytes(4, "little"))
    off_ld_orig, off_sv, off_sv_orig = find(0xDEAD0001), find(0xDEAD0002) - 4, find(0xDEAD0003) - 8
    orig_ld, orig_sv = STUB + off_ld_orig, STUB + off_sv_orig
    stub_code = stubs(orig_ld, orig_sv)
    data_base = (STUB + len(stub_code) + 3) & ~3
    offsets, blob = place(strings)
    addr = {name: data_base + off for name, off in offsets.items()}
    common = asm(_common_source(addr), COMMON)
    stub_all = stub_code + bytes(data_base - (STUB + len(stub_code))) + blob
    if len(common) > COMMON_SIZE or len(stub_all) > STUB_SIZE:
        raise RuntimeError("delete-save caves do not fit (%d/%d, %d/%d)" % (len(common), COMMON_SIZE, len(stub_all), STUB_SIZE))
    return {"common": (COMMON, common), "stubs": (STUB, stub_all), "entries": {"load": STUB, "save": STUB + off_sv}}
