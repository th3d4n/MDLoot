#!/usr/bin/env bash
# Download the raw source pages into sources/ (gitignored). Run from anywhere.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/sources"; T="$ROOT/tools"
MB="https://metabot.gg/en/minecraft-dungeons-2"
UA="Mozilla/5.0 (MDLoot fan site data refresh)"
mkdir -p "$SRC/pages"

get() { curl -fsS -A "$UA" -o "$2" "$1"; }
slug() { echo "$1" | tr '[:upper:]' '[:lower:]' | tr -d "'" | tr ' ' '-'; }

for p in weapons uniques armor; do get "$MB/$p" "$SRC/$p.html"; done
get "$MB/armor/sets" "$SRC/sets.html"
get "https://raw.githubusercontent.com/operator1212/dungeons2-stats-mod/main/stats.tsv" "$SRC/stats.tsv"

while IFS= read -r n; do [ -n "$n" ] && get "$MB/artifacts/$(slug "$n")" "$SRC/pages/a_$(slug "$n").html"; done < "$T/artifact_names.txt"
while IFS= read -r n; do [ -n "$n" ] && get "$MB/armor/$(slug "$n")" "$SRC/pages/r_$(slug "$n").html"; done < "$T/armor_extra_names.txt"

python3 -I "$T/extract_pages.py" "$SRC/pages/a_*.html" > "$SRC/art.txt"
python3 -I "$T/extract_pages.py" "$SRC/pages/r_*.html" > "$SRC/arm.txt"
echo "Sources saved to $SRC"
