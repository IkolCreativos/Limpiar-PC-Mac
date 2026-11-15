# mantenimiento-equipos

Plugins de Claude Code para mantenimiento, auditoría de almacenamiento y limpieza
segura de equipos. Regla central: **nunca borrar; mover a cuarentena, verificar y
que la persona decida.**

| Plugin | Sistema | Qué hace |
|---|---|---|
| `mac-mantenimiento` | macOS | Diagnóstico de rendimiento, espacio rápido, duplicados por contenido, consolidación entre discos, adelgazado de `.ai`/PDF/PSD, organización de fotos y vídeo |

## Instalar en un Mac

Dentro de Claude Code:

```
/plugin marketplace add IkolCreativos/Limpiar-PC-Mac
/plugin install mac-mantenimiento@mantenimiento-equipos
```

(Sin GitHub: `/plugin marketplace add /ruta/a/esta/carpeta`.)

Después, pedirle a Claude: **"prepara mac-mantenimiento"**. Ejecuta
`scripts/preparar.sh`, que compila las dos utilidades Swift y revisa dependencias.

Requisitos: herramientas de línea de comandos de Apple (`xcode-select --install`)
y, para el Python del sistema, `pillow` y `numpy`. Ghostscript y ffmpeg son
opcionales.

## Usar

Basta con describir el problema; la skill se activa sola:

- "este Mac va lento, diagnostícalo"
- "me falta espacio en disco"
- "busca duplicados entre estas dos carpetas"
- "adelgaza esta carpeta de cliente cerrado"
- "ordena estas fotos por año y mes"

## Actualizar

**Quien mantiene el plugin** (en este repositorio):

1. Editar lo que haga falta en `plugins/mac-mantenimiento/skills/mac-mantenimiento/`.
2. Subir el número de `version` en `plugins/mac-mantenimiento/.claude-plugin/plugin.json`
   (sin subirlo, los demás equipos no ven el cambio).
3. `git add -A && git commit -m "..." && git push`

**En cada Mac que lo usa:**

```
/plugin marketplace update mantenimiento-equipos
/plugin update mac-mantenimiento@mantenimiento-equipos
```

y volver a pedir "prepara mac-mantenimiento" (los binarios compilados no viajan
con la actualización).

## Añadir otro plugin (p. ej. Windows)

1. Crear `plugins/<nombre>/.claude-plugin/plugin.json` y `plugins/<nombre>/skills/<nombre>/SKILL.md`.
2. Añadir su entrada en `.claude-plugin/marketplace.json`.
