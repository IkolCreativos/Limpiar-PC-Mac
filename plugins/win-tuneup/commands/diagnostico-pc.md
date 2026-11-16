---
description: Diagnóstico rápido de rendimiento del equipo Windows (disco, CPU, RAM, arranque). Solo lectura.
---

Ejecuta un diagnóstico de rendimiento completo de este equipo Windows, en **modo solo lectura** (no cambies nada). Usa el skill `monitoreo-recursos` y las clases CIM `Win32_PerfFormattedData_*` (NO `Get-Counter`, falla en español).

Mide y reporta:
1. **Uptime y RAM** libre/total.
2. **Cola de disco en reposo** — 8 muestras cada 2s, con promedio e interpretación (sano <2).
3. **Proceso que más golpea el disco** (top por `IODataBytesPersec`). Distingue lo temporal (TiWorker/Windows Update) de lo crónico.
4. **Tipo de disco** (`Get-PhysicalDisk`, MediaType HDD vs SSD).
5. **Top procesos por RAM**.

Entrega un veredicto claro del **componente culpable** con el dato que lo prueba, y una recomendación priorizada. Si es un HDD saturado, menciona que la solución de fondo es un SSD y qué optimizaciones de software ayudan mientras tanto. Ofrece continuar con el agente `windows-optimizer` si el usuario quiere aplicar mejoras.

Argumentos opcionales del usuario: $ARGUMENTS
