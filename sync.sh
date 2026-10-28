#!/bin/bash
# Synchronise toutes les playlists de playlists.txt (seuls les nouveaux titres sont téléchargés).
cd "$(dirname "$0")" || exit 1

PYTHON="${PYTHON:-python3}"          # ou le python de ton venv : ./venv/bin/python
OUT="$HOME/Music/DJ/MixDownload"
FORMAT="aiff"
LOG="logs/sync_$(date +%F).log"
mkdir -p logs "$OUT"

echo "=== Sync $(date) ===" >> "$LOG"
grep -vE '^\s*(#|$)' playlists.txt | while read -r url; do
    echo "--- $url" >> "$LOG"
    "$PYTHON" mixdownload.py "$url" -o "$OUT" --format "$FORMAT" >> "$LOG" 2>&1 \
        || echo "❌ Échec : $url" >> "$LOG"
    sleep 30   # évite de se faire limiter par SoundCloud
done

# Notification macOS
osascript -e 'display notification "Synchronisation terminée" with title "MixDownload"' 2>/dev/null
find logs -name '*.log' -mtime +30 -delete   # garde 30 jours de logs
