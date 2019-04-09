#!/usr/bin/env python2
"""
udocker unit tests.
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import unittest
import mock
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.utils.chksum import ChkSUM


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class ChkSUMTestCase(unittest.TestCase):
    """Test ChkSUM() performs checksums portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        pass

    def test_01_sha256(self):
        """Test ChkSUM().sha256()."""
        self._init()
        mock_call = mock.MagicMock()
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
    unittest.main()
