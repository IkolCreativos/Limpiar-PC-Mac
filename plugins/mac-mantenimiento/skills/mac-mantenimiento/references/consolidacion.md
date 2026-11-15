# Consolidar varias ubicaciones en una fuente de verdad

## Antes de empezar

1. **Inventariar todas las ubicaciones.** Suele aparecer alguna que nadie
   recordaba. Preguntar explícitamente si hay más copias.
2. **Confirmar cuál será la fuente de verdad** y por qué.
3. **Comprobar si alguna está sincronizada con la nube.** Una carpeta de servicio
   de sincronización activa propaga los borrados al servidor:
   ```bash
   ps -Aceo comm | grep -iE "drive|dropbox|onedrive|sync"
   mount | grep -i <servicio>
   ls -a <carpeta> | grep -iE "\.tmp|shortcut-targets|\.icloud"
   ```
   Una carpeta con nombre de servicio de nube puede ser solo una descarga antigua
   y ya no estar sincronizada. Verificarlo antes de borrar.

## Detectar colisiones antes de fusionar

Dos carpetas pueden tener archivos en la **misma ruta relativa** con **contenido
distinto**. Una fusión directa sobrescribe silenciosamente.

```
rutas comunes            : N
  contenido idéntico     : X    ← se pueden saltar
  CONTENIDO DISTINTO     : Y    ← colisión real, decidir cuál gana
```

Para cada colisión, presentar ambas versiones con tamaño, fecha y —si son
documentos de diseño— autonomía de enlaces. Que la persona decida el criterio;
aplicarlo después de forma uniforme.

## Regla de conservación

Definir una prioridad explícita entre ubicaciones y aplicarla a todos los grupos.
Documentarla en el manifiesto para que sea auditable.

Advertencia: si se elige conservar la copia de la ubicación A y borrar la de B,
**la fuente de verdad pasa a ser A**. Si después se decide que la fuente debía
ser B, hay que traer de vuelta lo eliminado — y si la cuarentena ya se vació,
ya no se puede.

Definir la fuente de verdad **antes** de deduplicar, no después.

## Archivos de marcador de nube

Los archivos con extensión `.icloud` y 0 bytes son **punteros a contenido no
descargado**, no archivos reales. Borrar la carpeta hace perder la referencia
aunque el contenido siga en la nube. Antes de decidir sobre una carpeta con
marcadores: conectarse, dejar que se descarguen y volver a evaluar.

## Verificación de la fusión

```
todos los archivos de origen presentes en destino : sí/no
recuento origen == recuento destino               : sí/no
muestra de hashes                                 : N idénticos, 0 distintos
```

Y después: volver a pasar el detector de duplicados sobre el resultado. Fusionar
dos estructuras distintas puede generar duplicados nuevos que no existían en
ninguna de las dos por separado.

## Antes de borrar la última copia redundante

Calcular y comunicar el número exacto:

```
archivos en la carpeta a borrar   : N
ya presentes en la fuente         : X
DESAPARECERÍAN para siempre       : N - X   (Z GB)
```

Si `N - X` es mayor que cero, explicar qué es ese material antes de que se
decida. Y no borrar la única segunda copia de nada hasta que la fuente de verdad
esté respaldada en otro dispositivo físico.
