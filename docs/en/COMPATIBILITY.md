# Compatibility

🇧🇷 [Português](../pt-BR/COMPATIBILIDADE.md)

## What was tested

| | |
|---|---|
| Console | "R36SX V2.6" style clone (also sold as SF3000 / SF3500 / GB350 family – **not confirmed**), HiChip HC1600A (HC16xx), MIPS32 ~900 MHz, 256 MB, 640×480 screen |
| System | Linux 4.4.186, main program `rkgame`, launcher `icube`, folder `cubegm` on the SD card |
| `rkgame` SHA-256 | `57d8b4fd85e0aab44d17a51d209879c3f98130d066b622142736b42ad08ddcb9` (1,178,732 bytes) |

Everything was tried on real hardware, on that one build. **Other models or firmware versions are untested.**

## How the tool protects you

The code changes are written for exactly that `rkgame`. Before changing anything the tool checks the file's SHA-256 and every byte it is about to replace. If anything differs it **stops and changes nothing**. It never writes to your SD card – you copy the result yourself.

## Check yours

```bash
python build.py --check
```

- `OK` → supported.
- `rkgame is not the supported build` → either another firmware (not supported yet) or a file that was already modified. Use the **original** `cubegm` (a fresh backup).

## Other models

Clones look alike but ship different firmware. If your console has a `cubegm` folder and an `rkgame` file it *may* be close, but a different build needs the code addresses re-found (reverse-engineering). If you do that, open an issue or a pull request – see [HOW-IT-WORKS](HOW-IT-WORKS.md).

**Reporting your model:** open an issue with the "compatibility" template and paste the output of `python build.py --check` (it prints the SHA-256 of your `rkgame`).
