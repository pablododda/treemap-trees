"""Turn OpenStreetMap natural=tree nodes into small JSON tiles TreeMap can load for any area.

    python3 scripts/build_tiles.py trees.osm.pbf site [--all]

Keeps trees that name a species, genus or taxon (use --all to keep every tree). Each tile is one
zoom-13 web-map tile (about 5 km wide at the equator) at site/13/{x}/{y}.json:

    {"k": ["species", "genus", ...], "e": [[osm_id, lat, lon, "Tilia cordata", "Tilia", ...], ...]}

Data (c) OpenStreetMap contributors, available under the Open Database License (ODbL) 1.0.
"""
import json
import math
import os
import sys
import time
from collections import defaultdict

import osmium

Z = 13
COVERAGE_Z = 11
KEYS = ["species", "genus", "taxon", "leaf_type", "leaf_cycle", "height", "diameter_crown", "species:wikidata"]
NAME_KEYS = ("species", "genus", "taxon")


def tile(lat, lon):
    n = 2 ** Z
    x = int((lon + 180.0) / 360.0 * n)
    r = math.radians(max(min(lat, 85.0511), -85.0511))
    y = int((1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


class Trees(osmium.SimpleHandler):
    def __init__(self, keep_all):
        super().__init__()
        self.keep_all = keep_all
        self.tiles = defaultdict(list)
        self.seen = 0
        self.kept = 0
        self.species = defaultdict(int)

    def node(self, n):
        if n.tags.get("natural") != "tree" or not n.location.valid():
            return
        self.seen += 1
        tags = n.tags
        if not self.keep_all and not any(k in tags for k in NAME_KEYS):
            return
        lat, lon = round(n.location.lat, 6), round(n.location.lon, 6)
        row = [n.id, lat, lon] + [tags.get(k, "") for k in KEYS]
        while row and row[-1] == "":
            row.pop()
        self.tiles[tile(lat, lon)].append(row)
        self.kept += 1
        name = tags.get("species") or tags.get("taxon") or tags.get("genus")
        if name and " " not in name and tags.get("genus") and name != tags.get("genus"):
            name = f'{tags.get("genus")} {name}'  # bare epithet, e.g. species=romanzoffiana
        if name:
            self.species[name] += 1


def main():
    src, out = sys.argv[1], sys.argv[2]
    keep_all = "--all" in sys.argv
    t0 = time.time()
    h = Trees(keep_all)
    h.apply_file(src, locations=False)
    os.makedirs(out, exist_ok=True)
    biggest = 0
    for (x, y), rows in h.tiles.items():
        d = os.path.join(out, str(Z), str(x))
        os.makedirs(d, exist_ok=True)
        body = json.dumps({"k": KEYS, "e": rows}, ensure_ascii=False, separators=(",", ":"))
        biggest = max(biggest, len(body))
        with open(os.path.join(d, f"{y}.json"), "w", encoding="utf-8") as f:
            f.write(body)
    top = sorted(h.species.items(), key=lambda kv: -kv[1])[:200]
    index = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": os.environ.get("SOURCE_URL", src),
        "zoom": Z,
        "tile_url": "{z}/{x}/{y}.json",
        "keys": KEYS,
        "filter": "natural=tree nodes" + ("" if keep_all else " with species, genus or taxon"),
        "trees_seen": h.seen,
        "trees_kept": h.kept,
        "tiles": len(h.tiles),
        "largest_tile_bytes": biggest,
        "top_species": top,
        "attribution": "© OpenStreetMap contributors",
        "license": "Open Database License (ODbL) 1.0, https://opendatacommons.org/licenses/odbl/1-0/",
    }
    with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    # where in the world there are mapped trees, for TreeMap's map seen from far out: zoom-11 cells (about 20 km at
    # the equator) with how many trees each, as a flat list x0,y0,count0,x1,y1,count1,...
    cov = defaultdict(int)
    n = 2 ** COVERAGE_Z
    for rows in h.tiles.values():
        for row in rows:
            lat, lon = row[1], row[2]
            x = int((lon + 180.0) / 360.0 * n)
            r = math.radians(max(min(lat, 85.0511), -85.0511))
            y = int((1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * n)
            cov[(min(max(x, 0), n - 1), min(max(y, 0), n - 1))] += 1
    flat = []
    for (x, y), c in sorted(cov.items()):
        flat += [x, y, c]
    with open(os.path.join(out, "coverage.json"), "w", encoding="utf-8") as f:
        json.dump({"z": COVERAGE_Z, "cells": flat}, f, separators=(",", ":"))
    with open(os.path.join(out, ".nojekyll"), "w") as f:
        f.write("")
    print(f"{h.kept:,} of {h.seen:,} trees kept in {len(h.tiles):,} tiles; largest {biggest/1e6:.1f} MB; {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
