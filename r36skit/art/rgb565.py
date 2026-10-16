"""RGB565 <-> Pillow helpers.  The console stores most menu pictures as little-endian RGB565."""
from __future__ import annotations

import numpy as np
from PIL import Image


def dec(data: bytes, w: int, h: int) -> Image.Image:
    a = np.frombuffer(data, dtype="<u2").reshape(h, w).astype(np.uint32)
    r = ((a >> 11) & 31) * 255 // 31
    g = ((a >> 5) & 63) * 255 // 63
    b = (a & 31) * 255 // 31
    return Image.fromarray(np.stack([r, g, b], -1).astype(np.uint8), "RGB")


def enc(im: Image.Image) -> bytes:
    a = np.asarray(im.convert("RGB")).astype(np.uint32)
    v = ((a[..., 0] >> 3) << 11) | ((a[..., 1] >> 2) << 5) | (a[..., 2] >> 3)
    return v.astype("<u2").tobytes()
