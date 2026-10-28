#!/usr/bin/env python3
"""
mixdownload.py

Verifie chaque jour une liste de playlists (Apple Music, Spotify, Deezer,
SoundCloud ou fichier CSV). Pour chaque nouveau morceau ajoute depuis la
derniere verification, il le cherche sur SoundCloud (ou le prend directement
pour une playlist SoundCloud) et le telecharge avec yt-dlp, dans la meilleure
qualite possible, converti en WAV (ideal pour rekordbox), avec plusieurs
tentatives en cas d'echec.

La lecture des playlists est dans sources/ (un module par plateforme).

Prerequis : yt-dlp et ffmpeg (voir README.md, install.sh / install.ps1)

Configuration :
    - playlists.txt : une playlist par ligne (URL, fichier .csv, ou nom dans l'app Musique sur macOS)
    - config.json   : options (dossier de sortie, format, retries...) - genere au 1er lancement

Usage :
    python3 mixdownload.py                 # verification normale (telecharge les nouveautes)
    python3 mixdownload.py <url|fichier.csv> [-o DOSSIER] [--format aiff]
                                           # une playlist precise : tout au 1er passage, puis nouveautes
    python3 mixdownload.py --dry-run       # liste seulement ce qui serait telecharge
    python3 mixdownload.py --download-all   # ignore l'etat : (re)telecharge TOUT le contenu actuel
    python3 mixdownload.py --playlist "Nom" # force une seule playlist (sinon lit playlists.txt)

Comment fonctionne le suivi des "nouveautes" :
    Au tout premier passage sur une playlist, le script enregistre simplement
    une "baseline" (la liste des morceaux deja presents) SANS rien telecharger,
    pour eviter de tout aspirer d'un coup. Les passages suivants ne telechargent
    que les morceaux ajoutes apres cette baseline.
    -> Utilise --download-all une fois si tu veux recuperer tout l'existant.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from sources import fetch_tracks
from sources.apple import get_playlist_tracks  # noqa: F401  (compatibilite : import mixdownload)
from sources.common import LOG_FILE, log  # noqa: F401

# Repertoire du script (tout est stocke a cote)
BASE_DIR = Path(__file__).resolve().parent
PLAYLISTS_FILE = BASE_DIR / "playlists.txt"
CONFIG_FILE = BASE_DIR / "config.json"
STATE_FILE = BASE_DIR / "state.json"

DEFAULT_CONFIG = {
    "output_dir": str(BASE_DIR / "downloads"),
    "audio_format": "wav",      # wav, aiff, flac, mp3...
    "subfolder_per_playlist": True,
    "max_retries": 4,           # nombre de tentatives par morceau
    "retry_delay_sec": 5,       # attente entre les tentatives (augmente a chaque essai)
    "search_results": 3,        # combien de resultats SoundCloud essayer (scsearchN)
    "ytdlp_path": "yt-dlp",     # chemin vers le binaire yt-dlp (ex: "/opt/homebrew/bin/yt-dlp-nightly")
    "youtube_player_clients": "ios,web,mweb",  # clients YouTube a essayer (contourne le 403 android_vr)
    "youtube_cookies_browser": "arc",          # navigateur pour --cookies-from-browser ("" pour desactiver)
}


# ----------------------------- utilitaires ----------------------------------

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log(f"!! Fichier illisible, valeur par defaut utilisee : {path.name}")
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(load_json(CONFIG_FILE, {}))
    if not CONFIG_FILE.exists():
        save_json(CONFIG_FILE, cfg)  # genere un config.json editable au 1er lancement
    return cfg


def load_playlists():
    if not PLAYLISTS_FILE.exists():
        # cree un modele pour que l'utilisateur le remplisse
        PLAYLISTS_FILE.write_text(
            "# Une playlist par ligne. Les lignes vides et celles commencant par # sont ignorees.\n"
            "# Accepte : URL Apple Music, Spotify, Deezer, SoundCloud, chemin d'un fichier .csv,\n"
            "# ou (macOS) le nom EXACT d'une playlist de l'app Musique.\n"
            "# Exemples :\n"
            "# https://open.spotify.com/playlist/XXXXXXXXXXXXXXXXXXXXXX\n"
            "# https://www.deezer.com/fr/playlist/1234567890\n"
            "# https://music.apple.com/fr/playlist/ma-playlist/pl.xxxxxxxx\n"
            "# https://soundcloud.com/utilisateur/sets/ma-playlist\n"
            "# Diggin 2026\n",
            encoding="utf-8",
        )
        return []
    names = []
    for line in PLAYLISTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.append(line)
    return names


# ------------------------------ suivi ---------------------------------------

def track_key(artist, title):
    """Identifiant stable d'un morceau pour le suivi d'etat."""
    return f"{artist.lower().strip()}|{title.lower().strip()}"


# ------------------------------ yt-dlp --------------------------------------

def _try_download(search_prefix, n, query, outdir, fmt, ytdlp_path="yt-dlp", extra_args=None):
    """Un seul essai yt-dlp sur une source donnee (scsearch / ytsearch)."""
    cmd = [
        ytdlp_path, f"{search_prefix}{n}:{query}",
        "-x",                          # extraction audio
        "--audio-format", fmt,         # conversion (wav pour rekordbox)
        "--audio-quality", "0",        # meilleure qualite dispo
        "--embed-metadata",
        "--no-playlist",
        "--no-overwrites",             # ne re-telecharge pas un fichier existant
        "--download-archive", str(outdir / ".yt-dlp-archive.txt"),
        "--retries", "10",             # retries reseau internes yt-dlp
        "--fragment-retries", "10",
        "--playlist-items", "1",       # garde 1 seul resultat meme si searchN
        "-o", str(outdir / "%(uploader)s - %(title)s.%(ext)s"),
    ]
    # La pochette ne s'integre pas dans un WAV ; on ne l'integre que pour
    # les formats qui la supportent.
    if fmt in ("mp3", "m4a", "aiff", "flac"):
        cmd.insert(-2, "--embed-thumbnail")

    if extra_args:
        cmd.extend(extra_args)

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        return True, None
    err = (res.stderr or "").strip().splitlines()
    return False, (err[-1] if err else "erreur inconnue")


def download(query, outdir, fmt, search_results, max_retries, retry_delay,
             ytdlp_path="yt-dlp", youtube_player_clients="ios,web,mweb",
             youtube_cookies_browser=""):
    """
    Cherche le morceau et le telecharge en audio (meilleure qualite dispo).
    D'abord sur SoundCloud, avec plusieurs tentatives ; si tout echoue, bascule
    sur YouTube (meme logique de tentatives). Renvoie True si succes.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # (nom lisible, prefixe de recherche yt-dlp, args supplementaires)
    yt_extra = []
    if youtube_player_clients:
        yt_extra += ["--extractor-args", f"youtube:player_client={youtube_player_clients}"]
    if youtube_cookies_browser:
        yt_extra += ["--cookies-from-browser", youtube_cookies_browser]

    sources = [("SoundCloud", "scsearch", []), ("YouTube", "ytsearch", yt_extra)]

    for label, prefix, extra in sources:
        for attempt in range(1, max_retries + 1):
            # 1ere tentative : searchN=1 (resultat le plus pertinent).
            # tentatives suivantes : on elargit pour contourner lien mort / privé.
            n = 1 if attempt == 1 else max(search_results, 1)
            ok, tail = _try_download(prefix, n, query, outdir, fmt,
                                     ytdlp_path=ytdlp_path, extra_args=extra)
            if ok:
                if label != "SoundCloud":
                    log(f"    -> trouve sur {label}")
                return True
            log(f"    {label} tentative {attempt}/{max_retries} echouee : {tail}")
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)  # backoff progressif
        log(f"    {label} : echec, bascule vers la source suivante..."
            if label != sources[-1][0] else f"    {label} : echec.")

    return False


def download_direct(url, outdir, fmt, max_retries, retry_delay, ytdlp_path="yt-dlp"):
    """
    Telecharge directement une URL (titre SoundCloud), sans recherche.
    Memes options yt-dlp que _try_download. Renvoie True si succes.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        ytdlp_path, url,
        "-x",
        "--audio-format", fmt,
        "--audio-quality", "0",
        "--embed-metadata",
        "--no-playlist",
        "--no-overwrites",
        "--download-archive", str(outdir / ".yt-dlp-archive.txt"),
        "--retries", "10",
        "--fragment-retries", "10",
        "-o", str(outdir / "%(uploader)s - %(title)s.%(ext)s"),
    ]
    if fmt in ("mp3", "m4a", "aiff", "flac"):
        cmd.insert(-2, "--embed-thumbnail")

    for attempt in range(1, max_retries + 1):
        res = subprocess.run(cmd, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        if res.returncode == 0:
            return True
        err = (res.stderr or "").strip().splitlines()
        log(f"    SoundCloud tentative {attempt}/{max_retries} echouee : "
            f"{err[-1] if err else 'erreur inconnue'}")
        if attempt < max_retries:
            time.sleep(retry_delay * attempt)
    return False


# ------------------------------- main ---------------------------------------

def process_playlist(entry, cfg, state, args, explicit=False):
    """
    entry : nom de playlist de l'app Musique, URL ou fichier .csv (cle de state.json).
    explicit : entree passee en argument -> au 1er passage on telecharge tout
               (au lieu d'enregistrer une baseline).
    """
    fetched = fetch_tracks(entry, cfg.get("ytdlp_path", "yt-dlp"))
    if fetched is None:
        return 0, 0, 0
    name, tracks = fetched
    if not tracks:
        log(f'"{name}" : 0 morceau.')
        return 0, 0, 0

    current_keys = [track_key(t.artist, t.title) for t in tracks]
    seen = set(state.get(entry, {}).get("seen", []))
    first_time = entry not in state

    # Determine quoi telecharger
    if args.download_all or (first_time and explicit):
        to_get = list(zip(current_keys, tracks))
    elif first_time:
        # baseline : on memorise sans rien telecharger
        state[entry] = {"seen": current_keys, "updated": datetime.now().isoformat()}
        log(f'"{name}" : baseline enregistree ({len(tracks)} morceaux), aucun telechargement '
            f'(utilise --download-all pour tout recuperer).')
        return 0, 0, 0
    else:
        to_get = [(k, tr) for k, tr in zip(current_keys, tracks) if k not in seen]

    if not to_get:
        log(f'"{name}" : aucune nouveaute.')
        # rien a faire mais on rafraichit l'etat au cas ou
        state[entry] = {"seen": sorted(seen | set(current_keys)),
                        "updated": datetime.now().isoformat()}
        return 0, 0, 0

    log(f'"{name}" : {len(to_get)} nouveau(x) morceau(x).')

    if args.dry_run:
        for key, t in to_get:
            log(f'  -> (dry-run) {t.url or t.query}')
        return 0, 0, len(to_get)

    if cfg["subfolder_per_playlist"]:
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()
        outdir = Path(cfg["output_dir"]).expanduser() / safe
    else:
        outdir = Path(cfg["output_dir"]).expanduser()

    ok = fail = 0
    succeeded = set()
    for key, t in to_get:
        query = t.query
        log(f'  -> {query}')
        if t.url:
            done = download_direct(t.url, outdir, cfg["audio_format"], cfg["max_retries"],
                                   cfg["retry_delay_sec"], ytdlp_path=cfg.get("ytdlp_path", "yt-dlp"))
        else:
            done = download(query, outdir, cfg["audio_format"], cfg["search_results"],
                            cfg["max_retries"], cfg["retry_delay_sec"],
                            ytdlp_path=cfg.get("ytdlp_path", "yt-dlp"),
                            youtube_player_clients=cfg.get("youtube_player_clients", "ios,web,mweb"),
                            youtube_cookies_browser=cfg.get("youtube_cookies_browser", ""))
        if done:
            ok += 1
            succeeded.add(key)
            log(f'     OK')
        else:
            fail += 1
            log(f'     !! ECHEC apres {cfg["max_retries"]} tentatives : {query}')

    # "seen" = ce qui etait deja vu + les morceaux reussis aujourd'hui.
    # Les echecs ne sont PAS marques -> ils seront retentes au prochain passage.
    new_seen = seen | succeeded
    state[entry] = {"seen": sorted(new_seen),
                    "updated": datetime.now().isoformat()}
    return ok, fail, len(to_get)


def get_ytdlp_version(ytdlp_path):
    try:
        r = subprocess.run([ytdlp_path, "--version"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "inconnue"
    except (OSError, subprocess.TimeoutExpired):
        return "introuvable"


def main():
    p = argparse.ArgumentParser(
        description="Playlists (Apple Music, Spotify, Deezer, SoundCloud, CSV) -> SoundCloud (yt-dlp)")
    p.add_argument("sources", nargs="*", metavar="SOURCE",
                   help="URL de playlist/album/titre, fichier .csv ou nom de playlist de l'app "
                        "Musique (macOS). 1er passage : tout est telecharge, ensuite les "
                        "nouveautes. Sans SOURCE : lit playlists.txt")
    p.add_argument("-o", "--output", help="Dossier de sortie (remplace output_dir de config.json)")
    p.add_argument("--format", help="Format audio : wav, aiff, flac, mp3... "
                                    "(remplace audio_format de config.json)")
    p.add_argument("--dry-run", action="store_true",
                   help="Liste les nouveautes sans rien telecharger")
    p.add_argument("--download-all", action="store_true",
                   help="Ignore l'etat et (re)telecharge tout le contenu actuel des playlists")
    p.add_argument("--playlist", help="Force une seule playlist (sinon lit playlists.txt)")
    args = p.parse_args()

    cfg = load_config()
    if args.output:
        cfg["output_dir"] = args.output
    if args.format:
        cfg["audio_format"] = args.format.lower().lstrip(".")
    ytdlp_path = cfg.get("ytdlp_path", "yt-dlp")

    if not (Path(ytdlp_path).is_file() or shutil.which(ytdlp_path)):
        sys.exit(f"yt-dlp introuvable : {ytdlp_path}. Installe-le : brew install yt-dlp ffmpeg")

    # (entree, explicite) : les SOURCE en argument telechargent tout au 1er passage
    if args.sources or args.playlist:
        playlists = [(s, True) for s in args.sources]
        if args.playlist:
            playlists.append((args.playlist, False))
    else:
        playlists = [(s, False) for s in load_playlists()]

    if not playlists:
        sys.exit(f"Aucune playlist. Ajoute des URL ou des noms dans : {PLAYLISTS_FILE}\n"
                 f"ou passe une URL : python mixdownload.py <url>")

    state = load_json(STATE_FILE, {})

    ytdlp_version = get_ytdlp_version(ytdlp_path)
    log("=" * 60)
    log(f"yt-dlp : {ytdlp_path} (version {ytdlp_version})")
    log(f"Demarrage : {len(playlists)} playlist(s) | format={cfg['audio_format']} "
        f"| sortie={cfg['output_dir']}"
        + (" | DRY-RUN" if args.dry_run else "")
        + (" | DOWNLOAD-ALL" if args.download_all else ""))

    total_ok = total_fail = total_new = 0
    for entry, explicit in playlists:
        ok, fail, new = process_playlist(entry, cfg, state, args, explicit)
        total_ok += ok
        total_fail += fail
        total_new += new
        if not args.dry_run:
            save_json(STATE_FILE, state)  # sauvegarde apres chaque playlist

    log(f"Termine : {total_new} nouveaute(s) | {total_ok} telecharge(s) | {total_fail} echec(s)")
    log("=" * 60)


if __name__ == "__main__":
    main()
