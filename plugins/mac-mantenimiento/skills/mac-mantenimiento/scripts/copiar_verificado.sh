#!/bin/bash
# Copia carpetas a un destino y VERIFICA el recuento. Nunca borra el origen.
# Uso: copiar_verificado.sh <destino> <log> <origen1> [origen2 ...]
set -uo pipefail
DEST="$1"; LOG="$2"; shift 2
: > "$LOG"
for O in "$@"; do
  [ -d "$O" ] || { echo "no existe: $O" >> "$LOG"; continue; }
  N=$(basename "$O")
  echo "[$(date '+%F %H:%M')] COPIANDO  $N" >> "$LOG"
  ditto "$O" "$DEST/$N" 2>>"$LOG"          # ditto preserva metadatos y hardlinks
  co=$(find "$O" -type f -not -name '._*' -not -name '.DS_Store' 2>/dev/null | wc -l | tr -d ' ')
  cd_=$(find "$DEST/$N" -type f -not -name '._*' -not -name '.DS_Store' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$co" = "$cd_" ] && [ "$co" -gt 0 ]; then
    echo "[$(date '+%F %H:%M')] OK        $N  ($co archivos)" >> "$LOG"
  else
    echo "[$(date '+%F %H:%M')] REVISAR   $N  (origen $co / destino $cd_)" >> "$LOG"
  fi
done
echo "FIN" >> "$LOG"
