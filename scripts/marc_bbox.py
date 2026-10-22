"""Parse MARC 255 $c style bounding boxes from catalogue notes.

A note such as

    (E 20°16ʹ00ʺ--E 23°44ʹ00ʺ/N 38°30ʹ00ʺ--N 36°23ʹ00ʺ).

gives the west--east / north--south edges of the area a map shows, in
degrees, minutes and seconds. W and S are negative in decimal degrees.
"""
import re

# Hemisphere, degrees, then optional minutes and seconds. Notes use ʹ ' or ′
# for minutes and ʺ " or ″ for seconds.
DMS = r"([EWNS])\s*(\d{1,3})°\s*(?:(\d{1,2}(?:\.\d+)?)\s*[ʹ'′])?\s*(?:(\d{1,2}(?:\.\d+)?)\s*[ʺ\"″])?"
# Text before the bracket ("ǂc", "Coordinates:") is ignored, and some notes
# lack the closing ")".
BBOX = re.compile(r"\(\s*" + DMS + r"\s*-+\s*" + DMS + r"\s*/\s*" + DMS + r"\s*-+\s*" + DMS + r"\s*\)?")


def to_decimal(hemisphere, degrees, minutes, seconds):
    value = int(degrees) + float(minutes or 0) / 60 + float(seconds or 0) / 3600
    return -value if hemisphere in "WS" else value


def parse_bboxes(notes):
    """[(west, east, north, south), ...] for every valid bounding box in notes.

    A note can hold several boxes, e.g. a main map and an inset; callers
    normally use the first.
    """
    boxes = []
    for note in notes or []:
        for m in BBOX.finditer(note):
            g = m.groups()
            (h1, west), (h2, east), (h3, north), (h4, south) = [
                (g[i], to_decimal(*g[i:i + 4])) for i in range(0, 16, 4)]
            if h1 not in "EW" or h2 not in "EW" or h3 not in "NS" or h4 not in "NS":
                continue
            if north < south:  # catalogue order is N--S; tolerate it reversed
                north, south = south, north
            if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= north <= 90):
                continue
            boxes.append((west, east, north, south))
    return boxes


def centre(west, east, north, south):
    """(lat, lon) centre of a box. west > east means it crosses the antimeridian."""
    if west > east:
        lon = (west + east + 360) / 2
        lon = lon - 360 if lon > 180 else lon
    else:
        lon = (west + east) / 2
    return round((north + south) / 2, 6), round(lon, 6)
