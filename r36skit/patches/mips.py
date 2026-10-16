"""Small helpers to write the extra MIPS code ("caves") that we inject into dead code of the firmware.

Helpers para escrever o código MIPS extra ("caves") injetado em áreas mortas do firmware.
"""
from __future__ import annotations

import unicodedata

_KS = None


def assembler():
    global _KS
    if _KS is None:
        try:
            from keystone import KS_ARCH_MIPS, KS_MODE_LITTLE_ENDIAN, KS_MODE_MIPS32, Ks
        except ImportError as exc:  # pragma: no cover - friendly message
            raise SystemExit(
                "Missing dependency 'keystone-engine'. Run:  pip install -r requirements.txt\n"
                "Falta a dependência 'keystone-engine'. Rode:  pip install -r requirements.txt"
            ) from exc
        _KS = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
    return _KS


def asm(source: str, base: int) -> bytes:
    encoding, _count = assembler().asm(source, base)
    return bytes(encoding)


def jabs(target: int) -> str:
    """Assembler line that emits ``j target`` (absolute jump; the delay slot is written by the caller)."""
    return ".word 0x%08x" % (0x08000000 | ((target >> 2) & 0x3FFFFFF))


def lia(reg: str, addr: int) -> str:
    """Load a 32-bit absolute address into ``reg``."""
    return "lui %s, 0x%x\n ori %s, %s, 0x%x" % (reg, addr >> 16, reg, reg, addr & 0xFFFF)


def callslot(offset: int) -> str:
    """Call a libc function through its pointer slot (``0x530000 + offset``)."""
    return "lui $t9, 0x53\n lw $t9, %d($t9)\n jalr $t9\n nop" % offset


def callabs(addr: int) -> str:
    """Call a function of the program itself at an absolute address."""
    return "lui $t9, 0x%x\n ori $t9, $t9, 0x%x\n jalr $t9\n nop" % (addr >> 16, addr & 0xFFFF)


def cstring(text: str) -> bytes:
    """ASCII, NUL-terminated.  The firmware font only draws plain ASCII in these dialogs, so accents are removed."""
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore")
    return folded + b"\x00"


def place(blocks):
    """Lay out ``[(name, bytes)...]`` one after another; returns (``{name: offset}``, concatenated bytes)."""
    offsets, blob = {}, b""
    for name, data in blocks:
        offsets[name] = len(blob)
        blob += data
    return offsets, blob
