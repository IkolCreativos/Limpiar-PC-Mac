# Material de diseño gráfico: cuidados específicos

Los archivos de suites de maquetación e ilustración tienen dependencias que no se
ven en el sistema de archivos. Borrar por tamaño o por nombre rompe documentos.

## Paquetes de maquetación

Al empaquetar un documento, la aplicación genera una carpeta con:

```
NombreProyecto/
   documento.indd
   Links/              ← imágenes vinculadas
   Document fonts/     ← tipografías usadas
```

**La carpeta de enlaces no es una copia por descuido: es el mecanismo que hace
el paquete autónomo.** Existe para que el trabajo se pueda reabrir años después.

Implicaciones para deduplicar:
- Una imagen dentro de `Links/` que también está en otra carpeta **no sobra**.
  Borrarla rompe el documento.
- Salvo que la persona indique explícitamente que se trata de material de archivo
  y que acepta perder los vínculos.

**Carpetas de enlaces huérfanas** (sin documento al lado, ni en carpetas
próximas) sí son candidatas: no hay documento que romper. Buscar el documento en
la carpeta padre y en las inmediatas antes de concluir que está huérfana.

## Trampa del reenlazado por nombre

Las aplicaciones de maquetación reenlazan **por nombre de archivo**. Si en un
archivo hay copias idénticas con nombres distintos —la misma foto guardada como
`Enero.tif` y como `foto-original-130.tif`— y se deduplica conservando una sola,
los documentos que buscaban el otro nombre ya no la encuentran.

Consecuencia: **no se puede deduplicar por contenido y mantener el reenlazado
automático a la vez.** Decidir cuál importa más antes de actuar.

## Compatibilidad PDF en archivos de ilustración

Un archivo de ilustración se puede guardar con o sin capa de compatibilidad PDF:

| | Con compatibilidad PDF | Sin ella (aplanado) |
|---|---|---|
| Tamaño | grande | muy pequeño |
| Autonomía | se abre siempre completo | depende de los enlaces externos |
| Vista previa | sí | no |

Diferencias de tamaño de 10x o más entre dos versiones del mismo documento suelen
responder a esto, no a pérdida de contenido.

**Cómo comprobarlo:**
```bash
strings -n 8 <archivo> | grep -c "AIPrivateData"          # datos nativos presentes
strings -n 6 <archivo> | grep -m1 "CreatorTool"           # versión que lo guardó
strings -n 8 <archivo> | grep -cE "\.tif|\.psd|\.jpg"     # referencias a enlaces
```

**Aviso metodológico:** contar streams de imagen o páginas con herramientas de
PDF mide **solo la capa de compatibilidad**. En un archivo aplanado esa capa no
existe, y el recuento sale bajo sin que falte contenido. No sirve como prueba
de pérdida de datos.

**La comprobación que sí vale:** extraer las rutas de los enlaces que el archivo
referencia y verificar si existen.

```bash
strings -n 8 <archivo> | grep -oE "[A-Za-z0-9_ ./-]+\.(tif|psd|jpg|png)" | sort -u
```

Si un archivo aplanado referencia imágenes que ya no están en ningún sitio, es
inservible aunque pese poco. En ese caso la versión grande y autónoma es la
buena, por mucho que parezca "hinchada".

### Trampa del render en blanco: comparar vacío contra vacío

Al reescribir un archivo de ilustración para soltar los datos nativos y quedarse
con la capa PDF, **verificar comparando el render de antes y el de después no
basta**. Si el archivo se guardó *sin* compatibilidad PDF, su capa PDF es un
sello vacío: el motor del sistema lo renderiza en blanco tanto antes como
después. La diferencia sale cero y la comprobación da por bueno un archivo al
que se le ha quitado todo el contenido.

Un caso real: 38 de 791 archivos pasaron la comparación visual con diferencia
0,000 y quedaron reducidos de 1,4 MB a 852 bytes. Eran logos, mapas e
iconografía guardados sin compatibilidad.

**La comprobación que sí vale, en dos partes:**
```bash
# 1. ¿el render tiene contenido? (desviacion tipica casi nula = en blanco)
sips -s format png -Z 200 <archivo> --out /tmp/x.png
python3 -c "from PIL import Image;import numpy as np;print(np.asarray(Image.open('/tmp/x.png').convert('RGB'),float).std())"

# 2. ¿el resultado conserva datos nativos o solo la capa PDF?
strings -n 8 <archivo> | grep -c AIPrivateData
```
**Si el original renderiza en blanco, no reescribir: todo su contenido está en
los datos nativos.** Un archivo que el sistema no sabe dibujar es justamente el
que hay que dejar intacto.

Corolario general: una verificación que compara origen y destino solo es válida
si se confirma antes que el origen produce una señal no trivial. Comparar dos
vacíos siempre da idéntico.

## Al consolidar versiones de un mismo documento

- **Las fechas de modificación mienten** si hubo una copia masiva: todos los
  archivos aparecen con la fecha de la copia. Detectar el patrón (muchos archivos
  con fecha idéntica) antes de usar la fecha como criterio.
- Comparar por contenido y por autonomía, no por fecha ni por tamaño.
- Al resolver un conflicto, **conservar la versión descartada** en una carpeta
  aparte. Nunca sobrescribir directamente.
