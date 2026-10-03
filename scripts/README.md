# Scripts

Reference scripts for map search. See [docs/MAPS-GEO-SEARCH-RELEASE.md](../docs/MAPS-GEO-SEARCH-RELEASE.md).

These show how the location fields are worked out from data already in the records. They are for local testing, and as a reference for the XSLT in cudl-data-processing-xslt. They are not part of the release pipeline.

| Script | Purpose |
|---|---|
| `geo_enrich.py` | Reads a folder of Solr JSON files and writes copies of the items that gain `coverage_*` (place shown) or `origin_*` (place of origin) fields. The source files are never modified. |
| `marc_bbox.py` | Parses MARC 255 $c bounding-box notes. Used by `geo_enrich.py`. |
| `index_solr_json.sh` | Posts Solr JSON files to a core the way cudl-search's `PUT /item` does: one document per page. |
| `test_geo.py` | Unit tests for the parsing. |

## Local use

```bash
# 1. Add location fields to copies of the release's Solr JSON
scripts/geo_enrich.py --src ~/projects/cudl-data-releases/solr-json --out /tmp/geo-out

# 2. Index them into a local Solr (SOLR_URL defaults to http://localhost:8983/solr/cdcp)
scripts/index_solr_json.sh /tmp/geo-out

# Tests
python3 -m unittest discover scripts
```

To index whole collections, index the original files first and then the enriched copies. Copies replace the original documents, so items without a location stay in the index.

Requires Python 3.8+. There are no third-party dependencies.
