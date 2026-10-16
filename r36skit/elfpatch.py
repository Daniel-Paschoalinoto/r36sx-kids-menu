"""Tiny helper to read and patch the 32-bit little-endian MIPS ELF program (``rkgame``).

Pequeno utilitário para ler e alterar o programa ELF de 32 bits (``rkgame``).
Every write goes through an address (virtual address, as shown in a disassembler), never a raw file offset.
"""
from __future__ import annotations

import hashlib
import struct


class PatchError(RuntimeError):
    """Raised when the firmware does not look like the build these patches were made for."""


class Elf:
    def __init__(self, data: bytes):
        self.data = bytearray(data)
        phoff = struct.unpack_from("<I", self.data, 0x1C)[0]
        phentsize, phnum = struct.unpack_from("<HH", self.data, 0x2A)
        self._segments = []
        for i in range(phnum):
            p_type, p_off, p_va, _pa, p_filesz, _memsz, _flags, _align = struct.unpack_from(
                "<8I", self.data, phoff + i * phentsize
            )
            if p_type == 1:  # PT_LOAD
                self._segments.append((p_va, p_off, p_filesz))

    # ------------------------------------------------------------------ io
    @classmethod
    def load(cls, path) -> "Elf":
        with open(path, "rb") as fh:
            return cls(fh.read())

    def save(self, path) -> None:
        with open(path, "wb") as fh:
            fh.write(self.data)

    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    # ------------------------------------------------------------- address
    def offset(self, va: int) -> int:
        for seg_va, seg_off, seg_size in self._segments:
            if seg_va <= va < seg_va + seg_size:
                return seg_off + va - seg_va
        raise PatchError("address 0x%x is not backed by the file" % va)

    def read(self, va: int, size: int) -> bytes:
        off = self.offset(va)
        return bytes(self.data[off : off + size])

    def write(self, va: int, blob: bytes) -> None:
        off = self.offset(va)
        self.data[off : off + len(blob)] = blob

    # -------------------------------------------------------------- patches
    def patch(self, va: int, expected_hex: str, new_hex: str, what: str = "") -> None:
        """Replace bytes at ``va`` only if they are exactly what we expect (or already patched)."""
        expected, new = bytes.fromhex(expected_hex), bytes.fromhex(new_hex)
        current = self.read(va, len(expected))
        if current == new:
            return
        if current != expected:
            raise PatchError(
                "unexpected bytes at 0x%x (%s): found %s, expected %s" % (va, what, current.hex(), expected.hex())
            )
        self.write(va, new)

    def hook(self, va: int, expected_hex: str, target: int, what: str = "") -> None:
        """Turn two instructions into ``j target ; nop`` (idempotent: a previous hook is simply retargeted)."""
        expected = bytes.fromhex(expected_hex)
        current = self.read(va, 8)
        already_jump = (current[3] >> 2) == 2 and current[4:] == bytes(4)
        if current != expected and not already_jump:
            raise PatchError(
                "unexpected bytes at hook 0x%x (%s): found %s, expected %s" % (va, what, current.hex(), expected.hex())
            )
        self.write(va, jump(target))


def jump(target: int) -> bytes:
    """MIPS ``j target`` followed by a ``nop`` delay slot."""
    return struct.pack("<I", 0x08000000 | ((target >> 2) & 0x3FFFFFF)) + bytes(4)
