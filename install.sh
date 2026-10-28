#!/bin/bash
# Installation de l'automatisation MixDownload (macOS).
# - verifie/installe yt-dlp + ffmpeg via Homebrew
# - installe et active la tache quotidienne (launchd) a 18h00
#
# Usage :  bash install.sh

set -e

DIR="/Users/nikita/Claude/Projects/MixDownload"
PLIST="com.nikita.mixdownload.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST"

echo "==> Verification des dependances (yt-dlp, ffmpeg)..."
if ! command -v brew >/dev/null 2>&1; then
    echo "!! Homebrew n'est pas installe. Installe-le depuis https://brew.sh puis relance."
    exit 1
fi

command -v yt-dlp >/dev/null 2>&1 || { echo "   installation de yt-dlp..."; brew install yt-dlp; }
command -v ffmpeg >/dev/null 2>&1 || { echo "   installation de ffmpeg..."; brew install ffmpeg; }

echo "==> yt-dlp : $(command -v yt-dlp)  ($(yt-dlp --version 2>/dev/null))"
echo "==> ffmpeg : $(command -v ffmpeg)"

echo "==> Installation de la tache quotidienne (launchd)..."
mkdir -p "$HOME/Library/LaunchAgents"
cp "$DIR/$PLIST" "$DEST"

# Recharge proprement si deja chargee
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo ""
echo "OK. La tache tournera chaque jour a 18h00."
echo ""
echo "Prochaines etapes :"
echo "  1. Ajoute tes playlists dans : $DIR/playlists.txt"
echo "  2. (1ere fois) recupere tout l'existant :   python3 $DIR/mixdownload.py --download-all"
echo "     ou laisse le script ne prendre que les NOUVEAUX ajouts a partir de maintenant."
echo "  3. Test a blanc :   python3 $DIR/mixdownload.py --dry-run"
echo ""
echo "Pour desactiver plus tard :   launchctl unload \"$DEST\""
