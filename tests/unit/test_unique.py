#!/usr/bin/env python
"""
udocker unit tests: Unique
"""
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from udocker.helper.unique import Unique


class UniqueTestCase(TestCase):
    """Test Unique() class."""

    def test_01_init(self):
        """Test Unique() constructor."""
        uniq = Unique()
        self.assertEqual(uniq.def_name, "udocker")

    def test_02__rnd(self):
        """Test Unique._rnd()."""
        uniq = Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_03_uuid(self):
        """Test Unique.uuid()."""
        uniq = Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_04_imagename(self):
        """Test Unique.imagename()."""
        uniq = Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_05_layer_v1(self):
        """Test Unique.layer_v1()."""
        uniq = Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_06_filename(self):
        """Test Unique.filename()."""
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
