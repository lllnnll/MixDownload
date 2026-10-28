"""
Elements partages par toutes les sources : Track, journal, acces HTTP.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Dossier du projet (parent de sources/) : le log est stocke a cote du script
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "mixdownload.log"

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Track:
    """Meme forme que spotify_source.Track.

    url : lien a telecharger directement (SoundCloud). Si None, le morceau est
    cherche par "artiste titre" (logique de recherche habituelle).
    """
    artist: str
    title: str
    duration: float | None = None
    url: str | None = None

    @property
    def query(self) -> str:
        return f"{self.artist} {self.title}".strip()

    @property
    def label(self) -> str:
        return f"{self.artist} - {self.title}" if self.artist else self.title


class SourceError(RuntimeError):
    pass


def log(msg):
    """Affiche et ecrit dans le fichier de log avec horodatage."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def http_get(url, **kwargs):
    """requests.get avec import tardif : les playlists de l'app Musique
    fonctionnent meme avec un Python sans `requests` (ex. /usr/bin/python3)."""
    try:
        import requests
    except ImportError:
        raise SourceError("Module manquant : requests. Lance install.sh / install.ps1 "
                          "ou : pip install -r requirements.txt")
    kwargs.setdefault("headers", UA)
    kwargs.setdefault("timeout", 20)
    return requests.get(url, **kwargs)
