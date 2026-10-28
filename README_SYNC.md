# Synchronisation automatique quotidienne

MixDownload peut vérifier tes playlists chaque jour et télécharger **uniquement les nouveaux titres**. Les titres déjà traités sont mémorisés dans `state.json`. Retour au [README principal](README.md).

## 1. Lister tes playlists

Crée `playlists.txt` (tu peux partir de [playlists.example.txt](playlists.example.txt)) et mets une entrée par ligne. Les plateformes peuvent être mélangées. Les lignes qui commencent par `#` sont ignorées.

```
https://open.spotify.com/playlist/XXXXXXXXXXXXXXXXXXXXXX
https://www.deezer.com/fr/playlist/1234567890
https://music.apple.com/fr/playlist/ma-playlist/pl.xxxxxxxx
https://soundcloud.com/utilisateur/sets/ma-playlist
```

Sur macOS, tu peux aussi mettre le **nom exact** d'une playlist de l'app Musique.

**Premier passage** : pour chaque nouvelle ligne, le script enregistre l'état actuel de la playlist **sans rien télécharger** (baseline). Seuls les titres ajoutés ensuite sont téléchargés. Pour récupérer l'existant une fois, lance avant `python mixdownload.py "<URL>"` (ou `--download-all`).

Pour Spotify avec ton compte, fais d'abord `python spotify_source.py --setup` (voir [README_SPOTIFY.md](README_SPOTIFY.md)). La connexion se renouvelle ensuite toute seule.

## Réglages de la synchro

`sync.sh` et `sync.ps1` lancent `mixdownload.py -o <dossier> --format <format>` une seule fois. Le script lit lui-même `playlists.txt`.

| Réglage | Défaut | Variable d'environnement |
|---|---|---|
| Dossier de sortie | `~/Music/MixDownload` | `MIXDOWNLOAD_OUT` |
| Format (`aiff`, `wav`, `mp3`…) | `aiff` | `MIXDOWNLOAD_FORMAT` |
| Python | `venv` s'il existe, sinon `python3` / `python` | `PYTHON` |

Tu peux aussi modifier directement les lignes `OUT=` / `FORMAT=` (`sync.sh`) ou `$Out` / `$Format` (`sync.ps1`).

---

## macOS

### Prérequis
Lance l'installation du [README principal](README.md#installation) : `bash install.sh`.

### Tester
```bash
./sync.sh
```
Les résultats sont dans `logs/`. Les morceaux vont dans `~/Music/MixDownload`.

### Automatiser (tous les jours à 9h)
Depuis le dossier MixDownload :
```bash
sed "s|CHEMIN|$PWD|" com.mixdownload.sync.plist > ~/Library/LaunchAgents/com.mixdownload.sync.plist
launchctl load ~/Library/LaunchAgents/com.mixdownload.sync.plist
launchctl start com.mixdownload.sync      # test immédiat
```
La commande `sed` remplace `CHEMIN` par le chemin du dossier. Pour changer l'heure, modifie `Hour` / `Minute` dans le fichier copié.

Si le Mac dormait à 9h, la tâche se lance à son réveil.

Pour désactiver : `launchctl unload ~/Library/LaunchAgents/com.mixdownload.sync.plist`

> La première fois, macOS peut demander d'autoriser l'accès à l'app Musique (playlists par nom), ou au dossier Musique.

---

## Linux

### Prérequis
`bash install.sh` (voir le [README principal](README.md#installation)).

### Automatiser (tous les jours à 9h, avec cron)
```bash
crontab -e
```
Puis ajoute la ligne suivante, en remplaçant le chemin :
```
0 9 * * * /bin/bash /chemin/vers/MixDownload/sync.sh
```

---

## Windows

### Prérequis
Ouvre **PowerShell** et lance :
```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```
**Ferme puis rouvre PowerShell** pour que ces commandes soient reconnues. Ensuite, dans le dossier MixDownload :
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
Vérifie avec `python --version` et `ffmpeg -version`.

> Si `python` ouvre le Microsoft Store, va dans **Paramètres → Applications → Paramètres avancés des applications → Alias d'exécution d'application** et désactive les alias « python.exe » et « python3.exe ».

### Tester
Dans le dossier MixDownload :
```powershell
powershell -ExecutionPolicy Bypass -File .\sync.ps1
```
Les résultats sont dans `logs\`. Les morceaux vont dans `C:\Users\<toi>\Music\MixDownload`.

### Automatiser (tous les jours à 9h)
```powershell
powershell -ExecutionPolicy Bypass -File .\install_task_windows.ps1
Start-ScheduledTask -TaskName MixDownload      # test immédiat
```
Pour choisir une autre heure, ajoute par exemple `-Heure 21:30` à la première commande.

Si le PC était éteint à l'heure prévue, la tâche se lance au démarrage suivant. Tu la retrouves dans le **Planificateur de tâches**, sous le nom « MixDownload ».

Pour désactiver : `Unregister-ScheduledTask -TaskName MixDownload -Confirm:$false`

---

## À savoir
- **Ajouts seulement** : un titre retiré d'une playlist n'est pas supprimé de ton dossier.
- **Échecs** : un titre introuvable n'est pas mémorisé. Il est réessayé à la synchro suivante.
- **Spotify sans compte** : une playlist d'un autre utilisateur reste plafonnée à environ 100 titres.
- **Apple Music par lien** : la lecture se fait sur la page web. Si Apple change son site, la synchro peut trouver 0 titre ou afficher une erreur. Vérifie les logs de temps en temps.
- **Format AIFF** : il s'importe sans souci dans Rekordbox, sur Mac comme sur Windows.
