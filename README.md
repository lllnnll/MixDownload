# MixDownload

MixDownload récupère les titres d'une playlist (**Apple Music, Spotify, Deezer, SoundCloud** ou **fichier CSV**). Il cherche ensuite chaque titre sur SoundCloud et le télécharge avec **yt-dlp**, dans la meilleure qualité disponible. Le format par défaut est WAV, idéal pour l'analyse dans Rekordbox.

- **Plusieurs tentatives** par titre. Si SoundCloud échoue, le script **bascule automatiquement sur YouTube**.
- **Playlist SoundCloud** : chaque titre est téléchargé directement depuis son lien, sans recherche.
- **Nouveautés seulement** : le script retient ce qui a déjà été traité et ne prend ensuite que les ajouts. Une synchronisation quotidienne est possible ([README_SYNC.md](README_SYNC.md)).
- Fonctionne sur **macOS, Windows et Linux**.

> Aucun fichier audio n'est récupéré depuis Spotify, Deezer ou Apple Music. Seule la liste des titres est lue.

## Installation

Il faut **Python 3.9+** et **ffmpeg**. yt-dlp, requests et spotipy sont installés dans un environnement virtuel (`venv/`) par le script d'installation.

### macOS

```bash
brew install python ffmpeg        # Homebrew : https://brew.sh
bash install.sh
```

### Linux

```bash
sudo apt install python3 python3-venv ffmpeg     # Debian/Ubuntu (ou dnf / pacman)
bash install.sh
```

### Windows

Ouvre **PowerShell** :

```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```

Ferme et rouvre PowerShell, puis, dans le dossier MixDownload :

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

> Si `python` ouvre le Microsoft Store : **Paramètres → Applications → Paramètres avancés des applications → Alias d'exécution d'application**, puis désactive « python.exe » et « python3.exe ».

Au démarrage, `mixdownload.py` vérifie que yt-dlp et ffmpeg sont présents. S'il en manque un, il affiche la commande d'installation adaptée à ton système.

## Utilisation

Dans les exemples ci-dessous, `python` désigne le Python du venv :

| Système | Commande |
|---|---|
| macOS / Linux | `venv/bin/python` |
| Windows | `.\venv\Scripts\python.exe` |

Tu peux aussi activer le venv (`source venv/bin/activate` ou `.\venv\Scripts\Activate.ps1`) puis taper simplement `python`.

```bash
python mixdownload.py "<URL ou fichier.csv>" --dry-run     # vérifie ce qui serait téléchargé
python mixdownload.py "<URL ou fichier.csv>"               # télécharge
python mixdownload.py "<URL>" -o ~/Music/DJ --format aiff  # dossier et format au choix
```

Quand une URL ou un CSV est passé en argument, le **premier passage télécharge toute la playlist**. Les passages suivants ne prennent que les **nouveautés**.

La plateforme est détectée automatiquement à partir de l'URL. Les liens courts sont aussi acceptés : `spotify.link`, `link.deezer.com`, `on.soundcloud.com`.

| Plateforme | Exemple d'entrée | Remarques |
|---|---|---|
| **Spotify** | `https://open.spotify.com/playlist/…` (ou `/album/`, `/track/`) | Sans compte : playlists publiques, **≈ 100 titres max**. Avec compte : voir [README_SPOTIFY.md](README_SPOTIFY.md). |
| **Deezer** | `https://www.deezer.com/fr/playlist/…` (ou `/album/`, `/track/`) | API publique, toutes les pages sont lues. **Playlists publiques seulement.** |
| **Apple Music** (lien) | `https://music.apple.com/fr/playlist/…/pl.…` (ou album, titre) | Lu depuis la **page web** publique. Pour ta playlist : *Partager → Copier le lien*. |
| **Apple Music** (app, macOS) | `"Diggin 2026"` | Nom **exact** d'une playlist de l'app Musique. macOS uniquement, playlists privées incluses. |
| **SoundCloud** | `https://soundcloud.com/artiste/sets/…` (ou un titre, ou un profil) | Téléchargement direct de chaque titre, sans recherche. |
| **CSV** | `ma_playlist.csv` | Colonnes reconnues : `Track Name`/`title`/`titre`, `Artist Name(s)`/`artist`/`artiste`, `Duration (ms)` (facultative). Séparateur `,` `;` ou tabulation. |

Le CSV dépanne pour les longues playlists Spotify dont tu n'es pas propriétaire. Exporte-les avec Exportify, TuneMyMusic ou Soundiiz.

### Plusieurs playlists : `playlists.txt`

Mets une entrée par ligne (URL, fichier .csv ou nom de playlist de l'app Musique). Modèle : [playlists.example.txt](playlists.example.txt). Lance ensuite simplement :

```bash
python mixdownload.py                 # vérifie toutes les playlists, télécharge les nouveautés
python mixdownload.py --dry-run       # liste seulement ce qui serait téléchargé
python mixdownload.py --download-all  # (re)télécharge tout le contenu actuel
python mixdownload.py --playlist "Nom"   # une seule entrée, avec la même logique que playlists.txt
```

Pour une playlist de `playlists.txt`, le **premier passage enregistre une « baseline »** sans rien télécharger, pour ne pas tout aspirer d'un coup. Seuls les ajouts suivants sont téléchargés. Pour récupérer l'existant, lance une fois `--download-all`, ou `python mixdownload.py "<URL>"`.

Pour l'automatiser chaque jour (launchd, Planificateur de tâches Windows, cron) : **[README_SYNC.md](README_SYNC.md)**.

## Réglages (`config.json`)

`config.json` est créé au premier lancement à côté du script. Les options `-o` et `--format` le remplacent le temps d'une commande.

| Clé | Défaut | Rôle |
|---|---|---|
| `output_dir` | `~/Music/MixDownload` | Dossier de sortie |
| `audio_format` | `wav` | `wav`, `aiff`, `flac`, `mp3`, `m4a`… (AIFF et WAV conviennent à Rekordbox) |
| `subfolder_per_playlist` | `true` | Un sous-dossier par playlist |
| `max_retries` | `4` | Tentatives par titre (avec délai croissant) |
| `retry_delay_sec` | `5` | Délai de base entre deux tentatives |
| `search_results` | `3` | Nombre de résultats SoundCloud essayés après le 1er échec |
| `ytdlp_path` | `yt-dlp` | Chemin de yt-dlp. Celui du venv est trouvé automatiquement. |
| `youtube_player_clients` | `ios,web,mweb` | Clients YouTube utilisés pour le repli |
| `youtube_cookies_browser` | `""` | Ex. `"chrome"` : utilise les cookies du navigateur si YouTube bloque (403) |

## Fichiers générés

| Fichier | Contenu |
|---|---|
| `state.json` | Titres déjà traités, par playlist. Les **échecs ne sont pas mémorisés** : ils sont réessayés au passage suivant. |
| `mixdownload.log` | Journal détaillé de chaque exécution |
| `logs/` | Journaux de la synchronisation (`sync.sh` / `sync.ps1`) |
| `.yt-dlp-archive.txt` | Dans chaque dossier de sortie : évite de retélécharger un même fichier |

Tous ces fichiers sont ignorés par git (voir `.gitignore`). C'est aussi le cas des clés Spotify, rangées dans `~/.mixdownload/`.

## Limites

- **Spotify sans compte** : environ 100 titres et playlists publiques seulement. Au-delà, connecte ton compte ([README_SPOTIFY.md](README_SPOTIFY.md)) ou passe par un CSV.
- **Deezer** : seules les playlists **publiques** sont lisibles (API sans compte).
- **Apple Music par lien** : lu depuis la page web. Si Apple modifie son site, la lecture peut renvoyer 0 titre ou une erreur. Un avertissement s'affiche si moins de titres que prévu sont lus. La lecture par **nom** (app Musique) est réservée à macOS.
- **Correspondance** : la recherche SoundCloud (puis YouTube) prend le résultat le plus pertinent pour « artiste titre ». Vérifie avec `--dry-run`, puis écoute les remixes et les versions rares.
- **Qualité** : SoundCloud diffuse de l'audio déjà compressé (Opus ~256k ou MP3 128k). Le WAV ou l'AIFF ne crée pas de qualité. Ces formats donnent un fichier non compressé que Rekordbox analyse parfaitement.

## Dépannage

| Problème | Solution |
|---|---|
| `yt-dlp introuvable` / `ffmpeg introuvable` | Lance la commande affichée, puis **ferme et rouvre le terminal**. |
| `Module manquant : requests` (ou `spotipy`) | Lance le script avec le Python du venv, ou relance `install.sh` / `install.ps1`. |
| Beaucoup d'échecs ou des erreurs 403 | Mets yt-dlp à jour : `python -m pip install -U yt-dlp` (venv) ou `brew upgrade yt-dlp`. Pour YouTube, essaie `"youtube_cookies_browser": "chrome"`. |
| `Plateforme non reconnue` | Vérifie l'URL (playlist, album ou titre). Les liens de recherche ou de profil Spotify/Deezer ne sont pas gérés. |
| `Deezer : introuvable` | La playlist est privée : rends-la publique dans Deezer. |
| Apple Music : `404` ou 0 titre | La playlist n'est pas partagée publiquement, ou la page a changé. Sur macOS, mets plutôt le **nom** de la playlist. |
| `"…" n'est pas une URL : … macOS` | Sous Windows/Linux, utilise le lien `music.apple.com` au lieu du nom de la playlist. |
| Rien n'est téléchargé au 1er passage d'une playlist de `playlists.txt` | C'est la baseline : utilise `--download-all` une fois. |
| Accents ou emojis illisibles sous Windows | Utilise `sync.ps1`, ou lance avec `python -X utf8 mixdownload.py …` (le script tente de le faire tout seul). |
| Spotify : 403 / 404 / redirect URI | Voir [README_SPOTIFY.md](README_SPOTIFY.md#problèmes-fréquents). |

## Organisation du code

| Fichier | Rôle |
|---|---|
| `mixdownload.py` | Script principal : suivi des nouveautés, recherche et téléchargement (yt-dlp), options |
| `sources/` | Un module par plateforme : `apple.py` (app Musique), `apple_web.py`, `spotify.py`, `deezer.py`, `soundcloud.py`, `csvfile.py`. Détection automatique dans `__init__.py`. |
| `spotify_source.py` | Lecture Spotify (API avec compte ou page embed), utilisable seul (`--setup`, `--list`) |
| `install.sh` / `install.ps1` | Installation (venv + dépendances + vérification de ffmpeg) |
| `sync.sh` / `sync.ps1`, `com.mixdownload.sync.plist`, `install_task_windows.ps1` | Synchronisation quotidienne ([README_SYNC.md](README_SYNC.md)) |
