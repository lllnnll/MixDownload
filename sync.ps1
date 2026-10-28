# Synchronise toutes les playlists de playlists.txt (seuls les nouveaux titres sont téléchargés).
Set-Location -Path $PSScriptRoot

$Python = if ($env:PYTHON) { $env:PYTHON } elseif (Test-Path ".\venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }
$Out    = Join-Path $env:USERPROFILE "Music\DJ\MixDownload"
$Format = "aiff"
$Log    = "logs\sync_$(Get-Date -Format 'yyyy-MM-dd').log"

# Évite les plantages d'encodage (emojis) dans la console Windows
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

New-Item -ItemType Directory -Force -Path "logs", $Out | Out-Null
"=== Sync $(Get-Date) ===" | Out-File -Append -Encoding utf8 $Log

Get-Content playlists.txt | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") } | ForEach-Object {
    $url = $_.Trim()
    "--- $url" | Out-File -Append -Encoding utf8 $Log
    & $Python mixdownload.py $url -o $Out --format $Format 2>&1 | Out-File -Append -Encoding utf8 $Log
    if ($LASTEXITCODE -ne 0) { "Échec : $url" | Out-File -Append -Encoding utf8 $Log }
    Start-Sleep -Seconds 30   # évite de se faire limiter par SoundCloud
}

# Garde 30 jours de logs
Get-ChildItem logs -Filter *.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item
