# ============================================================
#  medir-disco.ps1  -  Muestreo de disco/CPU/RAM (SIN admin)
#  Compatible con Windows en espanol (usa clases CIM).
# ============================================================

$os = Get-CimInstance Win32_OperatingSystem
$up = (Get-Date) - $os.LastBootUpTime
Write-Host "Uptime: $([math]::Round($up.TotalMinutes,0)) min" -ForegroundColor Cyan
$tiw = if(Get-Process TiWorker -ErrorAction SilentlyContinue){'SI (Windows Update activo - reposo NO valido)'}else{'No'}
Write-Host "Windows Update (TiWorker) activo: $tiw"
Write-Host "RAM libre: $([math]::Round($os.FreePhysicalMemory/1MB,1)) / $([math]::Round($os.TotalVisibleMemorySize/1MB,1)) GB`n"

Write-Host "== Cola de disco (8 muestras cada 2s) ==" -ForegroundColor Cyan
$vals = 1..8 | ForEach-Object {
  $d = Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk | Where-Object { $_.Name -eq '_Total' }
  Start-Sleep -Seconds 2
  $d.AvgDiskQueueLength
}
$prom = [math]::Round(($vals | Measure-Object -Average).Average,1)
Write-Host "Muestras: $($vals -join ', ')"
Write-Host "Promedio: $prom  (sano <2 | molesto 2-10 | saturado >10 | critico >20)`n"

Write-Host "== Top 8 procesos por E/S de disco ==" -ForegroundColor Cyan
Get-CimInstance Win32_PerfFormattedData_PerfProc_Process |
  Where-Object { $_.Name -notin '_Total','Idle' } |
  Sort-Object IODataBytesPersec -Descending | Select-Object -First 8 Name,
  @{N='IO_KBps';E={[math]::Round($_.IODataBytesPersec/1KB,0)}}, @{N='CPU%';E={$_.PercentProcessorTime}} |
  Format-Table -AutoSize

Write-Host "== Tipo de disco ==" -ForegroundColor Cyan
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, @{N='GB';E={[math]::Round($_.Size/1GB,0)}} | Format-Table -AutoSize
