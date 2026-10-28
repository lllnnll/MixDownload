# MixDownload — surveillance quotidienne de playlists Apple Music → SoundCloud

Vérifie chaque jour tes playlists Apple Music. Dès qu'un nouveau morceau est
ajouté, il est cherché sur SoundCloud et téléchargé avec **yt-dlp** en **WAV**
(idéal pour l'analyse rekordbox), avec **plusieurs tentatives** en cas d'échec.
Si SoundCloud échoue après toutes les tentatives, le script **bascule
automatiquement sur YouTube** (toujours en meilleure qualité).

## Contenu

| Fichier | Rôle |
|---|---|
| `mixdownload.py` | Le script principal (diff quotidien + téléchargement + retries) |
| `playlists.txt` | **Tes playlists**, une par ligne — à remplir |
| `config.json` | Réglages (format, dossier de sortie, nb de tentatives…) |
| `com.nikita.mixdownload.plist` | La tâche planifiée macOS (launchd) — 18h00 chaque jour |
| `install.sh` | Installe les dépendances + active la tâche |
| `state.json` | Généré automatiquement : mémorise ce qui a déjà été vu |
| `downloads/` | Les morceaux téléchargés (un sous-dossier par playlist) |

## Installation (une seule fois)

```bash
bash /Users/nikita/Claude/Projects/MixDownload/install.sh
```

Cela installe `yt-dlp` et `ffmpeg` (via Homebrew) et active la tâche quotidienne.

## Configuration

Ajoute le **nom exact** de chaque playlist (tel qu'affiché dans l'app Musique)
dans `playlists.txt`, une par ligne :

```
Mes sons a mixer
Diggin 2026
```

## Première utilisation

Au tout premier passage sur une playlist, le script enregistre une *baseline*
(ce qui est déjà présent) **sans rien télécharger**, pour ne pas tout aspirer
d'un coup. Ensuite il ne prend que les ajouts.

Pour récupérer **tout l'existant** une fois :

```bash
python3 /Users/nikita/Claude/Projects/MixDownload/mixdownload.py --download-all
```

## Commandes utiles

```bash
# Vérification normale (ce que fait la tâche quotidienne)
python3 mixdownload.py

# Voir ce qui serait téléchargé, sans rien faire
python3 mixdownload.py --dry-run

# Tout (re)télécharger
python3 mixdownload.py --download-all

# Une seule playlist
python3 mixdownload.py --playlist "Diggin 2026"
```

## Réglages (`config.json`)

- `audio_format` : `wav` (défaut), `aiff`, `flac`, `mp3`, `m4a`…
- `output_dir` : dossier de sortie
- `subfolder_per_playlist` : un dossier par playlist (`true`/`false`)
- `max_retries` : nombre de tentatives par morceau (défaut `4`, backoff progressif)
- `search_results` : nb de résultats SoundCloud à essayer si la 1ʳᵉ tentative échoue

## Notes sur la qualité

SoundCloud diffuse de l'audio **déjà compressé** (souvent Opus ~256k ou MP3
128k selon le morceau). Le script récupère toujours le **meilleur flux
disponible** (`--audio-quality 0`) puis le convertit au format choisi. Convertir
en WAV ne *crée* pas de qualité supplémentaire, mais donne un fichier non
compressé que rekordbox analyse parfaitement (BPM, grille, formes d'onde).

## Logs & suivi

- `mixdownload.log` : journal détaillé de chaque exécution
- `launchd.out.log` / `launchd.err.log` : sortie de la tâche planifiée
- `state.json` : morceaux déjà traités. Les **échecs ne sont pas mémorisés** →
  ils sont automatiquement **réessayés** au passage suivant.

## Désactiver la tâche

```bash
launchctl unload ~/Library/LaunchAgents/com.nikita.mixdownload.plist
```
