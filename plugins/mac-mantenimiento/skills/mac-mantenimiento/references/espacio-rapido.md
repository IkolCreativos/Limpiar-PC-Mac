# Recuperar espacio: comprobaciones de alto rendimiento

En orden de relación beneficio/esfuerzo.

## 1. La Papelera

```bash
osascript -e 'tell application "Finder" to return (count of items of trash)'
```
Mover a la Papelera **no libera espacio**. Es habitual encontrar decenas de GB
esperando ahí tras una "limpieza" previa. Revisar el contenido antes de vaciar:
puede haber material aún necesario.

## 2. Mapa de ocupación

```bash
du -sh ~/* 2>/dev/null | sort -rh | head -12
du -sh ~/Library/* 2>/dev/null | sort -rh | head -10
du -sh ~/Library/Application\ Support/* 2>/dev/null | sort -rh | head -12
```
Sospechosos frecuentes:
- Copias de seguridad de dispositivos móviles (decenas de GB, a menudo olvidadas)
- Cachés de navegador y de suites de diseño
- Carpetas de proyecto en el Escritorio (además, Spotlight las reindexa)
- Perfiles de máquinas virtuales y contenedores

## 3. Archivos grandes sueltos

```bash
find <dir> -type f -size +500M -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' | sort -rh
```

## 4. Hibernación en equipos de sobremesa

`/private/var/vm/sleepimage` ocupa aproximadamente lo que la RAM instalada y se
reescribe en cada suspensión. En un equipo sin batería no aporta nada.

## 5. Copias de seguridad de móviles

Antes de borrar cualquiera:
- Identificar el dispositivo: leer `Info.plist` del backup (nombre, modelo, fecha).
- **Verificar que exista otra copia.** Buscar en discos externos y en la ubicación
  nativa del sistema.
- Si el dispositivo pertenece a otra persona, es una decisión que no corresponde
  tomar unilateralmente.
- Señal de alerta: si hay copias hechas el mismo día con varias herramientas
  distintas, puede tratarse de una recuperación de datos tras una avería — es
  decir, material potencialmente irrepetible.

## 6. Cachés y registros

`~/Library/Caches` y `~/Library/Logs` pueden acumular varios GB. Las cachés se
regeneran solas. No borrar cachés de aplicaciones abiertas.

## 7. Limitar caché del navegador

Los navegadores basados en Chromium admiten política de tamaño de caché:
```bash
defaults write com.google.Chrome DiskCacheSize -integer 524288000   # 500 MB
```

## Antes de borrar nada

- ¿Existe otra copia verificada? Comprobarlo, no suponerlo.
- ¿Es material de otra persona?
- ¿Se puede regenerar?
- Preferir mover a una carpeta de cuarentena y dejar que la persona vacíe.
