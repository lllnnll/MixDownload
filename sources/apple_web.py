"""
Apple Music via la page web publique (music.apple.com) : fonctionne sur tous
les OS, sans compte. Playlists publiques ou partagees, albums, titres.

La page contient un bloc JSON "serialized-server-data" avec la liste des titres.
Si Apple change son site, cette lecture peut casser : verifie les logs.
"""
from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, urlparse

from .common import SourceError, Track, http_get, log


def _sections(url: str) -> list[dict]:
    r = http_get(url)
    if r.status_code == 404:
        raise SourceError("Page Apple Music introuvable (404) : lien faux, ou playlist "
                          "non partagee publiquement.")
    r.raise_for_status()
    m = re.search(r'<script[^>]*id="serialized-server-data"[^>]*>(.*?)</script>',
                  r.content.decode("utf-8"), re.S)
    if not m:
        raise SourceError("Page Apple Music illisible (structure modifiee ?).")
    try:
        return json.loads(m.group(1))["data"][0]["data"]["sections"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise SourceError("Page Apple Music illisible (structure modifiee ?).")


def fetch_apple_web(url: str) -> tuple[str, list[Track]]:
    """Renvoie (titre de la playlist/album, morceaux)."""
    sections = _sections(url)
    header = next((s["items"][0] for s in sections
                   if s.get("itemKind") == "containerDetailHeaderLockup" and s.get("items")), {})
    items = [it for s in sections if s.get("itemKind") == "trackLockup"
             for it in s.get("items", [])]

    # Lien vers un seul titre d'un album (…/album/xxx/123?i=456) : on ne garde que lui
    song_id = parse_qs(urlparse(url).query).get("i", [None])[0]
    if song_id:
        items = [it for it in items
                 if (it.get("contentDescriptor") or {}).get("identifiers", {})
                 .get("storeAdamID") == song_id] or items

    tracks = []
    for it in items:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        dur = it.get("duration")
        tracks.append(Track((it.get("artistName") or "").strip(), title,
                            dur / 1000 if dur else None))

    expected = header.get("trackCount")
    if not song_id and expected and len(tracks) < expected:
        log(f"⚠️  Apple Music : {len(tracks)} titres lus sur {expected} annonces "
            f"(page web incomplete).")
    return (header.get("title") or "Apple Music").strip(), tracks
