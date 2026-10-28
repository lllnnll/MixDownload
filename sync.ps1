# Synchronise toutes les playlists de playlists.txt (seuls les nouveaux titres sont téléchargés).
# Réglages modifiables ici ou par variables d'environnement (MIXDOWNLOAD_OUT, MIXDOWNLOAD_FORMAT, PYTHON).
Set-Location -Path $PSScriptRoot

$Python = if ($env:PYTHON) { $env:PYTHON } elseif (Test-Path ".\venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }
$Out    = if ($env:MIXDOWNLOAD_OUT) { $env:MIXDOWNLOAD_OUT } else { Join-Path $env:USERPROFILE "Music\MixDownload" }
$Format = if ($env:MIXDOWNLOAD_FORMAT) { $env:MIXDOWNLOAD_FORMAT } else { "aiff" }
$Log    = "logs\sync_$(Get-Date -Format 'yyyy-MM-dd').log"

# Évite les plantages d'encodage (emojis) dans la console Windows
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

New-Item -ItemType Directory -Force -Path "logs", $Out | Out-Null
"=== Sync $(Get-Date) ===" | Out-File -Append -Encoding utf8 $Log

# mixdownload.py lit lui-même playlists.txt et ne télécharge que les nouveautés
& $Python mixdownload.py -o $Out --format $Format 2>&1 | Out-File -Append -Encoding utf8 $Log
if ($LASTEXITCODE -ne 0) { "Échec de la synchronisation (code $LASTEXITCODE)" | Out-File -Append -Encoding utf8 $Log }

# Garde 30 jours de logs
Get-ChildItem logs -Filter *.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item
