"""
SoundCloud : lecture du set / titre / profil avec yt-dlp. Chaque morceau garde
son URL et sera telecharge directement, sans recherche.
"""
from __future__ import annotations

import json
import subprocess

from .common import SourceError, Track


def _flatten(info: dict):
    """Un set contient des titres ; une page /sets contient des sets."""
    if not info:
        return
    if info.get("entries") is not None:
        for e in info["entries"]:
            yield from _flatten(e)
    else:
        yield info


def fetch_soundcloud(url: str, ytdlp_path: str = "yt-dlp") -> tuple[str, list[Track]]:
    res = subprocess.run([ytdlp_path, "-J", "--ignore-errors", url],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        info = json.loads(res.stdout)
    except json.JSONDecodeError:
        err = (res.stderr or "").strip().splitlines()
        raise SourceError(f"SoundCloud : lecture impossible ({err[-1] if err else 'erreur inconnue'})")

    tracks = []
    for e in _flatten(info):
        link = e.get("webpage_url") or e.get("url")
        if e.get("title") and link:
            tracks.append(Track((e.get("uploader") or "").strip(), e["title"].strip(),
                                e.get("duration"), link))
    return info.get("title") or "SoundCloud", tracks
