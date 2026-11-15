# Trampas de sistemas de archivos en macOS

Cada una de estas provocó un error real o casi lo provoca. Comprobarlas **antes**
de mover datos, no después.

---

## 1. Tamaño de clúster en ExFAT: inflación de hasta 3x

**Síntoma:** una copia a un disco externo ocupa el triple que el origen.

**Causa:** ExFAT en discos grandes suele formatearse con clústeres de 128–256 KB.
Cada archivo, aunque pese 1 byte, consume un clúster entero. Con cientos de miles
de archivos pequeños (`node_modules`, cachés, paquetes de diseño, archivos
AppleDouble) el desperdicio se dispara.

**Cómo detectarlo antes de copiar:**
```bash
printf 'x' > /Volumes/DISCO/.test
stat -f "%b" /Volumes/DISCO/.test   # bloques de 512 B
# bloques*512 = tamaño real de clúster. 512 KB de salida = clúster de 256 KB
rm /Volumes/DISCO/.test
```
`diskutil info` reporta "Allocation Block Size: 512 Bytes" y **miente**: ese es el
tamaño de bloque del dispositivo, no el clúster del sistema de archivos.

**Solución:** crear una imagen de disco APFS dentro del volumen ExFAT.
```bash
hdiutil create -type SPARSEBUNDLE -fs APFS -size <N>g \
  -volname "NOMBRE" -imagekey sparse-band-size=16384 /Volumes/DISCO/archivo.sparsebundle
hdiutil attach /Volumes/DISCO/archivo.sparsebundle
```
APFS usa bloques de 4 KB: mejora de 64x en archivos pequeños, y además preserva
metadatos nativos de macOS sin generar archivos `._*`.

---

## 2. Enlaces duros (hardlinks) que ExFAT no puede representar

**Dónde aparecen:** copias de seguridad incrementales de dispositivos móviles y
herramientas de respaldo que comparten inodos entre versiones.

**Detección:**
```bash
find <carpeta> -type f -print0 | xargs -0 stat -f "%l" | sort | uniq -c
# un recuento alto de "2" o más indica hardlinks
```
Confirmación cruzada: `du -shc carpetaA carpetaB` — si la suma acumulada es menor
que la suma individual, comparten inodos.

**Consecuencia:** copiar a ExFAT duplica los datos (el tamaño puede doblarse) y
rompe la estructura que la aplicación de origen espera encontrar.

**Solución:** imagen APFS (ver punto 1) y copiar con `ditto`, que preserva
hardlinks. `cp -R` **no** los preserva.

---

## 3. `du` frente a tamaño lógico: preasignación en imágenes de disco

**Síntoma:** el mismo contenido pesa ~1 GB más dentro de una imagen de disco.

**Causa:** al escribir archivos grandes (vídeo) en un sparsebundle, APFS preasigna
bloques en incrementos de ~16 MB para evitar fragmentación, y no siempre los
devuelve.

**Cómo distinguir sobrecarga de pérdida de datos:**
```python
st = os.lstat(p)
st.st_size          # tamaño lógico — DEBE coincidir entre origen y destino
st.st_blocks * 512  # ocupación real — puede diferir legítimamente
```
Si el tamaño lógico coincide y los hashes coinciden, la copia es correcta. La
diferencia de ocupación es contabilidad del sistema de archivos.

---

## 4. Espacios duros (U+00A0) en nombres de carpeta

**Síntoma:** un filtro por nombre no encuentra carpetas que existen visiblemente.

**Causa:** algunas exportaciones generan nombres con espacio de no separación
(`\xa0`) en lugar de espacio normal. Visualmente idénticos.

**Solución:** normalizar siempre antes de comparar.
```python
import re
norm = lambda s: re.sub(r'\s+', ' ', s.replace('\xa0', ' ')).strip().lower()
```

---

## 5. Normalización Unicode NFD en nombres de archivo

**Síntoma:** un patrón de shell con acentos no coincide con archivos que existen.

**Causa:** macOS almacena nombres en NFD (descompuesto): "ó" se guarda como
"o" + acento combinante. Un patrón escrito en NFC no coincide.

**Solución:** dejar que Python descubra las rutas (`os.listdir`) en vez de pasar
patrones desde el shell. Para comparar, usar `unicodedata.normalize('NFC', s)`.

---

## 6. `xargs` y rutas con espacios

Cualquier ruta con espacios rompe un pipe `find | xargs`. Usar siempre:
```bash
find <dir> -type f -print0 | xargs -0 <comando>
```
En bucles de shell, `while IFS= read -r f` y comillas en todas las variables.
En bucles con `basename`/`dirname`, entrecomillar o el nombre se parte.

---

## 7. El Terminal sin Acceso Total al Disco

**Síntoma:** `ls ~/.Trash` devuelve "Operation not permitted" y los conteos salen a cero.

**Causa:** TCC de macOS. Afecta a la Papelera, Mail, Mensajes, Fotos y más.

**Alternativa sin cambiar permisos:** consultar mediante Finder.
```bash
osascript -e 'tell application "Finder" to return (count of items of trash)'
```
Ojo: `it` es palabra reservada en AppleScript; nombrar la variable de otro modo.

---

## 8. Imágenes montadas con `nobrowse` son invisibles en el Finder

Si se monta con `hdiutil attach -nobrowse`, el volumen funciona en terminal pero
**no aparece en el Finder**, y la persona no podrá usarlo. Montar sin esa opción
cuando el usuario vaya a interactuar con el contenido.

Comprobar: `mount | grep nobrowse`

---

## 9. La Papelera no libera espacio

Mover a la Papelera es un renombrado dentro del mismo volumen. El espacio no se
recupera hasta vaciarla. Un usuario puede haber "limpiado" decenas de GB sin ver
ninguna mejora. **Comprobarlo siempre al principio de una auditoría.**

Cada volumen externo tiene además su propia `.Trashes`.

---

## 10. Umbral crítico de ocupación en Fusion Drive

Un Fusion Drive necesita margen libre para promover bloques calientes al SSD.
Por encima del ~85% de ocupación el escalonado deja de funcionar y el rendimiento
se desploma. Objetivo: mantenerlo **por debajo del 80%**.

---

## 11. Directorios "no vacíos" que están vacíos (ExFAT)

Tras interrumpir una copia, ExFAT puede dejar entradas de directorio inconsistentes:
`ls` no muestra nada pero `rm -rf` falla con "Directory not empty".

**Solución:** `rmdir` directo sobre la ruta; después `diskutil verifyVolume`.
Nota: la verificación necesita desmontar, así que hay que soltar antes cualquier
imagen de disco alojada en ese volumen.

---

## 12. Flags BSD que impiden borrar

Un archivo con el flag `uchg` (bloqueado) resiste a `rm`. Detectar con `ls -lO`
y limpiar con `chflags nouchg <ruta>`. `chflags -R` sobre el padre no siempre
alcanza a todos los hijos en volúmenes no nativos.
