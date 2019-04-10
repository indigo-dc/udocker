#!/usr/bin/env python
"""
udocker unit tests: ChkSUM
"""

import os
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch
except ImportError:
    from mock import Mock, MagicMock, patch

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.utils.chksum import ChkSUM


class ChkSUMTestCase(TestCase):
    """Test ChkSUM() performs checksums portably."""

    # TODO: review tests
    @patch('udocker.utils.chksum.hashlib')
    def test_01_sha256(self, mock_hashlib):
        """Test ChkSUM().sha256()."""
        sha256sum = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        cksum = ChkSUM()
        #
        file_data = StringIO("qwerty")
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum._hashlib_sha256("filename")
            self.assertEqual(status, sha256sum)

        status = cksum.sha256("filename")
        self.assertTrue(status)
        #
        mock_call.return_value = False
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertFalse(status)


if __name__ == '__main__':
    main()
