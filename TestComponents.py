import unittest
from calcs import *


class TestComponents(unittest.TestCase):

    def test_a(self):
        x = [ 0, 1, 2, 3, 4]
        y = [ 0, 1, 2, 3, 4]

        self.assertEqual((0, 0), interp_f(x, 0))
        self.assertEqual((0, 1), interp_f(x, 0.5))
        self.assertEqual((4, 4), interp_f(x, 4))
        self.assertEqual((3, 4), interp_f(x, 3.4))
        self.assertEqual(0.5, interp(x, y, 0.5), 0.0001)
        self.assertEqual(4, interp(x, y, 4.5), 0.0001)

    def test_c1(self):
        """ Demo of complex interpotation """
        x = [0, 1, 2, 3, 4]
        y = [0 + 0j, 0 + 1j, 0 + 2j, 0 + 3j, 0 + 4j]
        self.assertEqual(0 + 0.5j, interp(x, y, 0.5))
        self.assertEqual(0 + 2.1j, interp(x, y, 2.1))

    def test_c2(self):
        x = [ 0, 1, 2, 3, 4]
        y = [ 0 + 0j, 1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j]
        self.assertEqual(0.5 + 0.5j, interp(x, y, 0.5))

if __name__ == '__main__':
    unittest.main()