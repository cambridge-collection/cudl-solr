"""Tests for the reference geo scripts. Run: python3 -m unittest discover scripts"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geo_enrich import item_place_of_origin, soi_envelope, soi_sheets
from marc_bbox import centre, parse_bboxes


class MarcBboxTests(unittest.TestCase):
    def test_parses_degrees_minutes_seconds(self):
        [(w, e, n, s)] = parse_bboxes(["(E 20°16ʹ00ʺ--E 23°44ʹ00ʺ/N 38°30ʹ00ʺ--N 36°23ʹ00ʺ)."])
        self.assertAlmostEqual(w, 20.266667, places=5)
        self.assertAlmostEqual(e, 23.733333, places=5)
        self.assertAlmostEqual(n, 38.5)
        self.assertAlmostEqual(s, 36.383333, places=5)

    def test_west_and_south_are_negative(self):
        [(w, e, n, s)] = parse_bboxes(["(W 0°00ʹ27ʺ--E 0°00ʹ34ʺ/N 52°19ʹ16ʺ--N 52°18ʹ36ʺ)"])
        self.assertLess(w, 0)
        self.assertGreater(e, 0)

    def test_accepts_prefixes_and_a_missing_closing_bracket(self):
        for note in [
            "Scale not given ǂc (E 0°15ʹ21ʺ--E 0°18ʹ25ʺ/N 52°23ʹ12ʺ--N 52°21ʹ42ʺ)",
            "Coordinates: (E 92°10ʹ00ʺ--E 101°10ʹ00ʺ/N 28°32ʹ00ʺ--N 9°35ʹ00ʺ)",
            "(E 0°06ʹ51ʺ--E 0°06ʹ57ʺ/N 52°12ʹ42ʺ--N 52°12ʹ38ʺ.",
        ]:
            with self.subTest(note=note):
                self.assertEqual(len(parse_bboxes([note])), 1)

    def test_finds_every_box_in_a_note(self):
        note = ("(E 0°07ʹ56ʺ--E 0°08ʹ16ʺ/N 52°11ʹ42ʺ--N 52°11ʹ16ʺ). "
                "ǂc (E 0°07ʹ32ʺ--E 0°08ʹ25ʺ/N 52°11ʹ54ʺ--N 52°11ʹ15ʺ)")
        self.assertEqual(len(parse_bboxes([note])), 2)

    def test_ignores_other_degree_text(self):
        self.assertEqual(parse_bboxes(["Photo on a slope of 30° - 40°.", "Scale not given"]), [])

    def test_centre_allows_for_the_antimeridian(self):
        self.assertEqual(centre(170, -170, 10, 0), (5.0, 180.0))
        self.assertEqual(centre(20, 24, 38, 36), (37.0, 22.0))


class SurveyOfIndiaTests(unittest.TestCase):
    def test_single_sheet(self):
        self.assertEqual(soi_sheets("No.39 H 3"), [(39, "H", 3)])
        self.assertEqual(soi_envelope(soi_sheets("No.39 H 3")), (69.0, 69.25, 28.5, 28.25))

    def test_several_sheets_cover_all_of_them(self):
        self.assertEqual(soi_sheets("No.35 K 16 & K 12"), [(35, "K", 16), (35, "K", 12)])
        self.assertEqual(soi_sheets("No.38 G 12 & 8"), [(38, "G", 12), (38, "G", 8)])
        self.assertEqual(soi_sheets("Parts of 40B/15 & 40F/3"), [(40, "B", 15), (40, "F", 3)])
        self.assertEqual(soi_sheets("No. 41 K 4 & G 16"), [(41, "K", 4), (41, "G", 16)])
        self.assertEqual(soi_envelope(soi_sheets("No. 41 K 4 & G 16")), (69.75, 70.25, 21.25, 21.0))

    def test_ignores_edition_text(self):
        self.assertEqual(soi_sheets("No. 43 D 01 Second Edition"), [(43, "D", 1)])
        self.assertEqual(soi_sheets("No. 44 N 10 A"), [(44, "N", 10)])

    def test_letter_only_is_a_whole_degree_sheet(self):
        self.assertEqual(soi_envelope(soi_sheets("No.34 P")), (67, 68.0, 29, 28.0))

    def test_other_numbering_gives_nothing(self):
        self.assertEqual(soi_sheets("No. 111"), [])
        self.assertIsNone(soi_envelope(soi_sheets("No. 111")))


class PlaceOfOriginTests(unittest.TestCase):
    def test_reads_decimal_coordinates(self):
        item = {"pages": [{"creations-places": "52.175613 0.141032"}]}
        self.assertEqual(item_place_of_origin(item), (52.175613, 0.141032))

    def test_ignores_place_names_and_out_of_range_values(self):
        self.assertIsNone(item_place_of_origin({"pages": [{"creations-places": ["Madrid"]}]}))
        self.assertIsNone(item_place_of_origin({"pages": [{"creations-places": "95.1234 0.1234"}]}))


if __name__ == "__main__":
    unittest.main()
