import unittest
import nanovna
import math
import util 

class Run1(unittest.TestCase):

    def test_1(self):

        rc_list = [ complex(0.5, 0.5) ]
        f_list = [ 1.0 ]

        z_list = [nanovna.Nanovna.reflection_coefficient_to_z(rc) for rc in rc_list]
        self.assertEqual(50 + 100j, z_list[0]) 
        # Return loss
        s11_list = [nanovna.Nanovna.reflection_coefficient_to_s11(rc) for rc in rc_list]
        self.assertAlmostEqual(-3.098, s11_list[0], 0)
        # https://chemandy.com/calculators/return-loss-and-mismatch-calculator.htm
        vswr_list = [nanovna.Nanovna.reflection_coefficient_to_vswr(rc) for rc in rc_list]
        self.assertAlmostEqual(5.82, vswr_list[0], 1)

    def test_2(self):

        rc_list = [ complex(0.5, 0.5) ]
        f_list = [ 1.0e6 ]
        c = -nanovna.Nanovna.reflection_coefficient_to_c(rc_list[0], f_list[0])

        r = 0.999999999999
        self.assertEqual("1F", util.fmt_si(r) + "F")
        r = 1.0
        self.assertEqual("1F", util.fmt_si(r) + "F")
        r = 11e-3
        self.assertEqual("11mF", util.fmt_si(r) + "F")
        r = 1.2e-6
        self.assertEqual("1.2uF", util.fmt_si(r) + "F")
        r = 0.2299e-6
        self.assertEqual("230nF", util.fmt_si(r) + "F")

    def test_parse_scan_lines(self):

        lines = ["7000000 1.281372 0.359714 ", "7002000 -0.5 0.25"]
        f_list, rc_list = nanovna.Nanovna.parse_scan_lines(lines)
        self.assertEqual([7000000.0, 7002000.0], f_list)
        self.assertEqual([complex(1.281372, 0.359714), complex(-0.5, 0.25)], rc_list)
        # No output (e.g. firmware whose scan has no outmask)
        with self.assertRaises(Exception):
            nanovna.Nanovna.parse_scan_lines([])
        # Frequency only
        with self.assertRaises(Exception):
            nanovna.Nanovna.parse_scan_lines(["7000000"])
        # Not a scan response
        with self.assertRaises(Exception):
            nanovna.Nanovna.parse_scan_lines(["scan? usage"])

    def test_supports_scan(self):

        class FakeNanovna(nanovna.Nanovna):
            def __init__(self, help_lines):
                self.help_lines = help_lines
            def run_command(self, command, timeout=None):
                return self.help_lines

        # NanoVNA-F style: one command per line with usage
        n = FakeNanovna(["There are all commands",
                         "scan:                usage: scan {start(Hz)} {stop(Hz)} [points] [outmask]"])
        self.assertTrue(n.supports_scan())
        # edy555 / DiSlord style: all commands on one line
        n = FakeNanovna(["Commands: help exit info echo scan sweep data frequencies"])
        self.assertTrue(n.supports_scan())
        n = FakeNanovna(["Commands: help exit info echo sweep data frequencies"])
        self.assertFalse(n.supports_scan())

if __name__ == '__main__':
    unittest.main()
