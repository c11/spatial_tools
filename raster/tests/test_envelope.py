#pylint: disable=invalid-name,too-many-public-methods

"""
Tests for Envelope and RasterEnvelope classes
"""

import unittest
from spatial_tools.raster import envelope


class EnvelopeTest(unittest.TestCase):
    """
    Envelope class tests
    """
    def test_default(self):
        """
        Test extraction of attributes from standard initializer
        """
        e = envelope.Envelope(0.0, 0.0, 10.0, 10.0)
        self.assertEqual(e.x_min, 0.0)
        self.assertEqual(e.y_min, 0.0)
        self.assertEqual(e.x_max, 10.0)
        self.assertEqual(e.y_max, 10.0)

    def test_insufficient_arguments(self):
        """
        Test too few or too many arguments passed to the constructor
        """
        self.assertRaises(TypeError, envelope.Envelope, 0.0, 0.0, 10.0)
        self.assertRaises(TypeError, envelope.Envelope, 0.0, 0.0, 10.0,
            10.0, 10.0)

    def test_incorrect_dimensions(self):
        """
        Test invalid envelope shapes (point, line, inverted polygon)
        """
        self.assertRaises(envelope.EnvelopeError, envelope.Envelope, 0.0,
            0.0, 0.0, 0.0)
        self.assertRaises(envelope.EnvelopeError, envelope.Envelope, 0.0,
            0.0, 10.0, 0.0)
        self.assertRaises(envelope.EnvelopeError, envelope.Envelope, 10.0,
            10.0, 0.0, 0.0)

    def test_relationships(self):
        """
        Test relationships between envelopes
        """
        a = envelope.Envelope(0.0, 0.0, 10.0, 10.0)
        b = envelope.Envelope(0.0, 0.0, 10.0, 10.0)
        c = envelope.Envelope(1.0, 1.0, 9.0, 9.0)
        d = envelope.Envelope(10.0, 10.0, 20.0, 20.0)

        # a and b are equal and subsets and supersets of each other
        self.assert_(a == b)
        self.assertTrue(a.is_subset(b))
        self.assertTrue(b.is_subset(a))
        self.assertTrue(a.is_superset(b))
        self.assertTrue(b.is_superset(a))

        # c is a subset of a
        self.assertTrue(c.is_subset(a))
        self.assertFalse(c.is_disjoint(a))

        # a is a superset of c
        self.assertTrue(a.is_superset(c))
        self.assertFalse(a.is_disjoint(c))

        # d is disjoint from c, but shares a common point with a
        self.assertFalse(a.is_disjoint(d))
        self.assertTrue(c.is_disjoint(d))
        self.assertFalse(d.is_disjoint(a))
        self.assertTrue(d.is_disjoint(c))

    def test_set_operations(self):
        """
        Test various set operations
        """
        a = envelope.Envelope(3.0, 3.0, 10.0, 10.0)
        b = envelope.Envelope(0.0, 0.0, 7.0, 7.0)
        union = envelope.Envelope(0.0, 0.0, 10.0, 10.0)
        intersection = envelope.Envelope(3.0, 3.0, 7.0, 7.0)

        # Union
        c = a.union(b)
        self.assertEqual(c, union)

        # Intersection
        c = a.intersection(b)
        self.assertEqual(c, intersection)


class RasterEnvelopeTest(unittest.TestCase):
    """
    RasterEnvelope class tests
    """
    def test_default(self):
        """
        Test common use case setting all four corners and cell size of the
        RasterEnvelope and return attributes
        """
        re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        self.assertEqual(re.x_min, 0.0)
        self.assertEqual(re.y_min, 0.0)
        self.assertEqual(re.x_max, 10.0)
        self.assertEqual(re.y_max, 10.0)
        self.assertEqual(re.x_size, 10)
        self.assertEqual(re.y_size, 10)
        self.assertEqual(re.cell_size, 1.0)

        re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 0.1)
        self.assertEqual(re.x_min, 0.0)
        self.assertEqual(re.y_min, 0.0)
        self.assertEqual(re.x_max, 10.0)
        self.assertEqual(re.y_max, 10.0)
        self.assertEqual(re.x_size, 100)
        self.assertEqual(re.y_size, 100)
        self.assertEqual(re.cell_size, 0.1)

    def test_insufficient_arguments(self):
        """
        Test insufficient arguments passed to constructor
        """
        self.assertRaises(TypeError, envelope.RasterEnvelope, 0.0,
            10.0, 1.0)

    def test_incorrect_dimensions(self):
        """
        Test cases when coordinates are incorrect
        """
        self.assertRaises(
            envelope.EnvelopeError, envelope.RasterEnvelope, 0.0, 20.0,
                -10.0, 10.0, 1.0)
        self.assertRaises(
            envelope.EnvelopeError, envelope.RasterEnvelope, 0.0, 0.0,
                0.0, 0.0, 1.0)

    def test_snapped_subset(self):
        """
        Test functionality of is_snapped_subset
        """
        re_1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)

        re_2 = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        self.assertTrue(re_2.is_snapped_subset(re_1))

        re_3 = envelope.RasterEnvelope(1.2, 1.0, 10.2, 9.0, 1.0)
        self.assertFalse(re_3.is_snapped_subset(re_1))

    def test_grow_window(self):
        """
        Test giving coordinates that aren't multiples of cell_size, ensure
        that the window grows appropriately
        """
        re = envelope.RasterEnvelope(0.0, 0.3, 9.6, 10.0, 1.0)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        self.assert_(re == check_re)

    def test_union(self):
        """
        Test unioning of different RasterEnvelopes using different options
        """
        # re1 is a snapped subset of re2
        re1 = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        re2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re3 = re1.union(re2, snap_this=True)
        self.assert_(re3 == check_re)
        re3 = re1.union(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is a non-snapped subset of re2
        re1 = envelope.RasterEnvelope(1.2, 1.2, 9.2, 9.2, 1.0)
        re2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        check_re = envelope.RasterEnvelope(-0.8, -0.8, 10.2, 10.2, 1.0)
        re3 = re1.union(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re3 = re1.union(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is a snapped superset of re2
        re1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re2 = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re3 = re1.union(re2, snap_this=True)
        self.assert_(re3 == check_re)
        re3 = re1.union(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is a non-snapped superset of re2
        re1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re2 = envelope.RasterEnvelope(1.2, 1.2, 9.2, 9.2, 1.0)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re3 = re1.union(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(-0.8, -0.8, 10.2, 10.2, 1.0)
        re3 = re1.union(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 overlaps re2 but is not a subset
        re1 = envelope.RasterEnvelope(0.0, 0.0, 5.0, 5.0, 1.0)
        re2 = envelope.RasterEnvelope(4.2, 4.2, 9.2, 9.2, 1.0)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re3 = re1.union(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(-0.8, -0.8, 9.2, 9.2, 1.0)
        re3 = re1.union(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is disjoint from re2
        re1 = envelope.RasterEnvelope(0.0, 0.0, 5.0, 5.0, 1.0)
        re2 = envelope.RasterEnvelope(5.2, 5.2, 9.2, 9.2, 1.0)
        check_re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re3 = re1.union(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(-0.8, -0.8, 9.2, 9.2, 1.0)
        re3 = re1.union(re2, snap_this=False)
        self.assert_(re3 == check_re)

    def test_intersection(self):
        """
        Test intersection of different RasterEnvelopes using different options
        """
        # re1 is a snapped subset of re2
        re1 = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        re2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        check_re = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        re3 = re1.intersection(re2, snap_this=True)
        self.assert_(re3 == check_re)
        re3 = re1.intersection(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is a non-snapped subset of re2
        re1 = envelope.RasterEnvelope(1.2, 1.2, 9.2, 9.2, 1.0)
        re2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        check_re = envelope.RasterEnvelope(1.2, 1.2, 9.2, 9.2, 1.0)
        re3 = re1.intersection(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(1.0, 1.0, 10.0, 10.0, 1.0)
        re3 = re1.intersection(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is a snapped superset of re2
        re1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re2 = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        check_re = envelope.RasterEnvelope(1.0, 1.0, 9.0, 9.0, 1.0)
        re3 = re1.intersection(re2, snap_this=True)
        self.assert_(re3 == check_re)
        re3 = re1.intersection(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is a non-snapped superset of re2
        re1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re2 = envelope.RasterEnvelope(1.2, 1.2, 9.2, 9.2, 1.0)
        check_re = envelope.RasterEnvelope(1.0, 1.0, 10.0, 10.0, 1.0)
        re3 = re1.intersection(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(1.2, 1.2, 9.2, 9.2, 1.0)
        re3 = re1.intersection(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 overlaps re2 but is not a subset
        re1 = envelope.RasterEnvelope(0.0, 0.0, 5.0, 5.0, 1.0)
        re2 = envelope.RasterEnvelope(4.2, 4.2, 9.2, 9.2, 1.0)
        check_re = envelope.RasterEnvelope(4.0, 4.0, 5.0, 5.0, 1.0)
        re3 = re1.intersection(re2, snap_this=True)
        self.assert_(re3 == check_re)
        check_re = envelope.RasterEnvelope(4.2, 4.2, 5.2, 5.2, 1.0)
        re3 = re1.intersection(re2, snap_this=False)
        self.assert_(re3 == check_re)

        # re1 is disjoint from re2 - no result
        re1 = envelope.RasterEnvelope(0.0, 0.0, 5.0, 5.0, 1.0)
        re2 = envelope.RasterEnvelope(5.2, 5.2, 9.2, 9.2, 1.0)
        self.assertRaises(envelope.EnvelopeError, re1.intersection, re2)

    def test_get_offset(self):
        """
        Test method get_offset_from_xy
        """
        re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        (x_off, y_off) = re.get_offset_from_xy(0.3, 9.5)
        self.assertEqual((x_off, y_off), (0, 0))
        (x_off, y_off) = re.get_offset_from_xy(9.7, 0.3)
        self.assertEqual((x_off, y_off), (9, 9))

        re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 5.0)
        (x_off, y_off) = re.get_offset_from_xy(0.3, 9.5)
        self.assertEqual((x_off, y_off), (0, 0))
        (x_off, y_off) = re.get_offset_from_xy(9.7, 0.3)
        self.assertEqual((x_off, y_off), (1, 1))

        re = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 7.0)
        (x_off, y_off) = re.get_offset_from_xy(0.3, 9.5)
        self.assertEqual((x_off, y_off), (0, 0))
        (x_off, y_off) = re.get_offset_from_xy(12.0, 0.3)
        self.assertEqual((x_off, y_off), (1, 1))

    def test_min_of(self):
        """
        Test methods min_of and max_of
        """
        re_1 = envelope.RasterEnvelope(1.0, 1.0, 4.0, 4.0, 1.0)
        re_2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re_3 = envelope.RasterEnvelope(0.0, 0.0, 20.0, 20.0, 1.0)
        min_re = envelope.min_of((re_1, re_2, re_3))
        self.assert_(re_1 == min_re)

        re_1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re_2 = envelope.RasterEnvelope(1.0, 1.0, 4.0, 4.0, 1.0)
        re_3 = envelope.RasterEnvelope(0.0, 0.0, 20.0, 20.0, 1.0)
        min_re = envelope.min_of((re_1, re_2, re_3))
        self.assert_(re_2 == min_re)

        re_1 = envelope.RasterEnvelope(1.2, 1.2, 3.2, 3.2, 1.0)
        re_2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re_3 = envelope.RasterEnvelope(0.0, 0.0, 20.0, 20.0, 1.0)
        min_re = envelope.min_of((re_1, re_2, re_3))
        self.assert_(re_1 == min_re)
        check_re = envelope.RasterEnvelope(1.0, 1.0, 4.0, 4.0, 1.0)
        min_re = envelope.min_of((re_1, re_2, re_3), snap_re=re_2)
        self.assert_(check_re == min_re)
        min_re = envelope.min_of((re_2, re_1, re_3))
        self.assert_(check_re == min_re)

        re_1 = envelope.RasterEnvelope(1.0, 1.0, 4.0, 4.0, 1.0)
        re_2 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re_3 = envelope.RasterEnvelope(0.0, 0.0, 20.0, 20.0, 1.0)
        max_re = envelope.max_of((re_1, re_2, re_3))
        self.assert_(re_3 == max_re)

        re_1 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        re_2 = envelope.RasterEnvelope(0.0, 0.0, 20.0, 20.0, 1.0)
        re_3 = envelope.RasterEnvelope(1.0, 1.0, 4.0, 4.0, 1.0)
        max_re = envelope.max_of((re_1, re_2, re_3))
        self.assert_(re_2 == max_re)

        re_1 = envelope.RasterEnvelope(0.0, 0.0, 20.0, 20.0, 1.0)
        re_2 = envelope.RasterEnvelope(1.2, 1.2, 3.2, 3.2, 1.0)
        re_3 = envelope.RasterEnvelope(0.0, 0.0, 10.0, 10.0, 1.0)
        max_re = envelope.max_of((re_1, re_2, re_3))
        self.assert_(re_1 == max_re)
        check_re = envelope.RasterEnvelope(-0.8, -0.8, 20.2, 20.2, 1.0)
        max_re = envelope.max_of((re_1, re_2, re_3), snap_re=re_2)
        self.assert_(check_re == max_re)
        max_re = envelope.max_of((re_2, re_1, re_3))
        self.assert_(check_re == max_re)

    def test_from_gdal_dataset(self):
        """
        Test method from_gdal_dataset
        """
        from osgeo import gdal, gdalconst
        ds = gdal.Open('./data/dem.tif', gdalconst.GA_ReadOnly)
        re = envelope.RasterEnvelope.from_gdal_dataset(ds)
        self.assertEqual(re.x_min, -2130015.0)
        self.assertEqual(re.y_min, 2580015.0)
        self.assertEqual(re.x_max, -2127015.0)
        self.assertEqual(re.y_max, 2583015.0)
        self.assertEqual(re.x_size, 100)
        self.assertEqual(re.y_size, 100)
        self.assertEqual(re.cell_size, 30.0)


if __name__ == '__main__':
    unittest.main()
