#!/bin/bash
# limpieza_mensual.sh - Limpia solo lo que se regenera solo. Pensado para launchd.
# Nunca toca documentos, proyectos ni datos de apps: cachés, temporales y registros.
#   - Copias de Chrome (code_sign_clone) de mas de 7 dias que no esten en uso
#   - Perfiles temporales de Chrome sin ventana (motion-*) de mas de 7 dias sin proceso vivo
#   - Cachés de npm, composer y uv; registros de mas de 30 dias en ~/Library/Logs
#   - Xcode (si existe): DerivedData de mas de 30 dias y simuladores no disponibles
# Deja una linea por ejecucion en el log y avisa con una notificacion.
set -u
LOG="${LIMPIEZA_LOG:-$HOME/.mac-mantenimiento-limpieza.log}"
libre(){ df -k /System/Volumes/Data | awk 'NR==2{print $4}'; }
ANTES=$(libre)

T="$(getconf DARWIN_USER_TEMP_DIR)"; BASE="$(dirname "$T")"
EN_USO="$(lsof -c Google -Fn 2>/dev/null | sed -n 's/^n//p')"
usado(){ printf '%s\n' "$EN_USO" | grep -qF "$1/"; }

# 1. Copias de Chrome
CL="$BASE/X/com.google.Chrome.code_sign_clone"
if [ -d "$CL" ]; then
  find "$CL" -mindepth 1 -maxdepth 1 -name 'code_sign_clone.*' -mtime +7 | while read -r d; do
    usado "$d" || rm -rf "$d"
  done
fi

# 2. Perfiles temporales de Chrome sin ventana
find "$T" -mindepth 1 -maxdepth 1 -type d -name 'motion-*' -mtime +7 2>/dev/null | while read -r d; do
  pgrep -f "$(basename "$d")" >/dev/null || usado "$d" || rm -rf "$d"
done

# 3. Cachés de herramientas de desarrollo (se regeneran al instalar)
rm -rf "$HOME/.npm/_cacache" "$HOME/Library/Caches/composer" "$HOME/.cache/uv" \
       "$HOME/Library/Caches/node-gyp" "$HOME/Library/Caches/Homebrew" 2>/dev/null

# 4. Registros viejos
find "$HOME/Library/Logs" -type f -mtime +30 -delete 2>/dev/null

# 5. Xcode, solo si esta instalado
DD="$HOME/Library/Developer/Xcode/DerivedData"
[ -d "$DD" ] && find "$DD" -mindepth 1 -maxdepth 1 -mtime +30 -exec rm -rf {} + 2>/dev/null
[ -d /Applications/Xcode.app ] && xcrun simctl delete unavailable >/dev/null 2>&1

DESPUES=$(libre)
MB=$(( (DESPUES - ANTES) / 1024 )); [ "$MB" -lt 0 ] && MB=0
GB_LIBRES=$(( DESPUES / 1048576 ))
echo "$(date '+%F %H:%M') liberados=${MB}MB libres=${GB_LIBRES}GB" >> "$LOG"
osascript -e "display notification \"Liberados ${MB} MB. Quedan ${GB_LIBRES} GB libres.\" with title \"Limpieza mensual del Mac\"" 2>/dev/null
exit 0
