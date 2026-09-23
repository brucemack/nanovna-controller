import unittest
import analysis
from analysis import vswr_to_gamma


def to_gammas(vswr_list):
    return [vswr_to_gamma(v) for v in vswr_list]


class TestAnalysis(unittest.TestCase):

    def test_parse_thresholds(self):
        self.assertEqual([1.5, 2.0], analysis.parse_vswr_thresholds("1.5, 2"))
        self.assertEqual([1.5, 2.0], analysis.parse_vswr_thresholds("2 1.5;2.0"))
        self.assertEqual([], analysis.parse_vswr_thresholds(""))
        self.assertEqual([], analysis.parse_vswr_thresholds("  "))
        self.assertEqual([], analysis.parse_vswr_thresholds(None))
        for bad in ["0.9", "1", "abc", "inf", "nan"]:
            with self.assertRaises(Exception):
                analysis.parse_vswr_thresholds(bad)

    def test_extrema_example(self):
        # Shape from the 86-108 MHz example: minima 1.3, 1.1, 1.2 and maxima 1.5, 1.5
        vswr = [2.0, 1.6, 1.3, 1.4, 1.5, 1.3, 1.1, 1.3, 1.5, 1.4, 1.2, 1.6, 2.2]
        extrema = analysis.find_local_extrema(to_gammas(vswr))
        self.assertEqual([(2, "minimum"), (4, "maximum"), (6, "minimum"), (8, "maximum"), (10, "minimum")], extrema)

    def test_extrema_ignores_noise(self):
        gammas = [0.30, 0.20, 0.10, 0.104, 0.101, 0.105, 0.20, 0.30]
        self.assertEqual([(2, "minimum")], analysis.find_local_extrema(gammas))

    def test_extrema_monotonic(self):
        self.assertEqual([], analysis.find_local_extrema([0.1, 0.2, 0.3, 0.4, 0.5]))
        self.assertEqual([], analysis.find_local_extrema([0.5, 0.4, 0.3, 0.2, 0.1]))

    def test_extrema_edges_not_reported(self):
        # Maximum at the first sample, minimum inside, maximum pending at the end
        self.assertEqual([(2, "minimum")], analysis.find_local_extrema([0.5, 0.3, 0.1, 0.3, 0.5]))
        self.assertEqual([], analysis.find_local_extrema([0.1, 0.2]))

    def test_ranges_v_shape(self):
        f = [0.0, 1.0, 2.0, 3.0, 4.0]
        g = [0.4, 0.2, 0.0, 0.2, 0.4]
        ranges = analysis.find_ranges_below(f, g, 0.3)
        self.assertEqual(1, len(ranges))
        self.assertAlmostEqual(0.5, ranges[0]["start_hz"])
        self.assertAlmostEqual(3.5, ranges[0]["end_hz"])
        self.assertEqual(2, ranges[0]["min_index"])
        self.assertFalse(ranges[0]["open_start"])
        self.assertFalse(ranges[0]["open_end"])

    def test_ranges_open_edges(self):
        f = [0.0, 1.0, 2.0, 3.0]
        ranges = analysis.find_ranges_below(f, [0.1, 0.2, 0.4, 0.5], 0.3)
        self.assertEqual(1, len(ranges))
        self.assertTrue(ranges[0]["open_start"])
        self.assertEqual(0.0, ranges[0]["start_hz"])
        self.assertAlmostEqual(1.5, ranges[0]["end_hz"])
        ranges = analysis.find_ranges_below(f, [0.2, 0.2, 0.2, 0.2], 0.3)
        self.assertTrue(ranges[0]["open_start"])
        self.assertTrue(ranges[0]["open_end"])
        self.assertEqual(3.0, ranges[0]["end_hz"])

    def test_ranges_none_and_two_dips(self):
        f = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        self.assertEqual([], analysis.find_ranges_below(f, [0.5] * 7, 0.3))
        ranges = analysis.find_ranges_below(f, [0.5, 0.1, 0.5, 0.5, 0.2, 0.05, 0.5], 0.3)
        self.assertEqual(2, len(ranges))
        self.assertEqual(1, ranges[0]["min_index"])
        self.assertEqual(5, ranges[1]["min_index"])

    def test_analyze_sweep_format(self):
        f = [86e6, 90e6, 94e6, 98e6, 102e6, 106e6]
        g = [1.0, to_gammas([1.3])[0], 0.5, 0.2, 0.6, 1.02]
        result = analysis.analyze_sweep(f, g, [2.0])
        self.assertEqual(6, result["point_count"])
        self.assertEqual({"kind": "minimum", "frequency_mhz": "90.000", "vswr": "1.30"}, result["extrema"][0])
        self.assertEqual("maximum", result["extrema"][1]["kind"])
        band = result["bands"][0]
        self.assertEqual("2.00", band["threshold"])
        self.assertEqual(2, len(band["ranges"]))
        self.assertEqual("90.000", band["ranges"][0]["min_frequency_mhz"])
        self.assertFalse(band["ranges"][0]["open_start"])
        self.assertEqual("∞", analysis._fmt_vswr(1.02))

    def test_analyze_sweep_no_thresholds(self):
        result = analysis.analyze_sweep([1e6, 2e6, 3e6], [0.5, 0.1, 0.5], [])
        self.assertEqual([], result["bands"])


if __name__ == '__main__':
    unittest.main()
