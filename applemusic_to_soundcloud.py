#!/usr/bin/env python3
"""
applemusic_to_soundcloud.py

Lit une playlist depuis l'app Musique (macOS), cherche chaque morceau sur
SoundCloud et le telecharge avec yt-dlp.

Prerequis :
    brew install yt-dlp ffmpeg

Usage :
    python3 applemusic_to_soundcloud.py "Nom de ma playlist"
    python3 applemusic_to_soundcloud.py "Nom" --dry-run          # ne fait que lister les liens trouves
    python3 applemusic_to_soundcloud.py "Nom" -o ~/Music/SC      # dossier de sortie
    python3 applemusic_to_soundcloud.py "Nom" --format wav       # format audio (mp3 par defaut)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

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
        sys.exit(f"Erreur AppleScript : {e.stderr.strip()}")

    raw = result.stdout.strip()
    if raw == "__NOT_FOUND__":
        sys.exit(f'Playlist "{playlist_name}" introuvable dans l\'app Musique.')

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


def find_link(query):
    """Cherche le 1er resultat SoundCloud et renvoie (titre, url) sans telecharger."""
    cmd = [
        "yt-dlp", f"scsearch1:{query}",
        "--skip-download",
        "--print", "%(uploader)s | %(title)s | %(webpage_url)s",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    line = res.stdout.strip()
    return line if line else None


def download(query, outdir, fmt):
    """Cherche sur SoundCloud et telecharge le 1er resultat en audio."""
    cmd = [
        "yt-dlp", f"scsearch1:{query}",
        "-x",                          # extraction audio
        "--audio-format", fmt,
        "--audio-quality", "0",        # meilleure qualite dispo
        "--embed-metadata",
        "--embed-thumbnail",
        "--no-playlist",
        "-o", str(Path(outdir) / "%(title)s.%(ext)s"),
    ]
    res = subprocess.run(cmd)
    return res.returncode == 0


def main():
    p = argparse.ArgumentParser(description="Apple Music playlist -> SoundCloud via yt-dlp")
    p.add_argument("playlist", help="Nom exact de la playlist dans l'app Musique")
    p.add_argument("-o", "--output", default="~/Music/SoundCloud-DL",
                   help="Dossier de sortie (defaut: ~/Music/SoundCloud-DL)")
    p.add_argument("--format", default="mp3", help="Format audio (mp3, wav, flac, m4a...)")
    p.add_argument("--dry-run", action="store_true",
                   help="Liste seulement les liens trouves, sans telecharger")
    args = p.parse_args()

    if shutil.which("yt-dlp") is None:
        sys.exit("yt-dlp introuvable. Installe-le : brew install yt-dlp ffmpeg")

    outdir = Path(args.output).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    tracks = get_playlist_tracks(args.playlist)
    if not tracks:
        sys.exit("Aucun morceau trouve dans cette playlist.")

    print(f"\n{len(tracks)} morceaux dans \"{args.playlist}\"\n")

    ok, fail = 0, 0
    for i, (artist, title) in enumerate(tracks, 1):
        query = f"{artist} {title}".strip()
        print(f"[{i}/{len(tracks)}] {query}")

        if args.dry_run:
            match = find_link(query)
            print(f"    -> {match if match else 'AUCUN resultat SoundCloud'}\n")
            continue

        if download(query, outdir, args.format):
            ok += 1
        else:
            fail += 1
            print(f"    !! echec pour : {query}")
        print()

    if not args.dry_run:
        print(f"\nTermine : {ok} telecharges, {fail} echecs -> {outdir}")


if __name__ == "__main__":
    main()
