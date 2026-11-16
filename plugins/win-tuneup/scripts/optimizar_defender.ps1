# ============================================================
#  optimizar_defender.ps1  -  [REQUIERE ADMIN]
#  Limita el uso de CPU de Windows Defender en escaneos.
#  NO desactiva el antivirus. Reversible, con respaldo.
#  Ejecutar elevado:
#    Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy','Bypass','-File','<ruta>'
# ============================================================

$ErrorActionPreference = 'Continue'
$bk  = "$env:USERPROFILE\Documents\ClaudeBackup"
$log = "$bk\defender_log.txt"
if(-not (Test-Path $bk)){ New-Item -ItemType Directory -Path $bk | Out-Null }
function Log($m){ $m | Tee-Object -FilePath $log -Append }
"===== Ejecucion $(Get-Date) =====" | Out-File $log -Append -Encoding utf8

$esAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $esAdmin){ Log "ERROR: NO se ejecuta como administrador."; return }
Log "OK: ejecutando como administrador."

Log "`n--- Estado PREVIO (respaldo) ---"
$prev = Get-MpPreference | Select-Object ScanAvgCPULoadFactor, ScanOnlyIfIdleEnabled, DisableCpuThrottleOnIdleScans
$prev | Format-List | Out-String | ForEach-Object { Log $_ }
$prev | Format-List | Out-String | Out-File "$bk\Defender_estado_previo.txt" -Encoding utf8

Log "`n--- Aplicando limites ---"
try {
  Set-MpPreference -ScanAvgCPULoadFactor 30 -ErrorAction Stop
  Log "  ScanAvgCPULoadFactor = 30 (max 30% CPU en escaneos)"
  Set-MpPreference -ScanOnlyIfIdleEnabled $true -ErrorAction Stop
  Log "  ScanOnlyIfIdleEnabled = True (escanea en reposo)"
} catch { Log "  Error: $_" }

Log "`n--- Estado FINAL ---"
Get-MpPreference | Select-Object ScanAvgCPULoadFactor, ScanOnlyIfIdleEnabled | Format-List | Out-String | ForEach-Object { Log $_ }
Log "===== FIN $(Get-Date) ====="
Write-Host "`nLISTO. Log en: $log" -ForegroundColor Green

# ---- REVERTIR (manual, con el valor previo del respaldo): Set-MpPreference -ScanAvgCPULoadFactor 50 ----
