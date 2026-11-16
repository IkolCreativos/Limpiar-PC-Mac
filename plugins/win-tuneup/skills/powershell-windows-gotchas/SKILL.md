---
name: powershell-windows-gotchas
description: Trampas técnicas al automatizar Windows con PowerShell 5.1, especialmente en equipos en español y bajo Claude Code. Usar al escribir scripts de mantenimiento/optimización, manejar elevación/UAC, leer contadores de rendimiento, desfragmentar, o cuando algo "debería funcionar" y falla por idioma, encoding o permisos.
---

# Gotchas: PowerShell + Windows (español) bajo Claude Code

Colección de trampas reales encontradas optimizando equipos Windows. Léela antes de escribir scripts de mantenimiento.

## 1. Get-Counter falla en Windows en español
Los nombres de contador están localizados (`\Disco físico(_Total)\...`), así que `Get-Counter` con nombres en inglés falla, y con nombres en español es frágil.
**Solución:** usa clases CIM neutrales: `Win32_PerfFormattedData_PerfDisk_PhysicalDisk`, `Win32_PerfFormattedData_PerfProc_Process`, `Win32_PerfFormattedData_PerfOS_Memory`.

## 2. Elevación / UAC y Claude Code
- Una cuenta puede ser **administrador pero mostrarse sin privilegios** por el token filtrado de UAC. No hace falta otra cuenta; basta elevar.
- **Claude Code en modo auto NO puede lanzar procesos elevados** ni usar `-ExecutionPolicy Bypass`. Patrón correcto:
  1. Escribe el script `.ps1` (con auto-chequeo de elevación adentro).
  2. Dale al usuario el comando para ejecutarlo él:
     ```
     ! Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy','Bypass','-File','C:\ruta\script.ps1'
     ```
  3. Verifica leyendo el **log** o el estado resultante (eso sí se puede sin admin).
- Auto-chequeo de elevación dentro del script:
  ```powershell
  $esAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if(-not $esAdmin){ "No es admin"; return }
  ```

## 3. NO borrar %TEMP% recursivamente
Claude Code trabaja en `%TEMP%\claude`. Un `Remove-Item %TEMP%\* -Recurse` **rompe la lectura de salida del propio Claude Code** a mitad de sesión. Limpia rutas específicas (INetCache, prefetch), nunca `%TEMP%` entero.

## 4. Optimize-Volume: el log solo aparece al terminar
Con `Optimize-Volume ... -Verbose | Out-String | ...`, `Out-String` **almacena toda la salida y la emite de golpe al final**. Durante la desfrag el log parece "congelado" aunque esté trabajando.
**Para confirmar que avanza:** `Get-Service defragsvc` (Running = activo) y muestrea la actividad de disco. En un HDD la desfrag puede tardar **horas**.
Además: `-Defrag` es para HDD; **NUNCA desfragmentes un SSD** (usa `-ReTrim`). Comprueba `MediaType` antes.

## 5. Encoding UTF-16 y acentos rotos
- PowerShell 5.1 escribe archivos en **UTF-16 LE con BOM** por defecto. Si otro proceso (o Claude) leerá el archivo, usa `-Encoding utf8`.
- La salida de `.exe` nativos redirigida a log puede mostrar acentos rotos (`An�lisis`); es cosmético. Para limpiar al leer: `(Get-Content $log -Raw) -replace "`0",""`.

## 6. Sintaxis PowerShell 5.1 (no confundir con PS7)
- **No existen** `&&`, `||`, ternario `?:`, `??`, `?.`. Usa `if/else` y `;`.
- Un `foreach(){...} | comando` da "elementos de canalización vacíos": asigna a variable primero (`$r = foreach(...){...}; $r | ...`).
- Al llamar `.exe` con argumentos que empiezan por `-`/`@`, usa `--%` o pásalos como array.

## 7. Respaldos antes de cambiar (siempre)
- Registro: `reg export "HKCU\ruta" "C:\...\ClaudeBackup\clave.reg" /y`
- Tareas programadas: guarda su `.State` antes de `Disable-ScheduledTask`.
- Preferencias: `Get-MpPreference | Select ... | Out-File`.
Carpeta estándar de respaldos: `C:\Users\<user>\Documents\ClaudeBackup\`.
