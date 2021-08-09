#!/usr/bin/env python
"""
udocker unit tests: Uvolume
"""

from unittest import TestCase, main
from udocker.utils.uvolume import Uvolume


class UvolumeTestCase(TestCase):
    """Test Uvolume()."""

    def test_01_init(self):
        """Test01 Uvolume() constructor"""
        volm = '/data'
        uvol = Uvolume(volm)
        self.assertEqual(uvol.volume, volm)

    def test_02_cleanpath(self):
        """Test02 Uvolume().cleanpath()."""
        path = '/bin/ls'
        volm = '/data'
        uvol = Uvolume(volm)
        result = uvol.cleanpath(path)
        self.assertEqual(result, path)

        path2 = '//bin//ls'
        volm = '/data'
        uvol = Uvolume(volm)
        result = uvol.cleanpath(path2)
        self.assertEqual(result, path)

    def test_03_split(self):
        """Test03 Uvolume().split()."""
        volm = '/data:/contdata'
        uvol = Uvolume(volm)
        result = uvol.split()
        self.assertEqual(result, ('/data', '/contdata'))

        volm = '/data'
        uvol = Uvolume(volm)
        result = uvol.split()
        self.assertEqual(result, ('/data', '/data'))


if __name__ == '__main__':
    main()
