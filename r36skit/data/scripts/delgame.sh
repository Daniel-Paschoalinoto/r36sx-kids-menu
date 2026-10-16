#!/bin/sh
# delgame.sh "<caminho completo do jogo>"
# Apaga o jogo escolhido, os arquivos listados no .cue, os de mesmo nome e as capas.
# Registro: cubegm/delgame.log (a saida deste script e redirecionada para la).
SD="${SD:-/mnt/sdcard}"
echo "---- delgame: arg=[$1]"
f=$(printf '%s' "$1" | sed 's#//*#/#g')
case "$f" in
  "$SD"/roms/*) root="$SD/roms" ;;
  "$SD"/*/roms/*) root="${f%%/roms/*}/roms" ;;
  *) echo "recusado: fora de roms: [$f]"; exit 1 ;;
esac
case "$f" in *..*) echo "recusado: contem .."; exit 1 ;; esac
if [ ! -f "$f" ]; then echo "recusado: arquivo nao existe: [$f]"; exit 1; fi
d="${f%/*}"
b="${f##*/}"
stem="${b%.*}"
ext="${b##*.}"
echo "pasta=[$d] arquivo=[$b] nome=[$stem] ext=[$ext]"
case "$ext" in
  cue|CUE|Cue)
    while IFS= read -r line; do
      case "$line" in
        *FILE*|*file*|*File*)
          t=$(printf '%s\n' "$line" | sed -n 's/^[^"]*"\(.*\)".*$/\1/p')
          if [ -n "$t" ]; then echo "apagando (cue): [$t]"; rm -f -- "$d/$t"; fi
          ;;
      esac
    done < "$f"
    ;;
esac
# se for o ultimo jogo registrado, esquecer
lg="${LASTGAME:-$SD/cubegm/lastgame.txt}"
if [ -f "$lg" ]; then
  lgd="$(sed -n 1p "$lg" | tr -d '\r')"; lgn="$(sed -n 2p "$lg" | tr -d '\r')"
  if [ "$lgd" = "$d" ] && [ "$lgn" = "$b" ]; then echo "esquecendo lastgame"; rm -f -- "$lg"; fi
fi
echo "apagando: [$f]"
rm -f -- "$f"
for x in "$d"/*; do
  [ -f "$x" ] || continue
  bn="${x##*/}"
  case "$bn" in "$stem".*) echo "apagando (mesmo nome): [$bn]"; rm -f -- "$x";; esac
done
for dir in "$d/images" "$root/images"; do
  [ -d "$dir" ] || continue
  for x in "$dir"/*; do
    [ -f "$x" ] || continue
    bn="${x##*/}"
    case "$bn" in
      "$stem".png|"$stem"\(*\).png) echo "apagando (capa): [$dir/$bn]"; rm -f -- "$x";;
    esac
  done
done
sync 2>/dev/null
echo "ok"
exit 0
