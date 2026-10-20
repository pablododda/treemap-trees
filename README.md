# TreeMap trees

Street and park trees mapped by volunteers on [OpenStreetMap](https://www.openstreetmap.org), cut into small
map tiles so the [TreeMap](https://treemap-preview.pages.dev) app can show them for any city on the planet.

- Source: OpenStreetMap `natural=tree` nodes that name a species, genus or taxon.
- Refreshed weekly by the workflow in `.github/workflows/build.yml` (streams the planet file, keeps only trees).
- Served by GitHub Pages: `https://pablododda.github.io/treemap-trees/13/{x}/{y}.json` (zoom-13 web tiles),
  with stats in `index.json`.

Tile format: `{"k": [keys...], "e": [[osm_id, lat, lon, value for each key...], ...]}`; trailing empty values are dropped.

## License

The data is © OpenStreetMap contributors and available under the
[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). If you use it, credit
"© OpenStreetMap contributors" and share any database you build from it under the same license.
The scripts in this repository are MIT licensed.
