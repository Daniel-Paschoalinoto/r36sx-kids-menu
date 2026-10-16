"""Maintainer tool: builds the ready-to-copy packs (English + Português) that go to GitHub Releases.

Ferramenta do mantenedor: gera os pacotes prontos para copiar (English + Português) que vão para o GitHub Releases.
Usage: python make_release.py <folder-with-stock-cubegm>
"""
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from r36skit import __version__
from r36skit.build import build
from r36skit.config import ROOT

README = """R36SX Kids Menu {v} - ready pack ({lang})

EN: 1) Make a backup copy of your SD card. 2) Copy the folders "cubegm" and "roms" from this zip to the root of the
    SD card, answer "Replace / Merge". 3) Done. Want your own colours, texts or pictures? Use the builder:
    https://github.com/Daniel-Paschoalinoto/r36sx-kids-menu
PT: 1) Faça uma cópia de segurança do cartão SD. 2) Copie as pastas "cubegm" e "roms" deste zip para a raiz do cartão
    e responda "Substituir / Mesclar". 3) Pronto. Quer cores, textos ou imagens suas? Use o gerador:
    https://github.com/Daniel-Paschoalinoto/r36sx-kids-menu

Only works with the original firmware this tool recognises (python build.py --check).
Só funciona com o firmware original que a ferramenta reconhece (python build.py --check).
"""


def main(stock: Path):
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for lang in ("en", "pt-BR"):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            text = (ROOT / "config.toml").read_text(encoding="utf-8").replace('language = "en"', 'language = "%s"' % lang)
            text = text.replace('photo = "my_files/photo.jpg"', 'photo = ""').replace('mascot = "my_files/mascot.png"', 'mascot = ""')
            cfg.write_text(text, encoding="utf-8")
            out = Path(tmp) / "out"
            build(cfg, stock, out, log=lambda *a: None)
            name = dist / ("R36SX-Kids-Menu-v%s-%s.zip" % (__version__, lang))
            with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
                for f in sorted(out.rglob("*")):
                    if f.is_file() and "preview" not in f.relative_to(out).parts:
                        z.write(f, f.relative_to(out).as_posix())
                z.writestr("READ-ME.txt", README.format(v=__version__, lang=lang))
            print(name, name.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
