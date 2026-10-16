# Step-by-step guide

🇧🇷 [Português](../pt-BR/GUIA.md)

## 0. Before you start

- Make a **full copy of your SD card** to your computer (copy everything). If something goes wrong you can copy it back.
- You need a computer with Windows (Linux/macOS also work) and a card reader.
- The SD card has a folder called **`cubegm`** (the console's program and menu). That is the one we change.

## 1. Fastest way: the ready pack

1. Download `R36SX-Kids-Menu-…-en.zip` from the [`packs`](../../packs) folder of this project (click the file, then the download button).
2. Open the zip. Copy the folders **`cubegm`** and **`roms`** to the **root of the SD card**. When Windows asks, choose **Replace / Merge**.
3. Put the card back in the console. Done.

The pack uses the placeholder pictures and default colours. To personalise, use the builder below.

## 2. Build your own look

### 2.1 Install Python (once)
Download Python 3.11 or newer from <https://www.python.org/downloads/>. In the installer tick **"Add python.exe to PATH"**.

### 2.2 Where to put things

| Folder / file | What to put there |
|---|---|
| `stock/` | The **`cubegm`** folder from your SD card (original, unmodified). Result: `stock/cubegm/rkgame` |
| `my_files/` | **Your pictures**: `photo.jpg` (start screen), `mascot.png` (menus), optional `font.ttf` |
| `config.toml` | **Your choices** (colours, texts, language, features). Open with Notepad |
| `r36skit/data/strings/` | All the menu texts per language (`en.json`, `pt-BR.json`) |

### 2.3 Check your console is supported
Open a terminal in the project folder (in Windows: type `cmd` in the folder's address bar) and run:

```bash
python build.py --check
```

`OK - compatible firmware` → continue. Otherwise read [COMPATIBILITY](COMPATIBILITY.md).

### 2.4 Edit `config.toml`
Open it with Notepad. Every line has a note above it in English and Portuguese. The most useful ones:

| Setting | Meaning |
|---|---|
| `language` | `"en"` or `"pt-BR"` |
| `console_name` | Short title at the top of the screens (max ~16 letters) |
| `[splash] big_text / small_text` | The two lines of the start screen, e.g. `"R36S"` and `"of Anna"` |
| `photo` | Your photo file in `my_files`. `photo_focus_x/y` move the square crop onto the face (0–1), `photo_zoom` zooms in |
| `mascot` | Picture on the menus (character, logo…) – it is cropped to 4:3 |
| `[colors]` | Six colours in `#RRGGBB`. Search the web for "color picker" |
| `[features]` | Switch each extra on (`true`) or off (`false`) |

### 2.5 Build
Double-click **`build.bat`** (Windows) or run `./build.sh`. The first time it installs the needed packages (internet needed once). It takes a few seconds.

Look at the pictures in **`output/preview`**. Not happy? Change `config.toml` and build again – it is free and safe, nothing touches your card yet.

### 2.6 Copy to the SD card
Copy everything inside **`output`** (the folders `cubegm` and `roms`) to the root of the SD card, **Replace / Merge**. Do **not** copy `preview`.

## 3. Using the console

| You do | What happens |
|---|---|
| **L1 / R1** | Switch between Games, Videos, Music, Photos |
| **A** | Open / enter |
| **X** on a game in the list | Delete the game, its cover and files with the same name (asks first) |
| **X** on a slot in Pause → Load / Save | Delete that save (asks first) |
| Switch on while holding **B** | Skip "open last game" and go to the menu |

**Where do I put my files?**

| What | Where on the SD card |
|---|---|
| Games | `roms/` (any sub-folders you like, e.g. `roms/racing/`) |
| Covers | `roms/images/<exact game file name without extension>.png`, 240×240 |
| Videos / Music / Photos | folders `Movie`, `Music`, `Photo` |

Tips: **Mega Drive** games must end in `.md` (rename `.bin` → `.md`). **PlayStation** games open from the `.cue` file (the `.bin` stays hidden next to it).

## 4. Customising further

- **Change a text** (buttons, tips…): edit `r36skit/data/strings/en.json` (or your language) and build again. Keep texts short – the boxes are small.
- **New language:** copy `en.json` to `es.json`, translate the values (not the names on the left), set `language = "es"`. Letters outside the basic Latin set need a font that has them: put it in `my_files/font.ttf` and set `font = "my_files/font.ttf"`.
- **Tips box:** edit `"tips"` → `"lines"` in the language file (up to 2 lines).
- **Turn off an extra:** `[features]` in `config.toml`.

## 5. Troubleshooting

| Problem | Solution |
|---|---|
| `python` is not recognised | Reinstall Python and tick *Add python.exe to PATH*; reopen the window |
| *Could not find rkgame* | `stock/` must contain `cubegm/rkgame` (copy the folder from the card) |
| *rkgame is not the supported build* | Your firmware is different or already modified. Use the **original** copy. See [COMPATIBILITY](COMPATIBILITY.md) |
| Console shows the old menu | Files were not replaced. Copy again with *Replace* |
| Weird/black picture | Use a normal JPG/PNG; check `output/preview` first |
| Console does not start | Copy your backup of the card back (that's why you made it) |
| A game shows no cover | Cover name must equal the game file name, `.png`, 240×240, inside `roms/images` |
| `.bin` of a PlayStation game appears | Turn `hide_bin_files` on in `config.toml` |
