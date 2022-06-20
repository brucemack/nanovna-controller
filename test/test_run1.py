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

if __name__ == '__main__':
    unittest.main()
