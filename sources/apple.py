"""
Apple Music via l'app Musique (macOS uniquement) : lecture d'une playlist par
son nom, avec AppleScript. Code deplace tel quel depuis mixdownload.py.
"""

import shutil
import subprocess
import sys

from .common import log

# --- AppleScript : recupere artiste + titre de chaque morceau d'une playlist ---
APPLESCRIPT = '''
on run argv
    set playlistName to item 1 of argv
    tell application "Music"
        if not (exists playlist playlistName) then
            return "__NOT_FOUND__"
        end if
        set out to ""
        repeat with t in (tracks of playlist playlistName)
            set a to ""
            set n to ""
            try
                set a to artist of t
            end try
            try
                set n to name of t
            end try
            set out to out & a & tab & n & linefeed
        end repeat
        return out
    end tell
end run
'''


def get_playlist_tracks(playlist_name):
    """Renvoie une liste de tuples (artiste, titre) depuis l'app Musique."""
    if shutil.which("osascript") is None:
        sys.exit("osascript introuvable — ce script ne tourne que sur macOS.")
    try:
        result = subprocess.run(
            ["osascript", "-e", APPLESCRIPT, playlist_name],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        log(f"!! Erreur AppleScript pour \"{playlist_name}\" : {e.stderr.strip()}")
        return None

    raw = result.stdout.strip()
    if raw == "__NOT_FOUND__":
        log(f'!! Playlist introuvable dans l\'app Musique : "{playlist_name}"')
        return None

    tracks = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        artist = parts[0].strip() if len(parts) > 0 else ""
        title = parts[1].strip() if len(parts) > 1 else ""
        if title:
            tracks.append((artist, title))
    return tracks
