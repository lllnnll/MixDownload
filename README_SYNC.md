# Synchronisation automatique quotidienne

MixDownload peut vérifier tes playlists chaque jour et télécharger **uniquement les nouveaux titres**. Les titres déjà récupérés sont mémorisés dans `.archive.txt`.

## 1. Lister tes playlists

Ouvre `playlists.txt` et mets une URL par ligne. Toutes les plateformes peuvent être mélangées. Les lignes qui commencent par `#` sont ignorées.

```
https://open.spotify.com/playlist/XXXXXXXXXXXXXXXXXXXXXX
https://www.deezer.com/fr/playlist/1234567890
https://music.apple.com/fr/playlist/ma-playlist/pl.xxxxxxxx
https://soundcloud.com/utilisateur/sets/ma-playlist
```

Pour Spotify, fais d'abord `python spotify_source.py --setup` (voir `README_SPOTIFY.md`). La connexion se renouvelle ensuite toute seule.

---

## macOS

### Prérequis
```bash
brew install python ffmpeg
pip3 install yt-dlp requests spotipy
```

### Tester
```bash
chmod +x sync.sh
./sync.sh
```
Les résultats sont dans `logs/`. Les morceaux vont dans `~/Music/DJ/MixDownload`.

### Automatiser (tous les jours à 9h)
1. Ouvre `com.mixdownload.sync.plist` et remplace `CHEMIN` par le chemin complet du dossier MixDownload (ex. `/Users/toi/MixDownload`).
2. Lance :
```bash
cp com.mixdownload.sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.mixdownload.sync.plist
launchctl start com.mixdownload.sync      # test immédiat
```
Si le Mac dormait à 9h, la tâche se lance à son réveil.

Pour désactiver : `launchctl unload ~/Library/LaunchAgents/com.mixdownload.sync.plist`

---

## Windows

### Prérequis
Ouvre **PowerShell** et lance :
```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```
**Ferme puis rouvre PowerShell** pour que ces commandes soient reconnues, puis :
```powershell
pip install yt-dlp requests spotipy
```
Vérifie avec `python --version` et `ffmpeg -version`.

> Si `python` ouvre le Microsoft Store, va dans **Paramètres → Applications → Paramètres avancés des applications → Alias d'exécution d'application** et désactive les alias « python.exe » et « python3.exe ».

### Tester
Dans le dossier MixDownload :
```powershell
powershell -ExecutionPolicy Bypass -File .\sync.ps1
```
Les résultats sont dans `logs\`. Les morceaux vont dans `C:\Users\<toi>\Music\DJ\MixDownload`.

### Automatiser (tous les jours à 9h)
```powershell
powershell -ExecutionPolicy Bypass -File .\install_task_windows.ps1
Start-ScheduledTask -TaskName MixDownload      # test immédiat
```
Pour choisir une autre heure, ajoute par exemple `-Heure 21:30` à la première commande.

Si le PC était éteint à l'heure prévue, la tâche se lance au démarrage suivant. Tu la retrouves dans le **Planificateur de tâches**, sous le nom « MixDownload ».

Pour désactiver : `Unregister-ScheduledTask -TaskName MixDownload -Confirm:$false`

---

## Options communes

| Réglage | macOS (`sync.sh`) | Windows (`sync.ps1`) |
|---|---|---|
| Dossier de sortie | `OUT=...` | `$Out = ...` |
| Format (`aiff`, `mp3`, `wav`…) | `FORMAT=...` | `$Format = ...` |
| Python d'un venv | `PYTHON=./venv/bin/python` | détecté automatiquement si `venv\` existe |

## À savoir
- **Ajouts seulement** : un titre retiré d'une playlist n'est pas supprimé de ton dossier.
- **Spotify sans compte** : une playlist d'un autre utilisateur reste plafonnée à environ 100 titres.
- **Apple Music** : la lecture se fait sur la page web. Si Apple change son site, la sync peut trouver 0 titre sans erreur. Vérifie les logs de temps en temps.
- **Format AIFF** : il s'importe sans souci dans Rekordbox, sur Mac comme sur Windows.
