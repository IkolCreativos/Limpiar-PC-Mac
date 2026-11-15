# Deduplicación por contenido

## Estrategia de tres pasadas

Hashear todo es inviable: en un disco mecánico, 100 GB son 20–60 minutos de
lectura. La clave es descartar candidatos antes de leer.

1. **Agrupar por tamaño.** Dos archivos idénticos pesan lo mismo. Los tamaños
   únicos se descartan sin leer un solo byte. Suele eliminar el 60–90%.
2. **Hash parcial** (primeros 64 KB) de los que comparten tamaño. Elimina casi
   todos los falsos positivos con una lectura mínima.
3. **Hash completo** solo de los que siguen coincidiendo. Confirmación.

Umbral mínimo: ignorar archivos por debajo de ~8–64 KB salvo que se pida un
barrido exhaustivo. Aportan poco espacio y multiplican el tiempo.

**Al reportar, decir siempre qué umbral se usó.** Si alguien pregunta "¿está
limpio?", repetir sin umbral y dar el número real.

## Qué copia conservar

Por orden de preferencia:

1. La que tenga metadatos íntegros (EXIF de cámara presente).
2. La que esté en la ubicación designada como fuente de verdad.
3. La de ruta más corta o mejor estructurada.
4. Orden alfabético — para que el resultado sea reproducible.

## Método de cuarentena

Nunca borrar. Para cada grupo:
- Conservar una copia según el criterio anterior.
- Mover las sobrantes a `BORRAR-<motivo>/` **preservando la ruta relativa**,
  para que se puedan revisar en contexto y restaurar si hace falta.
- Escribir un CSV: archivo movido, copia conservada, tamaño, hash.

Una carpeta plana con miles de archivos es irrevisable. Con la estructura
original, la persona puede navegarla y juzgar.

## Duplicados legítimos que NO hay que tocar

Algunos archivos deben repetirse por diseño:
- Manifiestos de fuentes que las suites de diseño generan por cada paquete.
- Licencias que acompañan a cada familia tipográfica.
- Recursos enlazados desde documentos de maquetación (ver `archivos-diseno.md`).
- Archivos de 0 bytes: no son duplicados, son archivos corruptos o vacíos.
  Reportarlos aparte.

## Propagar una limpieza a la cuarentena

Si la persona ya descartó originales, sus copias en cuarentena también sobran.
Comparar la lista de supervivientes contra el manifiesto y separar las que
perdieron su original. Es coherente con la decisión ya tomada.

Cuidado con el orden: si la cuarentena se vacía antes de que nadie revise si
algún original borrado debía recuperarse, se pierde la marcha atrás.

## Cruce entre varias ubicaciones

Para N carpetas, indexar todas juntas y etiquetar cada archivo con su ubicación.
El resultado es una matriz de solapamiento:

```
A + B        1.049 grupos   6,2 GB redundantes
A (interno)    305 grupos   441 MB
B (interno)      2 grupos    12 MB
```

De ahí sale el dato que importa: **qué porcentaje de cada carpeta es exclusivo**.
Una carpeta con 0% exclusivo se puede eliminar entera; una con 90% exclusivo no
es un duplicado, es un archivo aparte.

## Verificación obligatoria

Tras cualquier operación:
```
recuento origen == recuento destino
muestra aleatoria de 40–80 hashes MD5, todos coincidentes
```
Y antes de un borrado irreversible: confirmar explícitamente cuántos archivos
desaparecerían para siempre y cuántos están cubiertos en otra copia.
