"""Emulator test (Unicorn) of the menu patches on a really patched rkgame.

Teste em emulador (Unicorn) dos patches de menu num rkgame realmente alterado.
Run:  python tests/emulator/run_menu_checks.py <original rkgame>      (needs: pip install unicorn)
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unicorn import UC_ARCH_MIPS, UC_MODE_LITTLE_ENDIAN, UC_MODE_MIPS32, Uc, UcError
from unicorn.mips_const import (UC_MIPS_REG_A0, UC_MIPS_REG_GP, UC_MIPS_REG_RA, UC_MIPS_REG_S0, UC_MIPS_REG_T9, UC_MIPS_REG_V0,
                                UC_MIPS_REG_V1)

from r36skit import strings
from r36skit.elfpatch import Elf
from r36skit.patches import listfilter, menu_lock
from r36skit.patches.apply import Options, apply_all

if len(sys.argv) != 2:
    sys.exit(__doc__)
stock = Elf.load(sys.argv[1])
patched = apply_all(Elf.load(sys.argv[1]), strings.load("en").dialog_texts(), Options())

ok = True


def chk(name, cond):
    global ok
    ok &= bool(cond)
    print(("OK   " if cond else "ERRO ") + name)


def machine(elf):
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + UC_MODE_LITTLE_ENDIAN)
    for va, off, size in elf._segments:
        base = va & ~0xFFF
        end = (va + size + 0xFFF) & ~0xFFF
        try:
            mu.mem_map(base, end - base)
        except UcError:
            pass
        mu.mem_write(va, bytes(elf.data[off:off + size]))
    mu.mem_map(0x10000000, 0x10000)
    mu.mem_map(0x20000000, 0x1000)
    return mu


# ---------- 1. the settings-entry code is the stock code again ----------
for va, size, what in ((0x414C88, 0x10C, "settings-entry block A"), (0x415124, 0x130, "settings-entry block B")):
    chk("stock bytes kept: " + what, stock.read(va, size) == patched.read(va, size))


# ---------- 1b. page order: R = next page, L = previous page ----------
def beq_target(elf, va):
    word = int.from_bytes(elf.read(va, 4), "little")
    assert (word >> 26) == 4, hex(va)
    off = word & 0xFFFF
    off -= 0x10000 if off & 0x8000 else 0
    return va + 4 + off * 4


MEDIA_ENTRY, SETTINGS_ENTRY_A, SETTINGS_ENTRY_B, TO_GAMES_FROM_MEDIA = 0x414BF8, 0x414C88, 0x415124, 0x4150B0
chk("games page: R -> media", beq_target(patched, 0x414894) == MEDIA_ENTRY)
chk("games page: L -> settings", beq_target(patched, 0x4147C4) == SETTINGS_ENTRY_A)
chk("media page: R -> settings", beq_target(patched, 0x414A6C) == SETTINGS_ENTRY_B)
chk("media page: L -> games", beq_target(patched, 0x414974) == TO_GAMES_FROM_MEDIA)
chk("settings page: R is the 'to games' handler (inline), L the 'to media' handler",
    patched.read(0x4149C0, 4).hex() == "00080224" and patched.read(0x414240, 4).hex() == "00040224")

# ---------- 2. settings page: rows 0 -> 1 -> 4 and back ----------
mu = machine(patched)
PTR = 0x10000100


def run_until(mu, start, stop, regs, count=200):
    mu.reg_write(UC_MIPS_REG_GP, 0x10009000)
    for reg, val in regs.items():
        mu.reg_write(reg, val)
    mu.reg_write(UC_MIPS_REG_RA, 0x20000000)
    try:
        mu.emu_start(start, stop, count=count)
    except UcError as exc:
        return str(exc)
    return None


def down(idx):
    mu.mem_write(PTR, bytes([idx]))
    err = run_until(mu, 0x414F28, 0x414EBC, {UC_MIPS_REG_V0: idx, UC_MIPS_REG_V1: PTR})
    return None if err else mu.reg_read(UC_MIPS_REG_V0)


def up(idx):
    mu.mem_write(PTR, bytes([idx]))
    mu.mem_write(PTR + 0x40, struct.pack("<I", PTR))  # a0 points to a pointer (lw a0,0(a0))
    err = run_until(mu, 0x414EAC, 0x414EBC, {UC_MIPS_REG_S0: PTR, UC_MIPS_REG_A0: PTR + 0x40, UC_MIPS_REG_V1: PTR})
    return None if err else mu.reg_read(UC_MIPS_REG_V0)


chk("settings down: volume(0) -> brightness(1)", down(0) == 1)
chk("settings down: brightness(1) -> controls(4)", down(1) == 4)
chk("settings down: controls(4) stays on controls", down(4) == 4)
chk("settings up: controls(4) -> brightness(1)", up(4) == 1)
chk("settings up: brightness(1) -> volume(0)", up(1) == 0)

# ---------- 3. the relocated list filter behaves as before ----------
mu = machine(patched)
cases = [("images", 4, 0), ("Images", 4, 0), ("imagesx", 4, 1), ("aventura", 4, 1), ("..", 4, 1),
         ("Tekken 3 (USA).cue", 8, 1), ("Tekken 3 (USA) (Track 1).bin", 8, 0), ("x.bin", 8, 0), ("jogo.gba", 8, 1),
         ("JOGO.GBA", 8, 1), ("a.zip", 8, 1), ("a.7z", 8, 0), ("semext", 8, 0), ("foo.sav", 8, 0), ("x.png", 8, 0),
         ("x.nes", 8, 1), ("x.md", 8, 1), ("x.sfc", 8, 1), ("x.txt", 8, 0), ("x.cuex", 8, 0)]
for name, dtype, expected in cases:
    entry = struct.pack("<IIHB", 1, 2, len(name) + 12, dtype) + name.encode() + b"\0"
    mu.mem_write(0x10000000, entry)
    err = run_until(mu, listfilter.FILTER_AT, 0x20000000, {UC_MIPS_REG_A0: 0x10000000}, count=5000)
    got = 1 if (not err and mu.reg_read(UC_MIPS_REG_V0)) else 0
    chk("filter %-32s -> %s" % (name, "keep" if expected else "hide"), got == expected and not err)

print("ALL OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
