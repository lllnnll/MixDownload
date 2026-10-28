"""
Spotify : branche spotify_source.fetch_spotify (API avec compte, ou page embed
sans compte) et convertit ses Track vers sources.common.Track.
"""
from __future__ import annotations

from .common import SourceError, Track, http_get


def _title(url: str) -> str:
    """Nom de la playlist via oEmbed (public, sans compte). Sert au nom du dossier."""
    try:
        r = http_get("https://open.spotify.com/oembed", params={"url": url})
        if r.ok and r.json().get("title"):
            return r.json()["title"]
    except (SourceError, ValueError, OSError):
        pass
    return "Spotify"


def fetch_spotify_source(url: str) -> tuple[str, list[Track]]:
    try:
        from spotify_source import SpotifyError, fetch_spotify, parse_url
    except ImportError as e:
        raise SourceError(f"Module manquant : {e.name}. Lance install.sh / install.ps1 "
                          "ou : pip install -r requirements.txt")
    try:
        kind, sid = parse_url(url)
        tracks = fetch_spotify(url)
    except SpotifyError as e:
        raise SourceError(f"Spotify : {e}")
    # Les deux classes Track ont les memes champs ; url reste None (pas de
    # telechargement direct depuis Spotify : on cherche par artiste + titre).
    return (_title(f"https://open.spotify.com/{kind}/{sid}"),
            [Track(t.artist, t.title, t.duration) for t in tracks])
