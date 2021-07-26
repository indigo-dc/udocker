#!/usr/bin/env python
"""
udocker unit tests: ChkSUM
"""
from unittest import TestCase, main
from unittest.mock import patch, mock_open
from io import BytesIO as strio
from udocker.utils.chksum import ChkSUM, LOG

class ChkSUMTestCase(TestCase):
    """Test ChkSUM()."""
    def setUp(self):
        LOG.setLevel(100)


    def test_01_hash(self):
        """Test01 ChkSUM().hash."""
        file_data = strio(b'qwertyui\n')
        sha256sum = ("42e6d97f00bff046ae2dea5c6db56d866ae749fb7dc05319e08e5fbee31d851c")
        cksum = ChkSUM()
        with patch('builtins.open', mock_open()) as mopen:
            mopen.return_value = file_data
            status = cksum.hash("filename", "sha256")
            self.assertEqual(status, sha256sum)

        file_data = strio(b'qwertyui\n')
        sha512sum =("2a260f37d0e522ecb43d93f23bfbbe88846da321f9eb1a9b552b74"
                    "d1fe356ef20506b06f1ab639e0e0b028e85404e0f6eee3deba3f7a2367de54af8a079ba823")
        cksum = ChkSUM()
        with patch('builtins.open', mock_open()) as mopen:
            mopen.return_value = file_data
            status = cksum.hash("filename", "sha512")
            self.assertEqual(status, sha512sum)


if __name__ == '__main__':
    main()
