#!/usr/bin/env python
"""
udocker unit tests: Unique
"""

from unittest import TestCase, main
from udocker.helper.unique import Unique


class UniqueTestCase(TestCase):
    """Test Unique() class."""

    def test_01_init(self):
        """Test01 Unique() constructor."""
        uniq = Unique()
        self.assertEqual(uniq.def_name, "udocker")

    def test_02__rnd(self):
        """Test02 Unique._rnd()."""
        uniq = Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_03_uuid(self):
        """Test03 Unique.uuid()."""
        uniq = Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_04_imagename(self):
        """Test04 Unique.imagename()."""
        uniq = Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_05_imagetag(self):
        """Test05 Unique.imagetag()."""
        uniq = Unique()
        rand = uniq.imagetag()
        self.assertEqual(len(rand), 10)

    def test_06_layer_v1(self):
        """Test06 Unique.layer_v1()."""
        uniq = Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_07_filename(self):
        """Test07 Unique.filename()."""
        uniq = Unique()
        rand = uniq.filename("zxcvbnmasdf")
        self.assertTrue(rand.endswith("zxcvbnmasdf"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 56)
        rand = uniq.filename(12345)
        self.assertTrue(rand.endswith("12345"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 50)


if __name__ == '__main__':
    main()
