---
name: monitoreo-recursos
description: Rutinas para monitorear rendimiento en Windows (disco, CPU, RAM, procesos) que funcionan en equipos con idioma español. Usar al medir salud del sistema, encontrar el proceso que satura el disco, comprobar la cola de disco en reposo, o confirmar la mejora tras optimizar. Cubre cómo interpretar cada métrica.
---

# Monitoreo de recursos en Windows (compatible con español)

Rutinas de PowerShell probadas para medir rendimiento sin depender de contadores en inglés.

## ⚠️ Por qué NO usar Get-Counter
`Get-Counter` referencia contadores por nombre localizado (ej. `\Disco físico(_Total)\...`) y **falla en Windows en español**. Usa siempre las clases CIM `Win32_PerfFormattedData_*`, que son neutrales al idioma.

## Cola de disco en reposo (la métrica clave)
```powershell
$vals = 1..8 | ForEach-Object {
  $d = Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk | Where-Object { $_.Name -eq '_Total' }
  Start-Sleep -Seconds 2
  $d.AvgDiskQueueLength
}
"Cola: $($vals -join ', ') | Promedio: $([math]::Round(($vals|Measure-Object -Average).Average,1))"
```
| AvgDiskQueueLength | Estado |
|---|---|
| < 2 | Sano |
| 2 – 10 | Molesto (se nota lentitud) |
| 10 – 20 | Saturado |
| > 20 | Crítico (equipo casi no responde) |

**Toma varias muestras**: el disco trabaja en ráfagas, un solo valor engaña. `PercentDiskTime` > 100% es normal (es acumulado, no un porcentaje real).

## Proceso que golpea el disco
```powershell
Get-CimInstance Win32_PerfFormattedData_PerfProc_Process |
  Where-Object { $_.Name -notin '_Total','Idle' } |
  Sort-Object IODataBytesPersec -Descending | Select-Object -First 10 Name,
  @{N='IO_KBps';E={[math]::Round($_.IODataBytesPersec/1KB,0)}}, @{N='CPU%';E={$_.PercentProcessorTime}}
```
Culpables frecuentes:
- **TiWorker** = Windows Update instalando. **Temporal** — espera a que termine antes de juzgar.
- **CompatTelRunner** = telemetría de compatibilidad (desactivable).
- **MsMpEng** = Windows Defender escaneando.
- **SearchIndexer / SearchApp** = indexado de búsqueda.
- **svchost#NN** = servicios varios (SysMain/prefetch suele estar aquí).

## RAM y uptime
```powershell
$os = Get-CimInstance Win32_OperatingSystem
"Uptime: $([math]::Round(((Get-Date)-$os.LastBootUpTime).TotalMinutes,0)) min"
"RAM libre: $([math]::Round($os.FreePhysicalMemory/1MB,1)) / $([math]::Round($os.TotalVisibleMemorySize/1MB,1)) GB"
```
El **uptime importa**: recién arrancado, indexado y prefetch saturan el disco y se calman solos en ~20-40 min. Mide "en reposo" con buen rato de encendido y sin Windows Update corriendo.

## Top procesos por RAM
```powershell
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 12 Name,
  @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,0)}}, @{N='CPUseg';E={[math]::Round($_.CPU,0)}}
```

## Tipo de disco
```powershell
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, @{N='GB';E={[math]::Round($_.Size/1GB,0)}}
```
Si `Get-PhysicalDisk` expira, el disco está tan saturado que ni responde — es un síntoma en sí.

## Comprobar mejora (antes vs. después)
Guarda el promedio de cola ANTES de optimizar y vuelve a medir DESPUÉS, con condiciones comparables (mismo "reposo", sin updates). La caída de la cola es la prueba objetiva de la mejora.
