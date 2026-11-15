# Lectura de metadatos en fotos y vídeo

## Qué herramienta usar según el formato

| Formato | Herramienta | Por qué |
|---|---|---|
| JPEG | parser EXIF propio o `sips` | EXIF en segmento APP1, fácil de leer |
| **HEIC** | **`sips`** | contenedor ISOBMFF: un parser de JPEG **no funciona** |
| PNG | `sips` | rara vez lleva fecha de captura |
| MOV / MP4 | **`ffprobe`** | fecha en `format_tags=creation_time` |

```bash
sips -g creation -g make -g model <archivo>
ffprobe -v quiet -show_entries format_tags=creation_time,com.apple.quicktime.model \
        -of default=nw=1 <archivo>
```

## Trampas

**Un lector de EXIF para JPEG devuelve cero en HEIC.** Si el material viene de
iPhone reciente, la mayoría será HEIC. Comprobar la tasa de acierto sobre una
muestra antes de procesar miles de archivos.

**`mdls` devuelve la fecha equivocada en vídeo.** `kMDItemContentCreationDate`
puede reflejar la fecha del sistema de archivos, no la de captura. Diferencias de
años. Usar `ffprobe` para vídeo.

**`sips` devuelve el literal `<nil>`** cuando falta un campo. Sin filtrarlo se
crea una carpeta llamada "nil". Mapear `<nil>`, `nil` y cadena vacía a un valor
propio de "desconocido".

**Coste.** `sips` y `ffprobe` lanzan un proceso por archivo (~30 ms). Aceptable
hasta unos pocos miles; por encima, avisar del tiempo.

## Relojes de cámara sin configurar

Concentraciones anómalas —cientos de fotos en enero de un año antiguo— suelen
indicar una cámara cuyo reloj nunca se puso en hora: estampa su fecha de fábrica.

No es un error del proceso. Reportarlo y dejar que la persona decida si renombra
esa carpeta, porque solo ella sabe de cuándo son realmente.

## Fotos recuperadas tras un formateo

Las herramientas de recuperación de datos producen un patrón reconocible:

- Nombres tipo `J<ancho>x<alto>-<secuencia>.jpg`: el nombre original se perdió.
- Carpetas `JPEG1`, `JPEG2`… `JPEGn`: orden de escritura del recuperador, **sin
  significado**. No merece la pena preservarlas.
- Duplicación masiva: el mismo archivo aparece varias veces porque existía en
  varios sitios del disco. Es normal encontrar que la mitad son copias.
- El EXIF **sí sobrevive dentro del archivo**, aunque el sistema de archivos haya
  perdido las fechas. Esa es la vía para reconstruir el orden cronológico.

## Separar material personal de descargado

Presencia de EXIF de cámara como heurística:
- **Con marca/modelo**: fotografía tomada con un dispositivo.
- **Sin EXIF**: probablemente descarga, gráfico o captura de pantalla.

**Advertencia importante:** ausencia de EXIF **no implica** que no sea personal.
Una foto propia pierde el EXIF al pasar por mensajería, al recortarla en un editor
o al descargarla de una red social. Presentarlo como indicio para revisar, nunca
como criterio de borrado automático.

Complementar con el ancho en píxeles: por debajo de ~640 px suele ser miniatura
o gráfico web.

## Esquema de organización recomendado

```
AÑO / MES / CÁMARA        cuando hay volumen suficiente
AÑO / MES                 en conjuntos pequeños
sin-fecha/                para lo que no tenga metadatos
```

Agrupar en "otras-camaras" los modelos con pocas fotos: con umbral 15–20 se evita
generar decenas de carpetas de un solo archivo. Si anidar por cámara produce más
carpetas de 1–2 archivos que carpetas útiles, no anidar.

## Carpetas temáticas: no reorganizar sin preguntar

Si existen carpetas nombradas por persona, evento o proyecto, contienen
**información que no está en los metadatos**. Reorganizarlas por fecha destruye
ese criterio de forma irreversible.

Opción recomendada: organizar cronológicamente **dentro** de cada carpeta
temática, conservando el grupo.
