# Crée une tâche planifiée Windows qui lance sync.ps1 tous les jours.
# Usage : clic droit > « Exécuter avec PowerShell »  (ou : powershell -ExecutionPolicy Bypass -File install_task_windows.ps1)
param([string]$Heure = "09:00")

$script = Join-Path $PSScriptRoot "sync.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`"" `
    -WorkingDirectory $PSScriptRoot
$trigger  = New-ScheduledTaskTrigger -Daily -At $Heure
# StartWhenAvailable : rattrape la tâche si le PC était éteint à l'heure prévue
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask -TaskName "MixDownload" -Action $action -Trigger $trigger `
    -Settings $settings -Description "Synchronisation quotidienne des playlists MixDownload" -Force | Out-Null

Write-Host "Tâche « MixDownload » créée : tous les jours à $Heure."
Write-Host "Tester maintenant : Start-ScheduledTask -TaskName MixDownload"
