#!/bin/bash
# Avisa cuando la presion de memoria o la ocupacion de disco cruzan un umbral.
# Pensado para ejecutarse periodicamente via launchd. No mata procesos: informa.
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="${VIGILANTE_LOG:-$HOME/.mac-mantenimiento-vigilante.log}"
SILENCIO="${LOG}.ultimo"
UMBRAL_SWAP_MB="${UMBRAL_SWAP_MB:-3072}"
UMBRAL_DISCO_PCT="${UMBRAL_DISCO_PCT:-85}"
ESPERA="${ESPERA_AVISO:-1800}"

SWAP=$(sysctl -n vm.swapusage | sed 's/.*used = \([0-9.]*\)M.*/\1/' | cut -d. -f1)
DISCO=$(df /System/Volumes/Data | awk 'NR==2{gsub("%","",$5); print $5}')
TOP=$(ps -Aceo rss,comm -m | awk 'NR==2{printf "%s (%.1f GB)", substr($0,index($0,$2)), $1/1048576}')

AVISO=""
[ "${SWAP:-0}" -gt "$UMBRAL_SWAP_MB" ] && AVISO="Memoria al limite: ${SWAP} MB en swap. Mayor consumo: ${TOP}."
[ "${DISCO:-0}" -ge "$UMBRAL_DISCO_PCT" ] && AVISO="${AVISO} Disco al ${DISCO}%."

echo "$(date '+%F %H:%M') swap=${SWAP}MB disco=${DISCO}% top=${TOP}" >> "$LOG"
tail -n 2000 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"

if [ -n "$AVISO" ]; then
  AHORA=$(date +%s); ULT=0; [ -f "$SILENCIO" ] && ULT=$(cat "$SILENCIO")
  if [ $((AHORA - ULT)) -gt "$ESPERA" ]; then
    echo "$AHORA" > "$SILENCIO"
    osascript -e "display notification \"$AVISO\" with title \"Rendimiento del Mac\"" 2>/dev/null
  fi
fi
