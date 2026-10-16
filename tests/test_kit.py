import json
from pathlib import Path

import pytest

from r36skit import config, strings
from r36skit.art import screens
from r36skit.art.draw import Theme
from r36skit.art.rgb565 import dec, enc
from r36skit.elfpatch import PatchError
from r36skit.patches.apply import SUPPORTED_RKGAME_SHA256, apply_all
from r36skit.elfpatch import Elf

ROOT = Path(__file__).resolve().parent.parent


def keys(d, prefix=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from keys(v, prefix + k + ".")
        else:
            yield prefix + k


def test_every_language_has_every_text():
    base = set(keys(json.loads((strings.DATA / "en.json").read_text(encoding="utf-8"))))
    for lang in strings.available():
        got = set(keys(json.loads((strings.DATA / (lang + ".json")).read_text(encoding="utf-8"))))
        assert base <= got, (lang, base - got)


def theme():
    cfg = config.load(ROOT / "config.toml")
    return Theme(cfg, strings.load(cfg.language))


def test_sprites_have_firmware_sizes():
    sizes = {"Movie.raw": 960000, "Music_.raw": 960000, "E-Book.raw": 960000, "Title_Game.raw": 768000}
    out = screens.build_language_sprites(theme())
    for name, size in sizes.items():
        assert len(out[name]) == size


def test_rgb565_roundtrip_is_stable():
    im = screens.no_cover_image(theme())
    assert enc(dec(enc(im), *im.size)) == enc(im)


def test_bad_color_is_explained_in_both_languages(tmp_path):
    bad = tmp_path / "c.toml"
    bad.write_text('[colors]\naccent = "yellow"\n', encoding="utf-8")
    with pytest.raises(config.ConfigError) as e:
        config.load(bad)
    assert "não é válida" in str(e.value) and "not valid" in str(e.value)


def test_unknown_firmware_is_refused():
    fake = bytearray(b"\x7fELF" + bytes(200))
    with pytest.raises(Exception):
        apply_all(Elf(bytes(fake)), strings.load("en").dialog_texts())


def test_patches_on_real_stock_if_available():
    stock = ROOT / "stock" / "cubegm" / "rkgame"
    if not stock.exists():
        pytest.skip("put your stock cubegm in stock/ to run this")
    elf = Elf.load(stock)
    if elf.sha256() != SUPPORTED_RKGAME_SHA256:
        pytest.skip("different firmware")
    out = apply_all(elf, strings.load("en").dialog_texts())
    assert out.sha256() != SUPPORTED_RKGAME_SHA256
