"""
Deezer via l'API publique (https://api.deezer.com), sans compte.
Playlists publiques, albums et titres. Pagination automatique.
"""
from __future__ import annotations

import re
import time

from .common import SourceError, Track, http_get

API = "https://api.deezer.com"
PAGE = 100   # titres par page (l'API suit ensuite le lien "next")


def _get(url: str) -> dict:
    for attempt in range(1, 4):
        j = http_get(url).json()
        err = j.get("error") if isinstance(j, dict) else None
        if not err:
            return j
        if err.get("code") == 4 and attempt < 3:   # quota depasse : on patiente
            time.sleep(5 * attempt)
            continue
        if err.get("code") == 800:
            raise SourceError("Deezer : introuvable. La playlist est privee ou supprimee "
                              "(seules les playlists publiques sont lisibles).")
        raise SourceError(f"Deezer : {err.get('message') or err}")
    raise SourceError("Deezer : trop de requetes, reessaie plus tard.")


def _to_track(t: dict) -> Track | None:
    if not t or not t.get("title"):
        return None
    dur = t.get("duration")
    return Track(((t.get("artist") or {}).get("name") or "").strip(), t["title"].strip(),
                 float(dur) if dur else None)


def fetch_deezer(url: str) -> tuple[str, list[Track]]:
    """Renvoie (titre, morceaux) pour une URL deezer.com de playlist/album/titre."""
    m = re.search(r"deezer\.com/(?:[a-z]{2}(?:-[a-z]{2})?/)?(playlist|album|track)/(\d+)", url)
    if not m:
        raise SourceError(f"URL Deezer non reconnue : {url}")
    kind, did = m.groups()

    info = _get(f"{API}/{kind}/{did}")
    if kind == "track":
        t = _to_track(info)
        return info.get("title", "Deezer"), [t] if t else []

    tracks: list[Track] = []
    nxt = f"{API}/{kind}/{did}/tracks?limit={PAGE}"
    while nxt:
        j = _get(nxt)
        tracks += [t for t in map(_to_track, j.get("data", [])) if t]
        nxt = j.get("next")
    return info.get("title") or "Deezer", tracks
