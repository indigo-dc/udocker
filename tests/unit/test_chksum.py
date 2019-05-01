#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: ChkSUM
"""
import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.utils.chksum import ChkSUM

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


class ChkSUMTestCase(TestCase):
    """Test ChkSUM() performs checksums portably."""
    def test_01_sha256(self):
        """Test ChkSUM().sha256()."""
        sha256sum = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        cksum = ChkSUM()
        #
        file_data = StringIO("qwerty")
        with patch(BUILTINS + '.open', mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum.sha256("filename")
            self.assertEqual(status, sha256sum)


if __name__ == '__main__':
    main()
