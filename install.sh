#!/usr/bin/env bash
# Installation de MixDownload (macOS / Linux) :
#   - cree un environnement virtuel Python (venv/)
#   - installe les dependances (requirements.txt : yt-dlp, requests, spotipy)
#   - verifie ffmpeg
#
# Usage :  bash install.sh

set -e
cd "$(dirname "$0")"

# --- Python 3.9+ ---
PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
        PY="$c"; break
    fi
done
if [ -z "$PY" ]; then
    echo "!! Python 3.9 ou plus recent introuvable."
    if [ "$(uname -s)" = "Darwin" ]; then
        echo "   Installe-le :  brew install python   (ou https://www.python.org/downloads/)"
    else
        echo "   Installe-le :  sudo apt install python3 python3-venv   (ou dnf / pacman)"
    fi
    exit 1
fi

echo "==> Creation de l'environnement virtuel (venv/) avec $("$PY" --version)"
if ! "$PY" -m venv venv; then
    echo "!! Echec de creation du venv. Sous Debian/Ubuntu : sudo apt install python3-venv"
    exit 1
fi

echo "==> Installation des dependances (requirements.txt)..."
venv/bin/python -m pip install --quiet --upgrade pip
venv/bin/python -m pip install --quiet --upgrade -r requirements.txt
echo "    yt-dlp $(venv/bin/yt-dlp --version)"

# --- ffmpeg (conversion audio) ---
if command -v ffmpeg >/dev/null 2>&1; then
    echo "==> ffmpeg : $(command -v ffmpeg)"
    FFMPEG_OK=1
else
    FFMPEG_OK=0
    if [ "$(uname -s)" = "Darwin" ]; then
        HINT="brew install ffmpeg   (Homebrew : https://brew.sh)"
    elif command -v apt-get >/dev/null 2>&1; then HINT="sudo apt install ffmpeg"
    elif command -v dnf >/dev/null 2>&1;     then HINT="sudo dnf install ffmpeg"
    elif command -v pacman >/dev/null 2>&1;  then HINT="sudo pacman -S ffmpeg"
    else HINT="installe ffmpeg avec le gestionnaire de paquets de ta distribution"
    fi
    echo "!! ffmpeg introuvable (indispensable pour convertir l'audio). Installe-le :"
    echo "   $HINT"
fi

echo ""
echo "Installation terminee."
echo ""
echo "Prochaines etapes :"
echo "  1. Test a blanc :   venv/bin/python mixdownload.py \"<url de playlist>\" --dry-run"
echo "  2. Telechargement : venv/bin/python mixdownload.py \"<url de playlist>\""
echo "  3. Sync quotidienne : ajoute tes URL dans playlists.txt, puis voir README_SYNC.md"
[ "$FFMPEG_OK" = 1 ] || { echo ""; echo "(N'oublie pas d'installer ffmpeg avant de telecharger.)"; }
