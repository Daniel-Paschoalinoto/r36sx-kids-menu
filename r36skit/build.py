"""Build the kids menu: reads YOUR stock ``cubegm`` folder + ``config.toml``, writes the changed files to ``output/``.

Gera o menu: lê a SUA pasta ``cubegm`` original + ``config.toml`` e grava os arquivos alterados em ``output/``.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path

from . import __version__
from .art import screens
from .art.draw import Theme
from .art.rgb565 import dec
from .config import ROOT, ConfigError, load as load_config
from .elfpatch import Elf, PatchError
from .patches.apply import SUPPORTED_RKGAME_SHA256, Options, apply_all
from .strings import load as load_strings

DATA = Path(__file__).parent / "data"
LANG_FILES = ("Movie", "Movie_", "Music", "Music_", "Photo", "Photo_", "E-Book", "E-Book_", "Title_Media", "Title_Game")
NO_COVER = "_no_cover"


# ------------------------------------------------------------------------------------------ stock folder
def find_cubegm(stock: Path) -> Path:
    """Accept the SD-card root, the ``cubegm`` folder itself, or a folder that contains ``cubegm``."""
    for cand in (stock, stock / "cubegm"):
        if (cand / "rkgame").is_file():
            return cand
    for hit in sorted(stock.rglob("rkgame")):
        if hit.is_file() and (hit.parent / "resource.cpd").is_file():
            return hit.parent
    raise SystemExit(
        "Could not find 'rkgame' inside %s\n"
        "  -> copy the 'cubegm' folder of your SD card (original firmware) into the 'stock' folder.\n"
        "Não encontrei o 'rkgame' em %s\n"
        "  -> copie a pasta 'cubegm' do seu cartão SD (firmware original) para dentro da pasta 'stock'." % (stock, stock)
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_stock(cubegm: Path) -> list[str]:
    """Return a list of problems (empty = compatible).  Used by ``--check`` and at the start of every build."""
    problems = []
    needed = ["rkgame", "resource.cpd", "UI_Res.cpd", "language/Movie.raw", "xgame-logo.bmp",
              "cores/.pcsx4all/pcsx4all.cfg"]
    for rel in needed:
        if not (cubegm / rel).exists():
            problems.append("missing / falta: cubegm/%s" % rel)
    rk = cubegm / "rkgame"
    if rk.is_file():
        digest = sha256_file(rk)
        if digest != SUPPORTED_RKGAME_SHA256:
            first = open(rk, "rb").read(4)
            what = "an ELF program" if first == b"\x7fELF" else "NOT an ELF program (already modified? other firmware?)"
            problems.append(
                "rkgame is not the supported build / rkgame não é a versão suportada (%s)\n"
                "      found / encontrado : %s\n      expected / esperado: %s"
                % (what, digest, SUPPORTED_RKGAME_SHA256))
    return problems


# ------------------------------------------------------------------------------------------ zip helpers
def read_zip(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}


def rewrite_zip(src: Path, dst: Path, replace: dict[str, bytes]) -> None:
    """Copy ``src`` to ``dst`` replacing some entries; entry order and names are kept."""
    buf = io.BytesIO()
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zo:
        names = [i.filename for i in zi.infolist()]
        unknown = set(replace) - set(names)
        if unknown:
            raise SystemExit("%s does not contain %s (different firmware?)\n%s não contém %s" % (src.name, unknown, src.name, unknown))
        for info in zi.infolist():
            zo.writestr(info.filename, replace.get(info.filename) or zi.read(info.filename), zipfile.ZIP_DEFLATED)
    data = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)


# ------------------------------------------------------------------------------------------ the build
def build(cfg_path: Path | None, stock: Path, out: Path, force: bool = False, log=print) -> Path:
    cfg = load_config(cfg_path)
    strings = load_strings(cfg.language)
    theme = Theme(cfg, strings)
    cubegm = find_cubegm(stock)
    log("Firmware folder / pasta do firmware: %s" % cubegm)

    problems = check_stock(cubegm)
    if problems and not force:
        log("\nCannot continue / não posso continuar:")
        for p in problems:
            log("  - " + p)
        log("\nSee docs/en/COMPATIBILITY.md  /  veja docs/pt-BR/COMPATIBILIDADE.md\n"
            "(use --force to try anyway - the program refuses to change code it does not recognise)")
        raise SystemExit(2)

    ocube = out / "cubegm"
    if out.exists():
        shutil.rmtree(out)
    ocube.mkdir(parents=True)
    preview = out / "preview"
    preview.mkdir()

    # 1. program ---------------------------------------------------------------------------------------
    log("[1/6] rkgame (code patches / ajustes de código)")
    options = Options(resume_last_game=cfg.resume_last_game, delete_game=cfg.delete_game, delete_save=cfg.delete_save,
                      hide_bin=cfg.hide_bin_files, no_cover_name=NO_COVER)
    try:
        elf = apply_all(Elf.load(cubegm / "rkgame"), strings.dialog_texts(), options, check_hash=not force)
    except PatchError as exc:
        raise SystemExit("\nERROR / ERRO: %s" % exc)
    elf.save(ocube / "rkgame")

    # 2. UI_Res.cpd: main menu pictures ------------------------------------------------------------------
    log("[2/6] main menu pictures / imagens do menu principal (UI_Res.cpd)")
    raws, shots = screens.build_ui_res_backgrounds(theme)
    rewrite_zip(cubegm / "UI_Res.cpd", ocube / "UI_Res.cpd", {n + ".raw": b for n, b in raws.items()})
    for name in ("MovieBg", "MusicBg", "PhotoBg", "DOWNLOAD"):
        shots[name].convert("RGB").save(preview / ("menu_%s.png" % name))

    # 3. resource.cpd: game list, loading, pause, search, footer ------------------------------------------
    log("[3/6] game list, pause and search screens / lista de jogos, pausa e busca (resource.cpd)")
    res = read_zip(cubegm / "resource.cpd")
    menu_raw, menu_bg = screens.build_menu_raw(theme, res["menu.raw"])
    game_raw, game_bg = screens.build_game_raw(theme, res["game.raw"])
    search_raw, search_bg = screens.build_search_raw(theme, res["search.raw"])
    lbg = screens.load_bg(theme)
    from .art.rgb565 import enc
    replace = {"menu.raw": menu_raw, "game.raw": game_raw, "search.raw": search_raw, "load_bg.raw": enc(lbg),
               "footbar3.raw": screens.build_footbar3(theme, res["footbar3.raw"])}
    rewrite_zip(cubegm / "resource.cpd", ocube / "resource.cpd", replace)
    menu_bg.save(preview / "game_list.png")
    game_bg.save(preview / "pause_menu.png")
    search_bg.save(preview / "search.png")
    lbg.save(preview / "loading.png")

    # 4. ui_<lang>.cpd: pause menu for each language ---------------------------------------------------------
    log("[4/6] pause menu for every language / menu de pausa de todos os idiomas (ui_*.cpd)")
    for ui in sorted(cubegm.glob("ui_??.cpd")):
        rewrite_zip(ui, ocube / ui.name, {"game.raw": game_raw})

    # 5. language sprites + splash --------------------------------------------------------------------------
    log("[5/6] labels and start screen / rótulos e tela de abertura")
    for filename, data in screens.build_language_sprites(theme).items():
        stock_file = cubegm / "language" / filename
        if stock_file.exists() and stock_file.stat().st_size != len(data):
            raise SystemExit("language/%s has an unexpected size (different firmware?)" % filename)
        (ocube / "language").mkdir(exist_ok=True)
        (ocube / "language" / filename).write_bytes(data)
    splash = screens.splash(theme)
    splash.convert("RGBA").save(ocube / "xgame-logo.bmp")
    splash.save(preview / "start_screen.png")

    # 6. scripts, PlayStation settings, placeholder cover --------------------------------------------------------
    log("[6/6] scripts, PlayStation settings, 'no cover' picture / scripts, ajustes do PlayStation, imagem 'sem capa'")
    for name in ("delgame.sh", "setlast.sh"):
        shutil.copyfile(DATA / "scripts" / name, ocube / name)
    cfg_src = cubegm / "cores" / ".pcsx4all" / "pcsx4all.cfg"
    if cfg.psx_speed_tweaks and cfg_src.is_file():
        text = cfg_src.read_bytes()
        text = re.sub(rb"(?im)^(ShowFps)\s+1", rb"\1 0", text)
        text = re.sub(rb"(?im)^(lighting)\s+1", rb"\1 0", text)
        dst = ocube / "cores" / ".pcsx4all"
        dst.mkdir(parents=True)
        (dst / "pcsx4all.cfg").write_bytes(text)
    images = out / "roms" / "images"
    images.mkdir(parents=True)
    screens.no_cover_image(theme).save(images / (NO_COVER + ".png"))

    log("\nDone / Pronto!  ->  %s" % out)
    log("Look at / veja as imagens em: %s" % preview)
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # accents on the Windows console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="build", description="R36SX Kids Menu %s - builds the modified menu files." % __version__)
    ap.add_argument("--config", type=Path, default=ROOT / "config.toml", help="settings file / arquivo de configurações")
    ap.add_argument("--stock", type=Path, default=ROOT / "stock", help="folder with your ORIGINAL cubegm / pasta com o cubegm ORIGINAL")
    ap.add_argument("--out", type=Path, default=ROOT / "output", help="where to write the result / onde gravar o resultado")
    ap.add_argument("--check", action="store_true", help="only check that your firmware is compatible / só verifica a compatibilidade")
    ap.add_argument("--force", action="store_true", help="ignore the firmware check (advanced) / ignora a verificação (avançado)")
    args = ap.parse_args(argv)
    try:
        if args.check:
            cubegm = find_cubegm(args.stock)
            problems = check_stock(cubegm)
            if problems:
                print("NOT compatible / NÃO compatível:")
                for p in problems:
                    print("  - " + p)
                return 2
            print("OK - compatible firmware / firmware compatível (rkgame sha256 %s...)" % SUPPORTED_RKGAME_SHA256[:12])
            return 0
        build(args.config, args.stock, args.out, args.force)
    except ConfigError as exc:
        print(exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
