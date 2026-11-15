---
name: mac-mantenimiento
description: Diagnóstico de rendimiento, auditoría de almacenamiento, deduplicación por contenido y organización de archivos multimedia en macOS. Úsala cuando un Mac vaya lento, falte espacio en disco, haya que consolidar carpetas duplicadas entre varios discos, o se necesite ordenar fotos y vídeos por metadatos. Cubre Fusion Drive, presión de memoria, trampas de sistemas de archivos y lectura de EXIF en JPEG/HEIC/vídeo.
---

# Mantenimiento y auditoría de almacenamiento en macOS

Procedimientos probados para diagnosticar lentitud, recuperar espacio y consolidar
archivos sin perder datos. Todo el enfoque se apoya en una regla central:

> **Nunca borrar. Mover a cuarentena, verificar, y que la persona decida.**

## Principios que gobiernan todo el trabajo

1. **Medir antes de actuar.** Nunca estimar tamaños ni suponer duplicación.
   Un `du -sh` mal leído puede llevar a borrar lo que no toca.
2. **Comparar por contenido, no por nombre.** Dos archivos con el mismo nombre
   pueden diferir; dos con nombres distintos pueden ser idénticos.
3. **Mover en vez de borrar.** Toda operación destructiva se convierte en un
   movimiento a una carpeta `BORRAR-<motivo>/` que conserva la estructura original.
4. **Dejar manifiesto.** Cada operación escribe un CSV con origen, destino y la
   copia conservada. Sin manifiesto no hay marcha atrás ni auditoría.
5. **Verificar después.** Recuento de archivos + muestra de hashes MD5 antes de
   declarar nada como completado.
6. **Confirmar la red de seguridad antes de cada paso irreversible.** Comprobar
   explícitamente que existe otra copia verificada.

## Antes del primer uso en un Mac

Ejecutar una vez `scripts/preparar.sh` (y de nuevo tras cada actualización del
plugin). Compila las dos utilidades Swift para la arquitectura de este equipo y
comprueba dependencias; no instala nada, solo indica qué falta y cómo ponerlo.
Los scripts de Python se invocan siempre con `/usr/bin/python3`.

## Flujo de trabajo

### Fase 1 — Diagnóstico
Ver `references/diagnostico-rendimiento.md`.
Ejecutar `scripts/diagnose.sh` para una radiografía en segundos.
Determinar si el cuello de botella es RAM, disco, térmico o software de fondo.

### Fase 2 — Recuperar espacio evidente
Papelera sin vaciar, cachés, hibernación, indexado de discos externos,
copias de seguridad de dispositivos móviles. Ver `references/espacio-rapido.md`.

### Fase 3 — Auditoría de duplicados
`scripts/duplicados.py` para un informe; `scripts/dedup_cuarentena.py` para actuar.
Ver `references/deduplicacion.md` para la estrategia de tres pasadas.

### Fase 4 — Consolidación entre ubicaciones
`scripts/cruce_ubicaciones.py` cruza N carpetas y devuelve la matriz de solapamiento.
Ver `references/consolidacion.md`.

### Fase 5 — Adelgazar archivos de diseño
Para material de cliente cerrado que se guarda como registro, no para reeditar.
Leer antes `references/archivos-diseno.md` y `references/herramientas.md`.

```
aplanar_ilustracion.py   .ai: suelta datos nativos, conserva vectores
reducir_incrustadas.py   .ai/.pdf: reduce las fotos de dentro (necesita ghostscript)
reducir_imagenes.py      PSD e imágenes: aplana y reduce al tamaño de impresión
```
Los tres conservan nombre y extensión, así que **ningún vínculo de maquetación
se rompe**, y los tres mueven el original a cuarentena dejando manifiesto.

### Fase 6 — Organización de multimedia
`scripts/organizar_multimedia.py` ordena por año/mes/cámara leyendo metadatos.
Ver `references/metadatos-multimedia.md`.

## Antes de tocar nada, leer

- `references/gotchas-sistemas-archivos.md` — **el más importante**. Trampas que
  pueden hacer que una copia ocupe el triple, o que rompa silenciosamente.
- `references/herramientas.md` — qué trae macOS ya instalado y qué hay que añadir.
  **Comprobar antes de instalar nada**: `sips`, `ditto` y CoreGraphics cubren casi todo.
- `references/archivos-diseno.md` — si hay material de Adobe de por medio.

## Mantenimiento automático (opcional)

Dos agentes de launchd en `~/Library/LaunchAgents`, con los scripts copiados a
`~/Library/Application Support/mac-mantenimiento/`:

- `vigilante_memoria.sh` cada 2 min: avisa si el swap pasa de 3 GB, el disco del
  85 % o el equipo lleva 7 días sin reiniciar. Registro en `~/.mac-mantenimiento-vigilante.log`.
- `limpieza_mensual.sh` el día 1 a las 11:00: copias de Chrome (`code_sign_clone`)
  y perfiles temporales sin ventana de más de 7 días que no estén en uso, cachés de
  npm/composer/uv, registros de más de 30 días y, si hay Xcode, DerivedData viejo y
  simuladores no disponibles. Solo toca lo que se regenera. Registro en
  `~/.mac-mantenimiento-limpieza.log`.

Desactivar: `launchctl bootout gui/$(id -u)/com.mac-mantenimiento.<vigilante|limpieza>`.

## Advertencias generales

- Las operaciones de borrado masivo pueden estar bloqueadas por los clasificadores
  de seguridad del agente. Es esperado: preparar carpetas de cuarentena y que la
  persona las vacíe desde el Finder.
- Usar `taskpolicy -b` para trabajo pesado de E/S; cede prioridad al usuario.
- En discos mecánicos, hashear decenas de GB lleva de 20 a 60 minutos. Avisar del
  tiempo estimado y lanzar en segundo plano.
- Nunca asumir que una carpeta "de respaldo" contiene lo que su nombre dice.
  Verificar siempre por contenido.
