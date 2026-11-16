---
description: Muestrea la cola de disco en reposo y el top de procesos por E/S. Útil para comprobar mejoras.
---

Monitorea el disco de este equipo Windows (solo lectura). Usa el skill `monitoreo-recursos`.

1. Reporta el **uptime** y si Windows Update (`TiWorker`) está activo — para saber si es un "reposo" válido.
2. Toma **8 muestras** de `AvgDiskQueueLength` (`Win32_PerfFormattedData_PerfDisk_PhysicalDisk`, `_Total`) cada 2 segundos y muestra la lista y el promedio, con interpretación (sano <2, saturado >10).
3. Muestra el **top 8 de procesos por E/S de disco**.

Si el usuario tiene una medición previa guardada (o está en memoria), **compara** antes vs. después y comenta la mejora.

Argumentos opcionales: $ARGUMENTS
