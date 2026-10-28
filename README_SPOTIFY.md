# Utiliser MixDownload avec Spotify

Retour au [README principal](README.md).

MixDownload lit les titres de ta playlist Spotify, puis les cherche et les télécharge sur SoundCloud. **Aucun fichier audio n'est récupéré depuis Spotify.**

## Quel mode choisir ?

| Ta situation | Mode | Configuration |
|---|---|---|
| Playlist publique de moins de 100 titres | Sans compte | Aucune |
| Tes propres playlists (même privées ou longues) | Avec compte | 5 minutes, une seule fois |
| Playlist de quelqu'un d'autre de plus de 100 titres | Export CSV | Aucune |

Le script choisit tout seul : il essaie le mode « avec compte » s'il est configuré, sinon il passe au mode « sans compte ».

`python` désigne ici le Python du venv créé par `install.sh` / `install.ps1` (`venv/bin/python`, ou `.\venv\Scripts\python.exe` sous Windows). spotipy y est déjà installé.

## Mode sans compte

Rien à faire, colle simplement le lien :

```bash
python mixdownload.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --dry-run
```

Limite : environ 100 titres et uniquement les playlists publiques.

## Mode avec compte (recommandé pour tes playlists)

Spotify exige que **chaque utilisateur crée sa propre « app » développeur**. C'est gratuit, mais il faut un **compte Spotify Premium**. Ces informations restent sur ton ordinateur.

### 1. Créer l'app

1. Va sur <https://developer.spotify.com/dashboard> et connecte-toi avec ton compte Spotify.
2. Clique sur **Create app** et remplis :
   - **App name** : `MixDownload` (ou ce que tu veux)
   - **App description** : `Usage personnel`
   - **Website** : laisse vide
   - **Redirect URI** : `http://127.0.0.1:8888/callback`, puis clique sur **Add**
     ⚠️ Écris bien `127.0.0.1`, et non `localhost` (Spotify refuse `localhost`).
   - **Which API/SDKs** : coche **Web API**
3. Accepte les conditions, puis clique sur **Save**.

### 2. Autoriser ton compte

Dans l'app, ouvre **Settings → User Management** et ajoute le nom et l'e-mail de ton compte Spotify.

### 3. Récupérer les clés

Dans **Settings**, copie le **Client ID**. Clique ensuite sur **View client secret** et copie le **Client Secret**.
🔒 Ne partage jamais ton Client Secret.

### 4. Configurer MixDownload

```bash
python spotify_source.py --setup
```

Colle les deux clés quand le script te les demande. Ton navigateur s'ouvre et te demande d'autoriser l'app : accepte. Tu n'auras plus à le refaire.

Si le navigateur affiche une page qui ne charge pas, copie l'URL complète de cette page et colle-la dans le terminal.

### 5. Choisir ta playlist

```bash
python spotify_source.py --list
```

Cette commande affiche toutes tes playlists avec leur lien. Copie celle que tu veux télécharger :

```bash
python mixdownload.py "https://open.spotify.com/playlist/XXXX" --dry-run   # vérifier les correspondances
python mixdownload.py "https://open.spotify.com/playlist/XXXX"             # télécharger
```

## Mode export CSV

Si tu veux une longue playlist qui ne t'appartient pas, exporte-la en CSV avec un service comme TuneMyMusic ou Soundiiz, puis :

```bash
python mixdownload.py ma_playlist.csv
```

## Problèmes fréquents

| Message | Solution |
|---|---|
| `403 Accès refusé` | Vérifie que ton compte est Premium et que ton e-mail est dans **User Management**. |
| `404 Introuvable` | La playlist n'est pas à toi. Le script passe automatiquement au mode sans compte ; utilise un CSV si elle dépasse 100 titres. |
| `INVALID_CLIENT: Invalid redirect URI` | La Redirect URI de l'app doit être exactement `http://127.0.0.1:8888/callback`. |
| `Module manquant : spotipy` | Utilise le Python du venv, ou relance `install.sh` / `install.ps1`. |
| Tu veux changer de compte | `python spotify_source.py --logout`, puis `--setup` |

Les clés sont stockées dans `~/.mixdownload/spotify.json`. Tu peux aussi utiliser les variables d'environnement `SPOTIFY_CLIENT_ID` et `SPOTIFY_CLIENT_SECRET`.
