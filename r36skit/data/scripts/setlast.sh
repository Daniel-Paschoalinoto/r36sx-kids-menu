#!/bin/sh
# setlast.sh "<pasta>" "<arquivo>"  -> guarda o ultimo jogo aberto (usado para abrir sozinho ao ligar)
printf '%s\n%s\n' "$1" "$2" > /mnt/sdcard/cubegm/lastgame.txt
sync 2>/dev/null
exit 0
