#!/usr/bin/env bash
# Stream an OpenStreetMap .pbf (the whole planet by default) and keep only natural=tree nodes.
# Streaming means the ~80 GB planet never has to fit on disk.
set -euo pipefail
SRC="${1:-}"
MIRRORS=(
  "https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf"
  "https://ftp.fau.de/osm-planet/pbf/planet-latest.osm.pbf"
  "https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf"
)
[ -n "$SRC" ] && MIRRORS=("$SRC")
for url in "${MIRRORS[@]}"; do
  echo "Reading $url"
  if curl -fsSL --retry 3 --retry-delay 10 "$url" | osmium tags-filter -F pbf -R --overwrite -o trees.osm.pbf - n/natural=tree; then
    ls -la trees.osm.pbf
    echo "SOURCE_URL=$url" >> "${GITHUB_ENV:-/dev/null}"
    exit 0
  fi
  echo "Failed reading $url, trying the next mirror"
done
exit 1
