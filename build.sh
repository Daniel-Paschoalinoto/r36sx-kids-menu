#!/bin/sh
# Linux / macOS launcher.  Usage: ./build.sh
cd "$(dirname "$0")" || exit 1
python3 -c "import PIL, numpy, keystone" 2>/dev/null || python3 -m pip install -r requirements.txt || exit 1
python3 build.py "$@"
