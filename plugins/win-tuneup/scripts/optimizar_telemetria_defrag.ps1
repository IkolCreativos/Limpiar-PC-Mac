# ============================================================
#  optimizar_telemetria_defrag.ps1  -  [REQUIERE ADMIN]
#  Desactiva telemetria de compatibilidad + desfragmenta el HDD.
#  Todo reversible. Genera log y respaldo del estado previo.
#  Ejecutar elevado:
#    Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy','Bypass','-File','<ruta>'
# ============================================================

$ErrorActionPreference = 'Continue'
$bk  = "$env:USERPROFILE\Documents\ClaudeBackup"
$log = "$bk\telemetria_defrag_log.txt"
if(-not (Test-Path $bk)){ New-Item -ItemType Directory -Path $bk | Out-Null }
function Log($m){ $m | Tee-Object -FilePath $log -Append }
"===== Ejecucion $(Get-Date) =====" | Out-File $log -Append -Encoding utf8

$esAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $esAdmin){ Log "ERROR: NO se ejecuta como administrador."; return }
Log "OK: ejecutando como administrador."

# ---------- 1) TELEMETRIA ----------
Log "`n--- Desactivando tareas de telemetria (reversible) ---"
$tareas = @(
  '\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser',
  '\Microsoft\Windows\Application Experience\ProgramDataUpdater',
  '\Microsoft\Windows\Application Experience\StartupAppTask',
  '\Microsoft\Windows\Customer Experience Improvement Program\Consolidator',
  '\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip',
  '\Microsoft\Windows\Autochk\Proxy'
)
$estadoPrevio = foreach($t in $tareas){
  $p = Split-Path $t; $n = Split-Path $t -Leaf
  $task = Get-ScheduledTask -TaskPath "$p\" -TaskName $n -ErrorAction SilentlyContinue
  if($task){ [PSCustomObject]@{ Tarea=$t; EstadoPrevio=$task.State } }
}
$estadoPrevio | Format-Table -AutoSize | Out-String | Out-File "$bk\Tareas_telemetria_estado_previo.txt" -Encoding utf8
foreach($t in $tareas){
  $p = Split-Path $t; $n = Split-Path $t -Leaf
  try { Disable-ScheduledTask -TaskPath "$p\" -TaskName $n -ErrorAction Stop | Out-Null; Log ("  Desactivada: {0}" -f $t) }
  catch { Log ("  (No se pudo / no existe): {0}" -f $t) }
}

# ---------- 2) DESFRAGMENTACION (solo si es HDD) ----------
$disco = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq 0 }
if($disco -and $disco.MediaType -eq 'SSD'){
  Log "`n--- OMITIENDO desfragmentacion: el disco es SSD (no se debe desfragmentar) ---"
} else {
  Log "`n--- Analizando fragmentacion de C: ---"
  try { Optimize-Volume -DriveLetter C -Analyze -Verbose 4>&1 | Out-String | ForEach-Object { Log $_ } } catch { Log "No se pudo analizar: $_" }
  Log "`n--- Desfragmentando C: (puede tardar HORAS en un HDD; el log aparece al terminar) ---"
  try { Optimize-Volume -DriveLetter C -Defrag -Verbose 4>&1 | Out-String | ForEach-Object { Log $_ }; Log "Desfragmentacion terminada." }
  catch { Log "Error en desfragmentacion: $_" }
}

Log "`n===== FIN $(Get-Date) ====="
Write-Host "`nLISTO. Log en: $log" -ForegroundColor Green

# ---- REVERTIR telemetria (manual): Enable-ScheduledTask -TaskPath '<ruta>\' -TaskName '<nombre>' ----
