# Installation de MixDownload (Windows) :
#   - crée un environnement virtuel Python (venv\)
#   - installe les dépendances (requirements.txt : yt-dlp, requests, spotipy)
#   - vérifie ffmpeg
#
# Usage (dans le dossier MixDownload) :
#   powershell -ExecutionPolicy Bypass -File .\install.ps1

Set-Location -Path $PSScriptRoot
$env:PYTHONUTF8 = "1"

# --- Python 3.9+ : lanceur « py » d'abord, sinon « python » ---
$PyCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c "import sys; sys.exit(sys.version_info < (3, 9))" 2>$null
    if ($LASTEXITCODE -eq 0) { $PyCmd = @("py", "-3") }
}
if (-not $PyCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c "import sys; sys.exit(sys.version_info < (3, 9))" 2>$null
    if ($LASTEXITCODE -eq 0) { $PyCmd = @("python") }
}
if (-not $PyCmd) {
    Write-Host "!! Python 3.9 ou plus récent introuvable. Installe-le :  winget install Python.Python.3.12"
    Write-Host "   Puis ferme et rouvre PowerShell. Si « python » ouvre le Microsoft Store, désactive"
    Write-Host "   les alias dans Paramètres > Applications > Alias d'exécution d'application."
    exit 1
}

$PyExe = $PyCmd[0]
$PyArgs = @($PyCmd | Select-Object -Skip 1)
Write-Host "==> Création de l'environnement virtuel (venv\)"
& $PyExe @PyArgs -m venv venv
if ($LASTEXITCODE -ne 0) { Write-Host "!! Échec de création du venv."; exit 1 }

$VenvPy = ".\venv\Scripts\python.exe"
Write-Host "==> Installation des dépendances (requirements.txt)..."
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet --upgrade -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "!! Échec de l'installation des dépendances."; exit 1 }
Write-Host "    yt-dlp $(& .\venv\Scripts\yt-dlp.exe --version)"

# --- ffmpeg (conversion audio) ---
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    Write-Host "==> ffmpeg : $($ffmpeg.Source)"
} else {
    Write-Host "!! ffmpeg introuvable (indispensable pour convertir l'audio). Installe-le :"
    Write-Host "   winget install Gyan.FFmpeg"
    Write-Host "   puis ferme et rouvre PowerShell."
}

Write-Host ""
Write-Host "Installation terminée."
Write-Host ""
Write-Host "Prochaines étapes :"
Write-Host "  1. Test à blanc :   .\venv\Scripts\python.exe mixdownload.py `"<url de playlist>`" --dry-run"
Write-Host "  2. Téléchargement : .\venv\Scripts\python.exe mixdownload.py `"<url de playlist>`""
Write-Host "  3. Sync quotidienne : ajoute tes URL dans playlists.txt, puis voir README_SYNC.md"
