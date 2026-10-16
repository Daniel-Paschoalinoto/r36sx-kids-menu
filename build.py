"""Entry point:  python build.py   (see README).  /  Ponto de entrada: python build.py   (veja o README)."""
import sys

if sys.version_info < (3, 11):
    sys.exit("Python 3.11 or newer is required / É preciso Python 3.11 ou mais novo: https://www.python.org/downloads/")

try:
    from r36skit.build import main
except ImportError as exc:  # missing Pillow / numpy / keystone
    sys.exit("Missing a package / Falta um pacote (%s).\nRun / Rode:  python -m pip install -r requirements.txt" % exc)

if __name__ == "__main__":
    sys.exit(main())
