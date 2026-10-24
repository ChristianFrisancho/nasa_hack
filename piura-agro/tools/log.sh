#!/usr/bin/env bash
# uso: tools/log.sh <archivo.tsv> <fase> <decision> <por_que> <evidencia> <resultado>
set -euo pipefail
[ "$#" -eq 6 ] || { echo "uso: $0 <archivo.tsv> <fase> <decision> <por_que> <evidencia> <resultado>" >&2; exit 2; }
f="$1"; shift
[ -s "$f" ] || printf 'ts\tphase\tdecision\twhy\tevidence\tresult\n' > "$f"
clean() { local s; s=$(printf '%s' "$1" | tr '\t\n\r' '   '); case "$s" in [=+\-@]*) s="'$s";; esac; printf '%s' "$s"; }
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(clean "$1")" "$(clean "$2")" "$(clean "$3")" "$(clean "$4")" "$(clean "$5")" >> "$f"
