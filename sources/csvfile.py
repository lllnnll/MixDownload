"""
Fichier CSV (export Exportify, TuneMyMusic, Soundiiz, Excel…).

Colonnes reconnues (sans tenir compte des majuscules) :
    titre    : Track Name, title, titre, name, track, song, morceau
    artiste  : Artist Name(s), artist, artists, artiste, artistes
    duree    : Duration (ms)   (facultatif)
Separateur detecte automatiquement : virgule, point-virgule ou tabulation.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .common import SourceError, Track

TITLE_COLS = ("track name", "title", "titre", "name", "track", "song", "morceau", "nom")
ARTIST_COLS = ("artist name(s)", "artist name", "artist", "artists", "artiste", "artistes")
DURATION_COLS = ("duration (ms)", "duration_ms", "track duration (ms)")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252", errors="replace")  # export Excel Windows


def _pick(header: dict, names: tuple) -> str | None:
    return next((header[n] for n in names if n in header), None)


def fetch_csv(entry: str) -> tuple[str, list[Track]]:
    path = Path(entry).expanduser()
    if not path.is_file():
        raise SourceError(f"Fichier CSV introuvable : {path}")
    text = _read_text(path)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = csv.DictReader(text.splitlines(), dialect=dialect)
    header = {(h or "").strip().lower(): h for h in (rows.fieldnames or [])}

    title_col, artist_col = _pick(header, TITLE_COLS), _pick(header, ARTIST_COLS)
    if not title_col:
        raise SourceError(f"CSV : aucune colonne de titre trouvee ({', '.join(header) or 'vide'}). "
                          f"Attendu : Track Name, title ou titre.")
    dur_col = _pick(header, DURATION_COLS)

    tracks = []
    for row in rows:
        title = (row.get(title_col) or "").strip()
        if not title:
            continue
        artist = (row.get(artist_col) or "").strip() if artist_col else ""
        try:
            dur = float(row.get(dur_col) or 0) / 1000 if dur_col else None
        except ValueError:
            dur = None
        tracks.append(Track(artist, title, dur or None))
    return path.stem, tracks
