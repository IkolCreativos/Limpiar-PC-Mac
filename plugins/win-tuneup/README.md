# win-tuneup

Plugin de Claude Code para **diagnóstico y optimización de rendimiento en Windows**, especialmente equipos con disco mecánico (HDD) que sufren saturación de disco.

Nace de la optimización real del **ASUS X555QG** (AMD A12-9720P, 12 GB RAM, HDD Toshiba 5400 RPM, Windows 10 Home 22H2), donde la cola de disco pasó de **41 → 0** aplicando estas rutinas.

## 🚀 Primeros pasos (Getting Started)

Este plugin forma parte del marketplace `mantenimiento-equipos`.

**1) Añade el marketplace** (una sola vez):
```
/plugin marketplace add IkolCreativos/Limpiar-PC-Mac
```

**2) Instala el plugin:**
```
/plugin install win-tuneup@mantenimiento-equipos
```

**3) Úsalo.** Ya tendrás disponibles:
- Comandos: `/diagnostico-pc` y `/monitor-disco`
- Agentes: `windows-diagnostics` y `windows-optimizer` (invócalos con el Agent tool o pídeselos a Claude)
- Skills: se activan solos cuando el contexto coincide (monitoreo, gotchas de PowerShell)

**Comandos útiles de gestión:**
```
/plugin marketplace update          # refrescar tras editar archivos
/plugin                              # ver/gestionar plugins instalados
claude plugin validate .            # validar el marketplace (desde la carpeta)
```

> 💡 **Flujo típico:** empieza con `/diagnostico-pc` para hallar el cuello de botella. Si es el disco, pide al agente `windows-optimizer` que aplique mejoras (te dará los scripts admin para ejecutar elevados). Al final, `/monitor-disco` para confirmar la mejora.

## Qué incluye

### Agentes (`agents/`)
- **windows-diagnostics** — Diagnostica cuellos de botella (disco / CPU / RAM / arranque) en modo *solo lectura*. Identifica el componente culpable con mediciones, sin cambiar nada.
- **windows-optimizer** — Aplica optimizaciones **reversibles con respaldo**: arranque, efectos visuales, energía, telemetría, desfragmentación, caché de navegador, Storage Sense, límite de CPU del antivirus.

### Skills (`skills/`)
- **monitoreo-recursos** — Rutinas de medición de disco/CPU/RAM/procesos que funcionan en Windows en español. Cómo interpretar la cola de disco, encontrar el proceso culpable y confirmar mejoras.
- **powershell-windows-gotchas** — Trampas técnicas encontradas (Get-Counter en español, %TEMP%, elevación/UAC, buffering de Optimize-Volume, encoding UTF-16, etc.).

### Comandos (`commands/`)
- **/diagnostico-pc** — Diagnóstico rápido de salud del equipo.
- **/monitor-disco** — Muestreo de la cola de disco en reposo + top de procesos por E/S.

### Scripts (`scripts/`)
Todos generan **log** y **respaldo del estado previo** en `Documents\ClaudeBackup\`. Los que requieren admin se ejecutan elevados por el usuario (Claude no puede lanzar procesos elevados en modo auto).
- `medir-disco.ps1` — Muestreo de disco (no requiere admin).
- `optimizar_telemetria_defrag.ps1` — **[ADMIN]** Desactiva telemetría de compatibilidad + desfragmenta el HDD.
- `optimizar_defender.ps1` — **[ADMIN]** Limita el CPU de Windows Defender en escaneos.
- `storage-sense.ps1` — Activa Storage Sense con config segura (no toca Descargas).

## Principios de este plugin
1. **Todo reversible** — siempre respaldar antes de cambiar.
2. **El disco es casi siempre el cuello de botella** en equipos lentos con HDD. Medir antes de tocar.
3. **Nunca matar procesos a ciegas** — reportar y bloquear en el arranque, no un "guardián asesino".
4. **La solución de fondo es un SSD** — estas rutinas exprimen el HDD, pero el salto real es cambiar el disco.
