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


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class ChkSUMTestCase(TestCase):
    """Test ChkSUM() performs checksums portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        pass

    # TODO: review tests
    @patch('udocker.utils.chksum.hashlib')
    def test_01_sha256(self, mock_hashlib):
        """Test ChkSUM().sha256()."""
        self._init()
        mock_call = MagicMock()
        cksum = ChkSUM()
        #
        mock_call.return_value = True
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertTrue(status)
        #
        mock_call.return_value = False
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertFalse(status)


if __name__ == '__main__':
    main()
