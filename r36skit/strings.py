"""Load the texts of a language.  / Carrega os textos de um idioma.

Languages are plain JSON files in ``r36skit/data/strings``.  To add a language, copy ``en.json`` to e.g. ``es.json``,
translate the values (not the keys) and use ``language = "es"`` in ``config.toml``.
Para adicionar um idioma, copie ``en.json`` para ``es.json``, traduza os valores (não as chaves) e use
``language = "es"`` no ``config.toml``.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).parent / "data" / "strings"


def available() -> list[str]:
    return sorted(p.stem for p in DATA.glob("*.json"))


class Strings:
    def __init__(self, data: dict, name: str):
        self.data = data
        self.name = name

    def __getitem__(self, dotted: str):
        node = self.data
        for part in dotted.split("."):
            node = node[part]
        return node

    def get(self, dotted: str, default=None):
        try:
            return self[dotted]
        except KeyError:
            return default

    def dialog_texts(self) -> dict:
        """The five strings used by the code patches (they are converted to plain ASCII there)."""
        d = self.data["dialogs"]
        return {k: d[k] for k in ("delete_game_title", "delete_game_sub", "delete_save_title", "delete_save_sub",
                                  "confirm_yes", "confirm_cancel")}


def load(language: str, overrides: dict | None = None) -> Strings:
    path = DATA / (language + ".json")
    if not path.exists():
        raise SystemExit(
            "Unknown language '%s'. Available / Disponíveis: %s" % (language, ", ".join(available()))
        )
    english = json.loads((DATA / "en.json").read_text(encoding="utf-8"))
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = _merge(english, data)  # missing keys fall back to English
    if overrides:
        merged = _merge(merged, overrides)
    return Strings(merged, language)


def _merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out
