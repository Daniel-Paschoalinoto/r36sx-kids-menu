# R36SX Kids Menu 🎮

**A simple, colourful, kid-friendly menu for the cheap "R36S / R36SX" retro handheld clones (HiChip HC1600A, firmware `cubegm`).**
Only four big buttons – **Games · Videos · Music · Photos** – your own colours, your own texts, your child's photo on the start screen, and a few quality-of-life extras.

🇧🇷 [Leia em português](README.pt-BR.md)

| Main menu | Games | Start screen |
|---|---|---|
| ![menu](docs/images/menu_MovieBg.png) | ![games](docs/images/game_list.png) | ![start](docs/images/start_screen.png) |

> The pictures above are the **built-in placeholders**. You replace them with your own in one minute (see below).

## What you get

- 🧒 Menu reduced to **Games / Videos / Music / Photos** (settings, e-books and console list are hidden).
- 🎨 **Your colours, texts, language** (English or Português; add more by copying one text file) – everything in one easy file, `config.toml`.
- 🖼️ **Your photo** on the start screen and a **mascot/logo** on the menus. No picture? A drawn placeholder is used.
- ▶️ **Resume the last game** by itself when you switch the console on (hold **B** to go to the menu instead).
- 🗑️ **Press X to delete a game** – removes the game, its `.cue` files, files with the same name and its cover (asks first).
- 💾 **Press X to delete a save** on the pause menu's Load/Save screens.
- 🙈 `.bin` files hidden from the game list (PlayStation games open from the `.cue`).
- 🖼️ **Covers** from `roms/images/<game name>.png` (240×240), with a "no cover" picture for games that have none.
- ⚡ Optional PlayStation speed-up (lighting and FPS counter off).

## Quick start (3 steps, no programming)

> ⚠️ **Make a backup copy of your SD card first.** Always.

**Option A – ready pack (fastest; being published after a hardware test – use Option B until then).** Download `R36SX-Kids-Menu-…zip` from the [Releases](../../releases) page, open it, copy the `cubegm` and `roms` folders onto your SD card (answer *Replace/Merge*). Done.

**Option B – build your own look (your colours, photo, texts):**

1. Install [Python 3.11+](https://www.python.org/downloads/) (tick **"Add python.exe to PATH"**).
2. Copy the **`cubegm`** folder from your SD card (original firmware) into the **`stock`** folder of this project. Put your pictures in **`my_files`**. Open **`config.toml`** with Notepad and change what you like.
3. Double-click **`build.bat`** (Windows) or run `./build.sh` (Linux/macOS). Look at `output/preview`, then copy the contents of **`output`** to the SD card root (*Replace/Merge*).

📖 Full step-by-step guide with pictures of every option: **[docs/en/GUIDE.md](docs/en/GUIDE.md)**

## Is my console compatible?

This was made and tested **on one device** (an "R36SX V2.6" clone with the HiChip HC1600A chip, Linux 4.4, program `rkgame`). The code changes only apply to the exact original `rkgame` they were written for; any other file is **refused** and nothing is changed. Check yours in 10 seconds:

```bash
python build.py --check
```

Details and how to report a new model: [docs/en/COMPATIBILITY.md](docs/en/COMPATIBILITY.md).

## Documentation

| | English | Português |
|---|---|---|
| Step-by-step guide, customising, troubleshooting | [GUIDE](docs/en/GUIDE.md) | [GUIA](docs/pt-BR/GUIA.md) |
| Compatibility | [COMPATIBILITY](docs/en/COMPATIBILITY.md) | [COMPATIBILIDADE](docs/pt-BR/COMPATIBILIDADE.md) |
| How it works (for tinkerers) | [HOW-IT-WORKS](docs/en/HOW-IT-WORKS.md) | [COMO-FUNCIONA](docs/pt-BR/COMO-FUNCIONA.md) |
| Legal notes | [LEGAL](docs/en/LEGAL.md) | [LEGAL](docs/pt-BR/LEGAL.md) |

## Contributing

New language? Copy `r36skit/data/strings/en.json` to e.g. `es.json`, translate the values, set `language = "es"`. Pull requests and compatibility reports are welcome. Run the tests with `python -m pytest`.

## License

Code: [MIT](LICENSE). This project is **not affiliated** with any console maker. The console firmware belongs to its manufacturer – see [LEGAL](docs/en/LEGAL.md). Use at your own risk.
