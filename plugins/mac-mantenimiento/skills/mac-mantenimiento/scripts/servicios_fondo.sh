#!/bin/bash
# Inventaria los agentes y demonios de terceros que arrancan solos.
# Solo lista y explica: NO desactiva nada automaticamente.
# Uso: servicios_fondo.sh [listar|desactivar <etiqueta>|reactivar <etiqueta>]
set -uo pipefail
UA="$HOME/Library/LaunchAgents"; LA="/Library/LaunchAgents"; LD="/Library/LaunchDaemons"

listar() {
  printf "%-56s %-10s %s\n" "ARCHIVO" "ESTADO" "AMBITO"
  printf '%.0s-' {1..86}; echo
  for dir in "$UA" "$LA" "$LD"; do
    amb=$([ "$dir" = "$UA" ] && echo "usuario" || { [ "$dir" = "$LA" ] && echo "sistema" || echo "demonio"; })
    for f in "$dir"/*.plist "$dir"/*.plist.disabled; do
      [ -e "$f" ] || continue
      b=$(basename "$f")
      case "$b" in com.apple.*) continue;; esac     # omitir los del sistema
      est=$([ "${b##*.}" = "disabled" ] && echo "desactivado" || echo "activo")
      printf "%-56s %-10s %s\n" "${b%.disabled}" "$est" "$amb"
    done
  done
  cat <<'NOTA'

CLASIFICACION ORIENTATIVA
  actualizadores de navegador/ofimatica  desactivar implica actualizar a mano
                                         (son parches de seguridad: avisar)
  asistentes de suites de diseño         prescindibles; la app funciona igual
  sincronizadores de nube                NO tocar sin preguntar: pueden estar
                                         sirviendo carpetas activas
  controladores de periferico            NO tocar (tabletas graficas, impresoras)
  motores de contenedores/VM             solo si no se usan

IMPACTO REAL: unos cientos de MB. Es la palanca MAS PEQUEÑA del mantenimiento.
No presentarla como solucion si el problema de fondo es falta de memoria.
NOTA
}

case "${1:-listar}" in
  listar) listar;;
  desactivar)
    f="${2:?falta la ruta del plist}"
    sudo launchctl bootout system "$f" 2>/dev/null
    launchctl unload -w "$f" 2>/dev/null
    sudo mv "$f" "$f.disabled" 2>/dev/null || mv "$f" "$f.disabled"
    echo "desactivado: $f  (reversible con 'reactivar')";;
  reactivar)
    f="${2:?falta la ruta del plist (sin .disabled)}"
    sudo mv "$f.disabled" "$f" 2>/dev/null || mv "$f.disabled" "$f"
    launchctl load -w "$f" 2>/dev/null || sudo launchctl load -w "$f" 2>/dev/null
    echo "reactivado: $f";;
  *) echo "Uso: $0 listar|desactivar <plist>|reactivar <plist>"; exit 1;;
esac
