"""
spotify_source.py — Lecture des playlists / albums / titres Spotify pour MixDownload.

Deux modes, choisis automatiquement :
  1. API Spotify (connexion à ton compte) : toutes tes playlists, sans limite de taille.
     Nécessite : compte Premium + une app sur developer.spotify.com (voir README).
  2. Page "embed" (sans compte) : n'importe quelle playlist publique, ~100 titres max.

Utilisation seule (pour tester) :
    python spotify_source.py --setup          # enregistre Client ID / Secret
    python spotify_source.py --list           # liste tes playlists
    python spotify_source.py <url_spotify>    # affiche les titres trouvés

Depuis mixdownload.py :
    from spotify_source import fetch_spotify
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "playlist-read-private playlist-read-collaborative"
CONFIG_DIR = Path.home() / ".mixdownload"
CONFIG_FILE = CONFIG_DIR / "spotify.json"
TOKEN_CACHE = CONFIG_DIR / "spotify_token.json"
API = "https://api.spotify.com/v1"
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Track:
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


class SpotifyError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #
def load_credentials() -> tuple[str, str] | None:
    """Variables d'environnement d'abord, puis ~/.mixdownload/spotify.json."""
    cid, secret = os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET")
    if cid and secret:
        return cid, secret
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if data.get("client_id") and data.get("client_secret"):
            return data["client_id"], data["client_secret"]
    return None


def setup() -> None:
    print("Configuration Spotify — voir README, section « Spotify ».")
    print(f"Redirect URI à déclarer dans ton app : {REDIRECT_URI}\n")
    cid = input("Client ID     : ").strip()
    secret = input("Client Secret : ").strip()
    if not cid or not secret:
        sys.exit("Client ID et Secret obligatoires.")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"client_id": cid, "client_secret": secret}, indent=2), encoding="utf-8")
    CONFIG_FILE.chmod(0o600)
    TOKEN_CACHE.unlink(missing_ok=True)
    print(f"\n✅ Enregistré dans {CONFIG_FILE}. Connexion au compte…")
    get_token(force=True)
    print("✅ Connecté. Essaie : python spotify_source.py --list")


# --------------------------------------------------------------------------- #
#  Authentification (OAuth via spotipy)
# --------------------------------------------------------------------------- #
def get_token(force: bool = False) -> str | None:
    """Renvoie un token utilisateur, ou None si non configuré."""
    creds = load_credentials()
    if not creds:
        if force:
            raise SpotifyError("Aucun Client ID/Secret. Lance : python spotify_source.py --setup")
        return None
    try:
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        raise SpotifyError("Module manquant : pip install spotipy")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    auth = SpotifyOAuth(client_id=creds[0], client_secret=creds[1],
                        redirect_uri=REDIRECT_URI, scope=SCOPES,
                        cache_path=str(TOKEN_CACHE), open_browser=True)
    return auth.get_access_token(as_dict=False)


def _get(url: str, token: str) -> dict:
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    if r.status_code == 401:
        raise SpotifyError("Token invalide ou expiré — relance --setup.")
    if r.status_code == 403:
        raise SpotifyError("Accès refusé (403) : compte non Premium, ou ton e-mail n'est pas "
                           "dans « User Management » de l'app.")
    if r.status_code == 404:
        raise SpotifyError("Introuvable (404) : playlist privée d'un autre utilisateur, "
                           "ou non accessible via l'API en mode développement.")
    if r.status_code == 429:
        raise SpotifyError("Trop de requêtes (429) — réessaie dans quelques minutes.")
    r.raise_for_status()
    return r.json()


# --------------------------------------------------------------------------- #
#  Lecture via l'API
# --------------------------------------------------------------------------- #
def _to_track(t: dict) -> Track | None:
    if not t or not t.get("name") or t.get("type") == "episode":
        return None
    artists = ", ".join(a["name"] for a in t.get("artists", []))
    dur = t.get("duration_ms")
    return Track(artists.strip(), t["name"].strip(), dur / 1000 if dur else None)


def _api_fetch(kind: str, sid: str, token: str) -> list[Track]:
    if kind == "track":
        t = _to_track(_get(f"{API}/tracks/{sid}", token))
        return [t] if t else []

    nxt = (f"{API}/playlists/{sid}/items?limit=50" if kind == "playlist"
           else f"{API}/albums/{sid}/tracks?limit=50")
    tracks: list[Track] = []
    while nxt:
        j = _get(nxt, token)
        for it in j.get("items", []):
            # nouveau format (item), ancien format (track), album (objet direct)
            raw = it.get("item") or it.get("track") or it
            t = _to_track(raw)
            if t:
                tracks.append(t)
        nxt = j.get("next")
    return tracks


def list_my_playlists() -> list[tuple[str, int | None, str]]:
    token = get_token(force=True)
    out, nxt = [], f"{API}/me/playlists?limit=50"
    while nxt:
        j = _get(nxt, token)
        for p in j.get("items", []):
            if not p:
                continue
            total = (p.get("items") or p.get("tracks") or {}).get("total")
            out.append((p["name"], total, f"https://open.spotify.com/playlist/{p['id']}"))
        nxt = j.get("next")
    return out


# --------------------------------------------------------------------------- #
#  Lecture via la page embed (sans compte)
# --------------------------------------------------------------------------- #
def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _embed_fetch(kind: str, sid: str) -> list[Track]:
    html = requests.get(f"https://open.spotify.com/embed/{kind}/{sid}", headers=UA, timeout=20).text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise SpotifyError("Page embed Spotify illisible (structure modifiée ?).")
    data = json.loads(m.group(1))

    entity = next((d for d in _walk(data) if "trackList" in d or d.get("type") == "track"), None)
    if not entity:
        raise SpotifyError("Aucun titre trouvé dans la page embed (playlist privée ?).")

    if kind == "track":
        artists = ", ".join(a["name"] for a in entity.get("artists", []))
        dur = entity.get("duration")
        return [Track(artists, entity["name"], dur / 1000 if dur else None)]

    tracks = []
    for t in entity.get("trackList", []):
        dur = t.get("duration")
        tracks.append(Track(t.get("subtitle", "").replace("\u00a0", " ").strip(),
                            t.get("title", "").strip(), dur / 1000 if dur else None))
    if len(tracks) >= 100:
        print("⚠️  Mode sans compte limité à ~100 titres. Pour tout récupérer : "
              "connecte ton compte (--setup) ou utilise un export CSV.")
    return tracks


# --------------------------------------------------------------------------- #
#  Point d'entrée
# --------------------------------------------------------------------------- #
def parse_url(url: str) -> tuple[str, str]:
    if "spotify.link" in url:
        url = requests.get(url, headers=UA, timeout=20, allow_redirects=True).url
    m = re.search(r"(playlist|album|track)[/:]([A-Za-z0-9]{22})", url)
    if not m:
        raise SpotifyError(f"URL Spotify non reconnue : {url}")
    return m.group(1), m.group(2)


def fetch_spotify(url: str) -> list[Track]:
    kind, sid = parse_url(url)
    try:
        token = get_token()
    except SpotifyError as e:
        print(f"⚠️  {e}")
        token = None

    if token:
        try:
            tracks = _api_fetch(kind, sid, token)
            print(f"Spotify (API) : {len(tracks)} titres.")
            return tracks
        except SpotifyError as e:
            print(f"⚠️  API : {e}\n   → repli sur le mode sans compte.")

    tracks = _embed_fetch(kind, sid)
    print(f"Spotify (sans compte) : {len(tracks)} titres.")
    return tracks


def main():
    # Emojis : evite les plantages d'encodage dans la console Windows
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Source Spotify de MixDownload")
    p.add_argument("url", nargs="?", help="URL de playlist, album ou titre Spotify")
    p.add_argument("--setup", action="store_true", help="configurer Client ID / Secret")
    p.add_argument("--list", action="store_true", help="lister tes playlists")
    p.add_argument("--logout", action="store_true", help="supprimer la connexion enregistrée")
    a = p.parse_args()

    try:
        if a.setup:
            setup()
        elif a.logout:
            TOKEN_CACHE.unlink(missing_ok=True)
            print("Déconnecté.")
        elif a.list:
            for name, total, link in list_my_playlists():
                print(f"{name[:40]:40} {str(total or '?'):>5} titres  {link}")
        elif a.url:
            for i, t in enumerate(fetch_spotify(a.url), 1):
                print(f"{i:3}. {t.label}")
        else:
            p.print_help()
    except SpotifyError as e:
        sys.exit(f"❌ {e}")


if __name__ == "__main__":
    main()
