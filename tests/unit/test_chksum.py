#!/usr/bin/env python
"""
udocker unit tests: ChkSUM
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock, mock_open
from io import BytesIO as strio
from udocker.utils.chksum import ChkSUM

BUILTINS = "builtins"


class ChkSUMTestCase(TestCase):
    """Test ChkSUM()."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # def test_01__init(self):
    #     """Test01 ChkSUM() constructor."""
    #     ChkSUM()

    # def test_02_sha256(self):
    #     """Test02 ChkSUM().sha256."""

    # def test_03_sha512(self):
    #     """Test03 ChkSUM().sha512."""

    # def test_04_hash(self):
    #     """Test04 ChkSUM().hash."""
    #     sha256sum = (
    #       "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    #     cksum = ChkSUM()
    #     file_data = strio('qwerty')
    #     with patch(BUILTINS + '.open', mock_open()) as mopen:
    #         mopen.return_value.__iter__ = (
    #             lambda self: iter(file_data.readline, ''))
    #         status = cksum.hash("filename", "sha256")
    #         self.assertEqual(status, sha256sum)
    #     sha512sum = ("cf83e1357eefb8bdf1542850d66d8007d620e4050b"
    #                  "5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff831"
    #                  "8d2877eec2f63b931bd47417a81a538327af927da3e")
    #     cksum = ChkSUM()
    #     file_data = strio('qwerty')
    #     with patch(BUILTINS + '.open', mock_open()) as mopen:
    #         mopen.return_value.__iter__ = (
    #             lambda self: iter(file_data.readline, ''))
    #         status = cksum.hash("filename", "sha512")
    #         self.assertEqual(status, sha512sum)


if __name__ == '__main__':
    main()
