# ============================================================
#  storage-sense.ps1  -  Activa Storage Sense (SIN admin)
#  Config SEGURA: limpia temporales y papelera; NUNCA toca Descargas.
#  Reversible: exporta la clave antes de cambiar.
# ============================================================

$key = "HKCU:\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy"
$bk  = "$env:USERPROFILE\Documents\ClaudeBackup"
if(-not (Test-Path $bk)){ New-Item -ItemType Directory -Path $bk | Out-Null }

# Respaldo
if(Test-Path $key){
  reg export "HKCU\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy" "$bk\StorageSense_backup.reg" /y | Out-Null
  Write-Host "Respaldo guardado en $bk\StorageSense_backup.reg"
} else {
  New-Item -Path $key -Force | Out-Null
  Write-Host "Clave no existia; creada."
}

# Config segura
Set-ItemProperty -Path $key -Name "01"   -Value 1   -Type DWord   # Storage Sense ON
Set-ItemProperty -Path $key -Name "08"   -Value 1   -Type DWord   # Borrar temporales
Set-ItemProperty -Path $key -Name "32"   -Value 30  -Type DWord   # Papelera: elementos > 30 dias
Set-ItemProperty -Path $key -Name "256"  -Value 0   -Type DWord   # Descargas: NUNCA (0 = no tocar)
Set-ItemProperty -Path $key -Name "2048" -Value 7   -Type DWord   # Frecuencia: semanal (0=poco espacio,1=diario,7=semanal,30=mensual)

Write-Host "Storage Sense activado (seguro). Estado:" -ForegroundColor Green
$v = Get-ItemProperty -Path $key
[PSCustomObject]@{
  'On (01)'            = $v.'01'
  'Temporales (08)'    = $v.'08'
  'Papelera dias (32)' = $v.'32'
  'Descargas (256)'    = if($v.'256' -eq 0){'NUNCA'}else{$v.'256'}
  'Frecuencia (2048)'  = $v.'2048'
} | Format-List
