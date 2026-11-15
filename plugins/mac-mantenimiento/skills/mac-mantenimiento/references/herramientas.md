# Herramientas: qué usar, qué trae macOS y qué hay que instalar

Inventario de lo que realmente hace falta para este trabajo. La mayoría ya está
en el sistema: **comprobar antes de instalar nada.**

```bash
for t in sips ditto taskpolicy swiftc ffmpeg gs magick qpdf exiftool mutool; do
  printf "%-10s " "$t"; command -v "$t" >/dev/null && echo OK || echo "NO DISPONIBLE"
done
/usr/bin/python3 -c "import PIL, numpy; print('PIL', PIL.__version__, '· numpy', numpy.__version__)"
```

---

## Nativas de macOS

### `sips` — el caballo de batalla para imágenes
Lee y convierte **incluido PSD**, sin instalar nada. También abre `.ai` y PDF
(los ve como PDF).

```bash
sips -g pixelWidth -g pixelHeight -g format <archivo>   # inspeccionar
sips -s format jpeg -s formatOptions 90 in.psd --out out.jpg
sips -s format psd -Z 3508 in.psd --out out.psd          # aplanar + reducir
sips -s format png -Z 200 in.ai --out /tmp/x.png         # render para verificar
```
`-Z N` limita el **lado mayor** conservando proporción. `-z alto ancho` deforma.

**Trampa:** al escribir PSD desde un origen con canal alfa, `sips` **premultiplica
el RGB por el alfa**. El fondo transparente se vuelve negro y la imagen colocada
sobre claro sale oscurecida. Detectarlo comparando renders; esos archivos no se
pueden procesar con `sips`.

### `ditto` — copiar sin perder nada
```bash
ditto <origen> <destino>
```
Preserva metadatos de macOS, recursos y **enlaces duros**. `cp -R` no los preserva.
Es la copia correcta para respaldos.

### `stat` — ocupación real frente a tamaño lógico
```bash
stat -f "%z" <archivo>    # tamaño logico: DEBE coincidir entre origen y destino
stat -f "%b" <archivo>    # bloques de 512 B: puede diferir legitimamente
stat -f "%l" <archivo>    # numero de enlaces: >1 indica hardlink
```
El lógico es el que prueba que una copia es correcta. La ocupación varía por
preasignación y tamaño de clúster; ver `gotchas-sistemas-archivos.md`.

### `taskpolicy -b` — trabajo pesado sin bloquear a la persona
```bash
taskpolicy -b <comando>
```
Ejecuta en segundo plano cediendo prioridad de E/S. Imprescindible en lotes
largos: la persona puede seguir trabajando.

### `strings` — mirar dentro de archivos binarios
```bash
strings -n 8 <archivo> | grep -c AIPrivateData    # datos nativos de Illustrator
strings -n 6 <archivo> | grep -m1 CreatorTool     # con qué se guardó
```

### `swiftc` + CoreGraphics — reescribir PDF y `.ai` sin instalar nada
Cuando no hay Ghostscript, `CGPDFDocument` + `CGContext(consumer:mediaBox:)`
reescribe un PDF conservando vectores y soltando los datos privados de la
aplicación de origen. Compilar una utilidad de 20 líneas es más rápido que
instalar una suite.

**Esto no recomprime las imágenes incrustadas**: si el peso son fotos dentro del
archivo, la reescritura no gana nada. Para eso hace falta Ghostscript.

### Diagnóstico
```bash
sysctl vm.swapusage        # uso de swap
memory_pressure            # porcentaje de memoria libre
diskutil verifyVolume <v>  # integridad tras una desconexion brusca
diskutil list              # que discos ve el sistema
mount | grep -i <nombre>   # si /Volumes/X es montaje real o carpeta huerfana
```

---

## Python (viene con las Command Line Tools)

Invocarlo siempre como **`/usr/bin/python3`**: si Homebrew ha instalado el suyo,
`python3` a secas apunta a uno sin PIL ni numpy.

```python
from PIL import Image        # lee PSD, JPEG, PNG, TIFF
import numpy as np           # diferencia media entre dos renders
import struct                # cabecera PSD: dimensiones, canales, modo, capas
import hashlib, csv, os
```

**Cabecera PSD sin abrir Photoshop** — dice si un PSD lleva alfa y cuántas capas:
```python
with open(p,'rb') as f:
    h=f.read(26)
    canales,alto,ancho,bits,modo = struct.unpack('>HIIHH', h[12:26])
    # modo: 3=RGB, 4=CMYK.  canales 4 en modo RGB = hay canal alfa
```
Saltando las secciones de modo de color y recursos se llega a la de capas, cuyo
tamaño revela qué porcentaje del archivo es retoque y cuánto el composite plano.

**Comparar dos versiones visualmente:**
```python
a=np.asarray(Image.open(x).convert('RGB'),float)
b=np.asarray(Image.open(y).convert('RGB'),float)
dif = np.abs(a-b).mean()      # sobre 255
```
Umbral orientativo: `<1` reescritura de vectores, `<6` reducción de resolución.

---

## Hay que instalarlas

### Ghostscript — recomprimir imágenes **dentro** de un PDF o `.ai`
```bash
brew install ghostscript
```
Es la única forma de reducir las fotos incrustadas **conservando los vectores
como vectores**. La alternativa —rasterizar el archivo entero— convierte el texto
en píxeles y no debe ofrecerse como equivalente.

```bash
gs -sDEVICE=pdfwrite -dNOPAUSE -dBATCH -dQUIET \
   -dDownsampleColorImages=true -dColorImageResolution=300 \
   -dColorImageDownsampleType=/Bicubic \
   -dDownsampleGrayImages=true  -dGrayImageResolution=300 \
   -dGrayImageDownsampleType=/Bicubic \
   -dAutoFilterColorImages=false -dColorImageFilter=/DCTEncode \
   -sOutputFile=salida.pdf entrada.ai
```

**Usar 300 dpi, no 200.** Medido sobre material real: bajar de 300 a 200 dpi
ahorra un 20% adicional sobre un archivo que ya se redujo 80x, y a cambio
ablanda visiblemente la textura fotográfica. No compensa.

El texto y los trazos salen **idénticos píxel a píxel**: Ghostscript solo toca
los flujos de imagen. Un archivo que apenas cambie entre 200 y 300 dpi tiene sus
imágenes ya por debajo de esa resolución; ahí el peso es otra cosa y no hay nada
que exprimir.

**Efecto colateral de instalarlo:** la fórmula arrastra `tesseract`, `cairo` y
**Python de Homebrew**, que pasa a eclipsar al Python del sistema en el `PATH`.
El de Homebrew no trae PIL ni numpy, así que los scripts de verificación dejan de
funcionar de golpe. Solución: invocar **`/usr/bin/python3`** por ruta explícita en
todo script de mantenimiento, nunca `python3` a secas.

Sin binario precompilado compila desde fuente: contar con una hora larga.

### No estaban y no hicieron falta
`ImageMagick`, `qpdf`, `exiftool`, `pdftoppm`, `mutool`. Todo lo que se necesitó
de ellas lo cubrieron `sips`, PIL y CoreGraphics. Comprobar siempre antes de
añadir dependencias.

---

## Regla de verificación que gobierna el uso de todas ellas

Una comparación entre origen y destino **solo vale si el origen produce una señal
no trivial**. Antes de dar por buena una transformación verificada por parecido
visual, confirmar que el original renderiza algo: comparar dos vacíos siempre da
idéntico. El caso completo está en `archivos-diseno.md`.
