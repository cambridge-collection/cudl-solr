# Map search: release changes

Map-based search for CUDL: a map on the search results page for collections whose items have locations, a "Search this area" filter, and "Show on map" for each result. Collection pages can also show a map of their items, with a List | Map switch, "Filter to this area" and "Show on map" on each item.

Each map is switched on per collection in `cudl.ui.json5` (section 5); nothing is hard-coded.

The code is on branch `feat/maps-geo-search` in four repos. The published data does **not** yet contain the location fields, so the data pipeline change in section 2 is needed before anything appears on the map.

## 1. Code changes

| Repo | Commit | Change |
|---|---|---|
| cudl-solr | `d329e8d` | `coverage_p`, `coverage_srpt`, `origin_p`, `origin_srpt` added to the default `fl` in `cdcp/conf/solrconfig.xml`. No schema change: the fields use the existing `*_p` and `*_srpt` dynamic fields. |
| cudl-search | `089a1f3` | `GET /items` accepts `bbox=west,south,east,north`. New `GET /items/locations` endpoint. |
| cudl-viewer | `a7b5bb10` | `bbox` search parameter, `coverage`/`origin` in `/search/JSON*`, new `/search/locationsJSON`. `docker-compose.yml`: `extra_hosts` for local development only. |
| cudl-viewer | `2fdd498f` | Reads `"map"` from `cudl.ui.json5` and passes the map collections to the search results page. |
| cudl-viewer | `feeea27f` | `/collections/{id}/itemJSON` takes `bbox` and returns each item's `coverage`/`origin`. Builds on the collection filter already on `main`. |
| cudl-viewer | `a87bab43` | Reads `"collectionMap"` from `cudl.ui.json5` for collection pages. |
| cudl-viewer-ui | `97cf3d1` | Leaflet map panel on the search results page. New dependencies: `leaflet` ^1.9.4, `leaflet.markercluster` ^1.5.3. |
| cudl-viewer-ui | `27718d9` | Map collections come from the page context instead of a hard-coded list. |
| cudl-viewer-ui | `dc93eb4` | List \| Map view on collection pages, added to the filter bar already on `main`. |

### Location fields

These are set on every page document of an item (in each entry of the `pages` array in the Solr JSON).

| Field | Meaning | Format | Example |
|---|---|---|---|
| `coverage_srpt` | Place shown: the area an item depicts | `ENVELOPE(west, east, north, south)`, decimal degrees | `ENVELOPE(20.266667, 23.733333, 38.500000, 36.383333)` |
| `coverage_p` | Centre of the place shown | `lat,lon` | `37.441667,22.0` |
| `origin_srpt` | Place of origin | `POINT(lon lat)` (longitude first) | `POINT(0.141032 52.175613)` |
| `origin_p` | Place of origin | `lat,lon` | `52.175613,0.141032` |

In the UI these are labelled **Place shown** and **Place of origin**. Do not label origin as "place made": that is wrong for books and artefacts.

## 2. Data pipeline (cudl-data-processing-xslt)

Generate the fields above in the Solr JSON. Use only coordinates already in the records: **no gazetteer or geocoding lookups**.

A working reference implementation is in [`scripts/`](../scripts/README.md): `geo_enrich.py` and `marc_bbox.py`, with unit tests. It produces the 2,612 enriched items used for local testing.

### 2a. Bounding-box notes → `coverage_*` (Maps, Scott Polar Research Institute)

The source is catalogue notes in MARC 255 ‡c form, e.g. `(E 20°16ʹ00ʺ--E 23°44ʹ00ʺ/N 38°30ʹ00ʺ--N 36°23ʹ00ʺ).`

- **Order:** west--east / north--south. Each value is hemisphere, degrees, then optional minutes and seconds. W and S are negative.
- **Primes:** accept `ʹ ' ′` for minutes and `ʺ " ″` for seconds.
- **Variants to accept:**
  - a leading `ǂc` or `Coordinates:` (and other text before the bracket);
  - a missing closing `)`;
  - several boxes in one note (a main map plus an inset). Use the first.
- **Checks:**
  - swap north and south if they are reversed;
  - reject longitudes outside ±180 and latitudes outside ±90;
  - west > east means the box crosses the antimeridian. That is valid; the centre must allow for it.
- **Pages with no notes of their own** (continuation sheets) inherit the item's first box.
- **Expected:** 1,053 of the 1,078 Maps items, plus 2 SPRI items.

### 2b. Survey of India sheet numbers → `coverage_*` (Survey of India Maps)

The source is `shelfLocator`, e.g. `No.39 H 3`: a 4° block number, a letter A–P (a 1° square), and an optional number 1–16 (a 15ʹ square).

- **Letters A–P** run north to south down each column, columns west to east: A–D are the first column, E–H the second.
- **Numbers 1–16** are laid out the same way within the 1° square.
- **Telling block numbers from sheet numbers:** block numbers are all above 16, sheet numbers 16 or below.
- **Shelf marks naming several sheets** (`No.35 K 16 & K 12`, `Parts of 40B/15 & 40F/3`, `No. 40 H 07 & 03 and part of 40 D 15`): use the bounding box covering all of them. Ignore edition text such as "Second Edition".
- **4° blocks used**, giving the south-west corner of each:

| Block | West | South |
|---|---|---|
| 34 | 64 | 28 |
| 35 | 64 | 24 |
| 38 | 68 | 32 |
| 39 | 68 | 28 |
| 40 | 68 | 24 |
| 41 | 68 | 20 |
| 43 | 72 | 32 |
| 44 | 72 | 28 |
| 45 | 72 | 24 |
| 46 | 72 | 20 |
| 53 | 76 | 28 |
| 64 | 80 | 20 |

- ⚠️ **This table was worked out from known places,** and the results matched the maps' descriptions (e.g. 41 K → Junagadh, 46 E 11 → Balasinor). **Check it against an official Survey of India "India and Adjacent Countries" sheet index before release.**
- **Expected:** 479 of 481 items. The exceptions are `No. 111`, which uses a different numbering scheme, and one other.

### 2c. Decimal coordinates → `origin_*` (Landscape Histories from the Air, Walking with Constable)

- **Source:** a `creations-places` value that is a decimal latitude/longitude pair, e.g. `52.175613 0.141032`. In the TEI it is `<origPlace><geo>…</geo></origPlace>`.
- **Expected:** 1,078 of 1,411 Landscape Histories items. This includes the 23 of 65 Constable items, which are the same records.
- **Display:** these values also show on the site as raw numbers wherever the origin place is displayed or faceted. Consider hiding the `<geo>` value from those displays.

### 2d. Not yet included (optional)

- **3 Faculty of Classics / Digital Thessaly photos** (`MS-CLASSICS-AJBW-…`): `Coordinates: 39.29…, 22.27…` appears in the description text. Add as place shown (a point).
- **1 Japanese map** (`PR-FK-00211-00019`): `Coordinates: 124.000-132.000/ 33.000~43.000`, a decimal bounding box written in a different style. Add as place shown.

## 3. Release order

1. **cudl-solr:** deploy the updated `solrconfig.xml` and reload the `cdcp` core.
2. **cudl-search:** deploy the API.
3. **Data:** release the XSLT change and re-index the items in the map collections. Every page document of an item needs the fields, so re-index whole items.
4. **cudl-viewer-ui:** release a new version (currently `4.3.2-SNAPSHOT`) with the new npm dependencies.
5. **cudl-viewer:** set `cudl-viewer-ui.version` in `pom.xml` (currently `4.3.1`) to the new UI version, then release.
6. **`cudl.ui.json5`:** add `"map"` and `"collectionMap"` to the map collections (see section 5). Until then no collection shows a map.

The viewer copes with steps 1–3 not being done yet: the map shows no items, and every result says "Not on map". Old viewers ignore the new API endpoint and fields.

## 4. Configuration and infrastructure

- **No new viewer properties.** Which collections have a map is set per collection in `cudl.ui.json5` (see section 5).
- **Do not commit local dev settings.** These belong only in a local `docker/cudl-global.properties`:
  - `searchURL=http://host.docker.internal:80/`
  - `cudl.ui.dev = true`
- **Map tiles:** browsers load tiles from `https://tile.openstreetmap.org/`.
  - If a Content-Security-Policy is set anywhere (CloudFront, load balancer, Tomcat), allow that host in `img-src`. None was found in cudl-viewer, cudl-terraform or cudl-cdk.
  - The OpenStreetMap tile usage policy applies. It is fine for modest traffic; heavy use needs a hosted tile provider. Attribution is shown on the map.
- **Privacy notice:** visitors' browsers request map tiles from OpenStreetMap. Consider mentioning this.

## 5. Which collections have a map

Two settings on a collection's entry in `cudl.ui.json5` (next to `layout`) switch the maps on. They are independent: a collection can have either, both or neither.

| Setting | Controls |
|---|---|
| `"map"` | The map on the search results page, when the collection is the selected Collection facet. |
| `"collectionMap"` | The map on the collection's own page: the List \| Map switch, and "Show on map" on each item. |

Each takes the same values:

- `true`: the map is on.
- `{"collapsed": true}`: the map is on, with a note that many items have no recorded location. On the search page the map also starts closed. Use it when fewer than half the collection's items have a location.
- Absent, or `false`: no map. This is the default, so collections without the settings are unaffected, and older viewers ignore them.

Turn them on only for collections with more than a handful of items with a location. Current values:

| Collection | `cudl.ui.json5` entry | `map` and `collectionMap` | Items with a location |
|---|---|---|---|
| Maps | `collections/maps.collection.json` | `true` | 1,053 of 1,078 |
| Survey of India Maps | `collections/surveyofindiamaps.collection.json` | `true` | 479 of 481 |
| Landscape Histories from the Air | `collections/landscapehistories.collection.json` | `true` | 1,078 of 1,411 |
| Walking with Constable | `collections/constable.collection.json` | `{"collapsed": true}` | 23 of 65 |

**`ITEM_LOCATIONS_MAX_ROWS` in `cudl-search/frontend/main.py` (5,000):** the most locations returned for one map. Increase it if collections grow.

## 6. Checks after release

- [ ] `GET /items?fq=facet-collection:"Maps"&bbox=0.11,52.19,0.14,52.22` returns results, and the docs include `coverage_srpt`.
- [ ] `GET /items?bbox=0,0,1` returns 400.
- [ ] `GET /items/locations?fq=facet-collection:"Maps"`: `numFound` is about 1,053.
- [ ] Search page, Collection = Maps:
  - [ ] the map opens with blue clusters, and the summary says about 1,053 items;
  - [ ] Points / Areas / Map only all work;
  - [ ] "Search this area" filters the results and adds a "within map area" chip, which can be removed.
- [ ] Collection = Landscape Histories: orange points. Collection = Walking with Constable: the map starts collapsed, with the amber note.
- [ ] "Show on map" zooms to and highlights the item. Results without a location say "Not on map · no location recorded".
- [ ] Other collections show no map, and the Collection facet shows the map icon only for the four map collections.
- [ ] `/collections/maps`: a List | Map switch. Map view shows the collection's items; "Filter to this area" filters the list. Items show "Show on map", or "Not on map" when they have no location.
- [ ] `/collections/constable`: the map view shows the note that many items have no location.
- [ ] A collection without `"collectionMap"` has the filter bar but no List | Map switch.

## 7. Known limitations and open items

- **The Survey of India sheet table** (2b) needs checking before release.
- **Place search box on the map** (place name or postcode): parked. The recommendation was Nominatim plus postcodes.io; it needs a decision on the provider and the privacy notice.
- **Order of results with no keyword:** a search within one collection with no keyword returns results in the index's internal order, not collection order. A fix would be a sort tiebreak (`score desc, collection_sort asc`) when one Collection facet is selected.
- **Letters:** the TEI `<correspDesc>` records sender and recipient places as names only (1,511 letters, 1,162 of them Darwin, which are released only as bound volumes). They can't be mapped without a lookup.
- **Very large areas** (e.g. a world map): in Points mode, the centre marker is off-screen when zoomed in elsewhere.
