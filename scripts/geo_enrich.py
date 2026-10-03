#!/usr/bin/env python3
"""Add map fields to copies of Solr JSON files, using only data already present.

Reference implementation for the data pipeline (see
docs/MAPS-GEO-SEARCH-RELEASE.md). It reads the release's solr-json files,
never modifies them, and writes a copy of every item that gains a location.

Place shown (the area an item depicts):
  coverage_srpt  ENVELOPE(west, east, north, south)
  coverage_p     "lat,lon" centre
  from  - MARC 255 $c bounding-box notes (see marc_bbox.py)
        - Survey of India sheet numbers in shelfLocator, e.g. "No.39 H 3"

Place of origin:
  origin_srpt    POINT(lon lat)
  origin_p       "lat,lon"
  from  - decimal "lat lon" values in creations-places

Usage:
  scripts/geo_enrich.py --src ~/projects/cudl-data-releases/solr-json --out /tmp/geo-out
"""
import argparse
import collections
import functools
import json
import os
import re
from multiprocessing import Pool

from marc_bbox import parse_bboxes, centre

LATLON = re.compile(r"^\s*(-?\d{1,2}\.\d{2,})[\s,;]+(-?\d{1,3}\.\d{2,})\s*$")

# Survey of India "India and Adjacent Countries" 4° sheets used in the
# collection: number -> (west, south). Reconstructed from known places;
# verify against an official sheet index before relying on it.
SOI_SHEETS = {
    34: (64, 28), 35: (64, 24),
    38: (68, 32), 39: (68, 28), 40: (68, 24), 41: (68, 20),
    43: (72, 32), 44: (72, 28), 45: (72, 24), 46: (72, 20),
    53: (76, 28),
    64: (80, 20),
}
SOI_LETTERS = "ABCDEFGHIJKLMNOP"
SOI_TOKEN = re.compile(r"(?<![A-Za-z])([A-P])(?![A-Za-z])|(\d+)")


def soi_sheets(shelf_locator):
    """[(block, letter, number or None)] for every sheet named in a shelf mark.

    Handles "No.39 H 3", "No.35 K 16 & K 12", "No.38 G 12 & 8",
    "Parts of 40B/15 & 40F/3" and "No. 40 H 07 & 03 and part of 40 D 15".
    4° block numbers are all above 16 and sheet numbers 1-16, which tells them apart.
    """
    sheets = []
    block = letter = None
    for let, num in SOI_TOKEN.findall(shelf_locator or ""):
        if num:
            n = int(num)
            if n > 16:
                block, letter = n, None
            elif block is not None and letter is not None:
                sheets.append((block, letter, n))
        elif block is not None:
            letter = let
    if not sheets and block is not None and letter is not None:
        sheets.append((block, letter, None))  # a whole 1° sheet
    return sheets


def soi_envelope(sheets):
    """(west, east, north, south) covering the given sheets, or None."""
    boxes = []
    for block, letter, number in sheets:
        if block not in SOI_SHEETS:
            continue
        west, south = SOI_SHEETS[block]
        i = SOI_LETTERS.index(letter)
        # 1° sheets run north to south down each column, columns west to east;
        # 15' sheets are numbered the same way within their 1° sheet.
        w, n = west + i // 4, south + 4 - i % 4
        size = 1.0
        if number is not None:
            j = number - 1
            w, n, size = w + (j // 4) * 0.25, n - (j % 4) * 0.25, 0.25
        boxes.append((w, w + size, n, n - size))
    if not boxes:
        return None
    return (min(b[0] for b in boxes), max(b[1] for b in boxes),
            max(b[2] for b in boxes), min(b[3] for b in boxes))


def first(value):
    return value[0] if isinstance(value, list) and value else value


def as_list(value):
    return value if isinstance(value, list) else ([value] if value else [])


def item_place_shown(item, text):
    """(west, east, north, south) for the item, and which source gave it."""
    pages = item.get("pages") or []
    if "°" in text:
        box = next((b[0] for b in (parse_bboxes(p.get("notes")) for p in pages) if b), None)
        if box:
            return box, "bbox-note"
    if "surveyofindiamaps" in (item.get("collection-slug") or []):
        shelf = next((first(p.get("shelfLocator")) for p in pages if p.get("shelfLocator")), "")
        box = soi_envelope(soi_sheets(shelf))
        if box:
            return box, "soi-sheet"
    return None, None


def item_place_of_origin(item):
    """(lat, lon) from the first decimal coordinates in creations-places, or None."""
    for page in item.get("pages") or []:
        for value in as_list(page.get("creations-places")):
            m = LATLON.match(value) if isinstance(value, str) else None
            if m:
                lat, lon = float(m.group(1)), float(m.group(2))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
    return None


def enrich(filename, src, out):
    text = open(os.path.join(src, filename), encoding="utf-8").read()
    item = json.loads(text)
    slugs = item.get("collection-slug") or []
    item_box, source = item_place_shown(item, text)
    origin = item_place_of_origin(item)
    sources = collections.Counter()
    if source:
        sources[source] += 1
    if origin:
        sources["origin-latlon"] += 1
    if not item_box and not origin:
        return slugs, sources, False

    for page in item.get("pages") or []:
        # A page's own note wins; pages without one (continuation sheets)
        # inherit the item's box.
        boxes = parse_bboxes(page.get("notes")) if "°" in text else []
        box = boxes[0] if boxes else item_box
        if box:
            west, east, north, south = box
            page["coverage_srpt"] = f"ENVELOPE({west:.6f}, {east:.6f}, {north:.6f}, {south:.6f})"
            lat, lon = centre(west, east, north, south)
            page["coverage_p"] = f"{lat},{lon}"
        if origin:
            lat, lon = origin
            page["origin_srpt"] = f"POINT({lon} {lat})"
            page["origin_p"] = f"{lat},{lon}"
    with open(os.path.join(out, filename), "w", encoding="utf-8") as fh:
        json.dump(item, fh, ensure_ascii=False)
    return slugs, sources, True


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--src", required=True, help="directory of solr-json files to read")
    parser.add_argument("--out", required=True, help="directory to write enriched copies to")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    files = [f for f in os.listdir(args.src) if f.endswith(".json")]
    per_collection = collections.defaultdict(collections.Counter)
    written = 0
    with Pool() as pool:
        work = functools.partial(enrich, src=args.src, out=args.out)
        for slugs, sources, wrote in pool.imap_unordered(work, files, chunksize=200):
            written += wrote
            for slug in slugs:
                per_collection[slug].update(sources)
    print("files written:", written)
    for slug, counts in sorted(per_collection.items()):
        if counts:
            print(f"  {slug:28} {dict(counts)}")


if __name__ == "__main__":
    main()
