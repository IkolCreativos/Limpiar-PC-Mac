#!/bin/bash
# preparar.sh - Deja la skill lista en este Mac: compila las utilidades Swift
# y comprueba las dependencias. Se puede ejecutar las veces que haga falta.
# No instala nada por su cuenta: solo compila y avisa de lo que falta.
set -u
cd "$(dirname "$0")" || exit 1
ok(){ printf '  \033[32mOK\033[0m     %s\n' "$1"; }
falta(){ printf '  \033[31mFALTA\033[0m  %s\n         -> %s\n' "$1" "$2"; FALLOS=$((FALLOS+1)); }
opc(){ printf '  \033[33mOPCIONAL\033[0m %s\n         -> %s\n' "$1" "$2"; }
FALLOS=0

[ "$(uname)" = "Darwin" ] || { echo "Este plugin es solo para macOS."; exit 1; }
echo "== Preparando mac-mantenimiento ($(sw_vers -productVersion), $(uname -m)) =="

echo "Utilidades Swift:"
if command -v swiftc >/dev/null 2>&1 && swiftc --version >/dev/null 2>&1; then
  for u in airewrite pdfpaginas; do
    if [ -x "$u" ] && [ "$u" -nt "$u.swift" ]; then ok "$u (ya compilado)"
    elif swiftc -O -o "$u" "$u.swift" 2>/tmp/preparar_$u.log; then ok "$u compilado"
    else falta "$u no compila" "ver /tmp/preparar_$u.log"; fi
  done
else
  falta "swiftc" "instalar las herramientas de Apple:  xcode-select --install"
fi

echo "Herramientas del sistema:"
for t in sips ditto taskpolicy mdutil hdiutil; do
  command -v $t >/dev/null 2>&1 && ok "$t" || falta "$t" "deberia venir con macOS"
done

echo "Python del sistema (/usr/bin/python3):"
if /usr/bin/python3 -c "import PIL, numpy" 2>/dev/null; then
  ok "PIL y numpy"
else
  falta "PIL / numpy" "/usr/bin/python3 -m pip install --user pillow numpy"
fi

echo "Opcionales:"
command -v gs >/dev/null 2>&1 && ok "ghostscript (reducir_incrustadas.py)" \
  || opc "ghostscript" "solo para reducir_incrustadas.py:  brew install ghostscript"
command -v ffprobe >/dev/null 2>&1 && ok "ffprobe (fechas de video)" \
  || opc "ffprobe" "solo para organizar video por fecha:  brew install ffmpeg"

echo
if [ $FALLOS -eq 0 ]; then echo "Listo."; else echo "Faltan $FALLOS requisitos (ver arriba)."; exit 1; fi
