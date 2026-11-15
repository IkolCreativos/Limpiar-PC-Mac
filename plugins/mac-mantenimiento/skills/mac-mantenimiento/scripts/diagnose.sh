#!/bin/bash
# diagnose.sh - Radiografía rápida del estado del iMac. Solo lectura.
C_R=$'\e[31m'; C_Y=$'\e[33m'; C_G=$'\e[32m'; C_B=$'\e[1m'; C_0=$'\e[0m'
bar(){ local p=$1 w=28 f; f=$((p*w/100)); printf '['; printf '%0.s#' $(seq 1 $f 2>/dev/null); printf '%0.s.' $(seq 1 $((w-f)) 2>/dev/null); printf '] %s%%' "$p"; }
echo "${C_B}== ESTADO DEL SISTEMA  $(date '+%F %H:%M') ==${C_0}"
echo

# --- Memoria ---
PS=$(vm_stat | head -1 | grep -o '[0-9]*')
eval $(vm_stat | sed 's/\.//' | awk -F: '/Pages free/{print "FREE="$2}/Pages active/{print "ACT="$2}/Pages inactive/{print "INA="$2}/Pages wired/{print "WIR="$2}/Pages occupied by compressor/{print "CMP="$2}' | tr -d ' ')
TOTAL=$(( $(sysctl -n hw.memsize) / 1048576 ))
USED=$(( (ACT + WIR + CMP) * PS / 1048576 ))
MPCT=$(( USED * 100 / TOTAL ))
SWU=$(sysctl -n vm.swapusage | sed 's/.*used = \([0-9.]*\)M.*/\1/' | cut -d. -f1)
printf "RAM    %s  %s/%s MB\n" "$(bar $MPCT)" "$USED" "$TOTAL"
if [ "$SWU" -gt 2048 ]; then CS=$C_R; elif [ "$SWU" -gt 512 ]; then CS=$C_Y; else CS=$C_G; fi
printf "SWAP   ${CS}%s MB en uso${C_0}" "$SWU"
[ "$SWU" -gt 2048 ] && printf "  <-- el disco está haciendo de RAM, ahí se va la fluidez"
echo; echo

# --- Disco ---
DPCT=$(df /System/Volumes/Data | awk 'NR==2{gsub("%","",$5); print $5}')
DAV=$(df -h /System/Volumes/Data | awk 'NR==2{print $4}')
if [ "$DPCT" -ge 85 ]; then CD=$C_R; elif [ "$DPCT" -ge 75 ]; then CD=$C_Y; else CD=$C_G; fi
printf "DISCO  %s  ${CD}%s libres${C_0}" "$(bar $DPCT)" "$DAV"
[ "$DPCT" -ge 85 ] && printf "  <-- Fusion Drive necesita <80%% para funcionar"
echo; echo

# --- Top consumidores ---
echo "${C_B}Mayores consumidores de RAM${C_0}"
ps -Aceo rss,pcpu,comm -m | awk 'NR>1 && NR<=9 {printf "  %7.0f MB  %5.1f%% cpu  %s\n", $1/1024, $2, substr($0, index($0,$3))}'
echo
echo "${C_B}Mayores consumidores de CPU${C_0}"
ps -Aceo pcpu,rss,comm -r | awk 'NR>1 && NR<=7 {printf "  %5.1f%%  %7.0f MB  %s\n", $1, $2/1024, substr($0, index($0,$3))}'
echo
CH=$(ps -Aco comm | grep -c "Google Chrome Helper (Renderer)")
echo "Procesos totales: $(ps -Ac | wc -l | tr -d ' ')   |   Renderers de Chrome: $CH"
