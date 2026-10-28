#!/bin/bash
# Synchronise toutes les playlists de playlists.txt (seuls les nouveaux titres sont téléchargés).
# Réglages modifiables ici ou par variables d'environnement (MIXDOWNLOAD_OUT, MIXDOWNLOAD_FORMAT, PYTHON).
cd "$(dirname "$0")" || exit 1

if [ -n "$PYTHON" ]; then :
elif [ -x venv/bin/python ]; then PYTHON=venv/bin/python   # venv créé par install.sh
else PYTHON=python3
fi
OUT="${MIXDOWNLOAD_OUT:-$HOME/Music/MixDownload}"
FORMAT="${MIXDOWNLOAD_FORMAT:-aiff}"
LOG="logs/sync_$(date +%F).log"
mkdir -p logs "$OUT"

echo "=== Sync $(date) ===" >> "$LOG"
# mixdownload.py lit lui-même playlists.txt et ne télécharge que les nouveautés
if "$PYTHON" mixdownload.py -o "$OUT" --format "$FORMAT" >> "$LOG" 2>&1; then
    MSG="Synchronisation terminée"
else
    MSG="Synchronisation en échec : voir $LOG"
    echo "❌ $MSG" >> "$LOG"
fi

# Notification (macOS / Linux de bureau)
if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"$MSG\" with title \"MixDownload\"" 2>/dev/null
elif command -v notify-send >/dev/null 2>&1; then
    notify-send "MixDownload" "$MSG" 2>/dev/null
fi
find logs -name '*.log' -mtime +30 -delete   # garde 30 jours de logs
