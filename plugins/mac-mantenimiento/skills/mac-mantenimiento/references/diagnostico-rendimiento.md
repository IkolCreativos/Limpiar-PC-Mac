# Diagnóstico de rendimiento en macOS

Orden de comprobación. La causa más frecuente de lentitud en equipos con pocos
años es **memoria agotada volcando swap sobre un disco lento**, no un procesador
insuficiente ni un disco averiado.

## 1. Identificar el hardware

```bash
system_profiler SPHardwareDataType | head -20
sysctl -n hw.memsize hw.physicalcpu
sw_vers
```

## 2. Tipo de almacenamiento — determinante

```bash
diskutil list physical
system_profiler SPStorageDataType | grep -iE "Medium Type|Device Name|Solid State"
diskutil apfs list | grep -iE "Fusion|Physical Store|Capacity"
```

Un **Fusion Drive** combina un SSD pequeño (24–128 GB) con un disco mecánico.
Aparece como un único volumen APFS con dos Physical Stores: uno marcado
"Main, Faster Disk Use" y otro "Secondary, Designated Aux Use".

Implicación: si hay swap activo, cae sobre el disco mecánico. La latencia pasa
de ~0,1 ms a ~10 ms. Cien veces más lento.

## 3. Presión de memoria y swap

```bash
vm_stat
sysctl vm.swapusage
memory_pressure | tail -8
```

Interpretación:
- `used` en swap por encima de 2 GB: el disco está haciendo de RAM.
- `Pages free` muy bajo con `Pages compressed` alto: sistema saturado.
- `swapins`/`swapouts` crecientes entre dos lecturas: thrashing activo.

Medir dos veces separadas por unos minutos. Un swap que **crece durante la
observación** confirma el diagnóstico.

## 4. Ocupación de disco

```bash
df -h /System/Volumes/Data
```
Usar siempre el volumen de datos. `/` es el volumen de sistema de solo lectura y
muestra una ocupación baja y engañosa.

## 5. Descartar fallo de hardware

```bash
pmset -g therm                      # CPU_Speed_Limit < 100 indica throttling térmico
diskutil info diskN | grep SMART    # debe decir "Verified"
log show --last 24h --predicate 'eventMessage CONTAINS "I/O error"' | head
```
`SMART Status: Not Supported` es normal en discos USB: el puente no lo expone.
Significa que **no se puede evaluar su salud** — dato relevante si ese disco va
a ser la única copia de algo.

## 6. Consumo por proceso

```bash
ps -Aceo pcpu,pmem,rss,comm -r | head -20    # por CPU
ps -Aceo pmem,rss,pcpu,comm -m | head -20    # por memoria
ps -Aco comm | sort | uniq -c | sort -rn | head    # procesos por app
```

Los navegadores basados en Chromium generan un proceso por pestaña; con decenas
abiertas suman varios GB. Las suites de diseño y ofimática cargan servicios
residentes aunque la app esté cerrada.

## 7. Software de arranque automático

```bash
ls -1 ~/Library/LaunchAgents/ /Library/LaunchAgents/ /Library/LaunchDaemons/
osascript -e 'tell application "System Events" to get the name of every login item'
```
Actualizadores, sincronizadores y asistentes de suites comerciales. Desactivarlos
libera poca memoria (cientos de MB) — **es la palanca más pequeña**. No venderla
como solución si el problema real es la RAM.

## Ajustes de bajo riesgo y efecto real

```bash
sudo pmset -a hibernatemode 0        # en equipos de sobremesa: no hay batería
sudo rm -f /private/var/vm/sleepimage # libera un archivo del tamaño de la RAM
sudo mdutil -i off /Volumes/EXTERNO   # deja de indexar discos de archivo
```
Añadir carpetas de archivo muerto a la lista de privacidad de Spotlight reduce
E/S de fondo constante.

## Jerarquía de impacto

1. **Ampliar RAM** si hay slots libres (`system_profiler SPMemoryDataType`
   muestra "Upgradeable Memory: Yes" y bancos vacíos). Elimina el swap de raíz.
2. **Liberar disco** por debajo del 80% en Fusion Drive.
3. **Disco de arranque externo SSD por Thunderbolt** si el interno es mecánico.
4. **Disciplina de uso**: no mantener abiertas a la vez varias aplicaciones de
   diseño y ofimática en equipos con memoria justa.
5. Desactivar servicios de fondo — marginal frente a lo anterior.
