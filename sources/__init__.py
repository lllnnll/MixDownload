"""
Sources de playlists de MixDownload.

Une "entree" (ligne de playlists.txt ou argument) peut etre :
    - un nom de playlist de l'app Musique (macOS)  -> sources/apple.py
    - une URL music.apple.com                       -> sources/apple_web.py
    - une URL Spotify (ou spotify.link)             -> sources/spotify.py
    - une URL Deezer (ou link.deezer.com)           -> sources/deezer.py
    - une URL SoundCloud (ou on.soundcloud.com)     -> sources/soundcloud.py
    - un chemin de fichier .csv                     -> sources/csvfile.py
"""
from __future__ import annotations

import re
import sys
from urllib.parse import urlparse

from .common import SourceError, Track, http_get, log

SHORT_HOSTS = ("spotify.link", "link.deezer.com", "deezer.page.link", "on.soundcloud.com")
_LONG_URL = re.compile(r"https://(?:www\.)?(?:open\.spotify\.com|deezer\.com|soundcloud\.com)"
                       r"/[^\s\"'<>\\]+")

PLATFORM_NAMES = {
    "apple_app": "Apple Music (app Musique)", "apple_web": "Apple Music",
    "spotify": "Spotify", "deezer": "Deezer", "soundcloud": "SoundCloud", "csv": "CSV",
}


def _host(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def detect(entry: str) -> str:
    """Devine la plateforme d'une entree (voir docstring du module)."""
    e = entry.strip()
    if e.lower().endswith(".csv"):
        return "csv"
    if e.lower().startswith("spotify:"):
        return "spotify"
    if not re.match(r"https?://", e, re.I):
        return "apple_app"
    host = _host(e)
    if host == "spotify.link" or host.endswith("spotify.com"):
        return "spotify"
    if "deezer" in host:
        return "deezer"
    if host.endswith("soundcloud.com") or host == "snd.sc":
        return "soundcloud"
    if host in ("music.apple.com", "itunes.apple.com", "geo.music.apple.com"):
        return "apple_web"
    raise SourceError(f"Plateforme non reconnue : {e}")


def resolve_short_link(url: str) -> str:
    """Suit un lien court (spotify.link, link.deezer.com, on.soundcloud.com)."""
    if _host(url) not in SHORT_HOSTS:
        return url
    r = http_get(url, allow_redirects=True)
    if _host(r.url) not in SHORT_HOSTS:
        return r.url
    # Certains liens courts renvoient une page qui redirige en JavaScript
    m = _LONG_URL.search(r.text)
    if not m:
        raise SourceError(f"Lien court impossible a resoudre : {url}")
    return m.group(0)


def fetch_tracks(entry: str, ytdlp_path: str = "yt-dlp") -> tuple[str, list[Track]] | None:
    """Renvoie (nom affiche, morceaux), ou None si la source est illisible
    (l'erreur est journalisee et on passe a la playlist suivante)."""
    try:
        kind = detect(entry)
        if kind == "apple_app":
            if sys.platform != "darwin":
                log(f'!! "{entry}" n\'est pas une URL : la lecture par nom de playlist '
                    f'(app Musique) ne marche que sur macOS. Utilise le lien '
                    f'music.apple.com de la playlist (Partager > Copier le lien).')
                return None
            from .apple import get_playlist_tracks
            tracks = get_playlist_tracks(entry)
            if tracks is None:
                return None
            return entry, [Track(a, t) for a, t in tracks]

        if kind == "csv":
            from .csvfile import fetch_csv
            return fetch_csv(entry)

        url = resolve_short_link(entry.strip())
        if kind == "spotify":
            from .spotify import fetch_spotify_source
            return fetch_spotify_source(url)
        if kind == "deezer":
            from .deezer import fetch_deezer
            return fetch_deezer(url)
        if kind == "soundcloud":
            from .soundcloud import fetch_soundcloud
            return fetch_soundcloud(url, ytdlp_path)
        from .apple_web import fetch_apple_web
        return fetch_apple_web(url)
    except SourceError as e:
        log(f"!! {e}")
    except (OSError, ValueError) as e:  # reseau (requests), fichier, JSON invalide
        log(f"!! Erreur de lecture pour \"{entry}\" : {e}")
    return None
