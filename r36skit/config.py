"""Read ``config.toml`` and turn it into plain Python objects.

Lê o ``config.toml`` e transforma em objetos Python.  Errors are written in English AND Portuguese.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ConfigError(SystemExit):
    pass


def _hex(value: str, name: str) -> tuple[int, int, int]:
    text = str(value).strip().lstrip("#")
    if len(text) != 6 or any(c not in "0123456789abcdefABCDEF" for c in text):
        raise ConfigError(
            "config.toml: color '%s' = %r is not valid. Use #RRGGBB, e.g. #FFE028.\n"
            "config.toml: a cor '%s' = %r não é válida. Use #RRGGBB, por exemplo #FFE028." % (name, value, name, value)
        )
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


@dataclass
class Palette:
    sky_top: tuple = (40, 150, 255)
    sky_bottom: tuple = (10, 70, 190)
    panel: tuple = (8, 30, 110)
    accent: tuple = (255, 224, 40)
    outline: tuple = (10, 40, 120)
    highlight: tuple = (0, 150, 255)
    white: tuple = (255, 255, 255)



@dataclass
class Config:
    language: str = "en"
    console_name: str = "MY GAMES"
    font: Path | None = None
    splash_big: str = "R36SX"
    splash_small: str = "my retro console"
    photo: Path | None = None
    photo_focus: tuple = (0.5, 0.5)
    photo_zoom: float = 1.0
    mascot: Path | None = None
    palette: Palette = field(default_factory=Palette)
    resume_last_game: bool = True
    delete_game: bool = True
    delete_save: bool = True
    hide_bin_files: bool = True
    psx_speed_tweaks: bool = True
    root: Path = ROOT


def load(path: Path | None = None) -> Config:
    path = Path(path) if path else ROOT / "config.toml"
    if not path.exists():
        raise ConfigError("Cannot find %s\nNão encontrei %s" % (path, path))
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            "config.toml has a typo: %s\n(check quotes \"like this\" and that each line is name = value)\n"
            "O config.toml tem um erro de digitação: %s\n(confira as \"aspas\" e se cada linha é nome = valor)" % (exc, exc)
        ) from exc

    general, splash, menu = data.get("general", {}), data.get("splash", {}), data.get("menu", {})
    colors, features = data.get("colors", {}), data.get("features", {})
    cfg = Config(root=path.parent)

    cfg.language = str(general.get("language", cfg.language))
    cfg.console_name = str(general.get("console_name", cfg.console_name))[:24]
    cfg.font = _optional_file(cfg.root, general.get("font"))
    cfg.splash_big = str(splash.get("big_text", cfg.splash_big))[:12]
    cfg.splash_small = str(splash.get("small_text", cfg.splash_small))[:32]
    cfg.photo = _optional_file(cfg.root, splash.get("photo"))
    cfg.photo_focus = (_clamp(splash.get("photo_focus_x", 0.5)), _clamp(splash.get("photo_focus_y", 0.5)))
    cfg.photo_zoom = max(1.0, min(4.0, float(splash.get("photo_zoom", 1.0))))
    cfg.mascot = _optional_file(cfg.root, menu.get("mascot"))

    for name in ("sky_top", "sky_bottom", "panel", "accent", "outline", "highlight"):
        if name in colors:
            setattr(cfg.palette, name, _hex(colors[name], name))

    for name in ("resume_last_game", "delete_game", "delete_save", "hide_bin_files", "psx_speed_tweaks"):
        if name in features:
            setattr(cfg, name, bool(features[name]))
    return cfg


def _clamp(value) -> float:
    return max(0.0, min(1.0, float(value)))


def _optional_file(root: Path, name) -> Path | None:
    if not name:
        return None
    p = (root / str(name)).resolve()
    return p if p.is_file() else None
