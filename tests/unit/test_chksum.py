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
import sys
import unittest
import mock
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.utils.chksum import ChkSUM

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


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

    @mock.patch('udocker.utils.chksum.hashlib.sha256')
    def test_01_init(self, mock_hashlib_sha):
        """Test ChkSUM() constructor."""
        self._init()
        mock_hashlib_sha.return_value = True
        cksum = ChkSUM()
        self.assertEqual(cksum._sha256_call, cksum._hashlib_sha256)

    def test_02_sha256(self):
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

    def test_03__hashlib_sha256(self):
        """Test ChkSUM()._hashlib_sha256()."""
        sha256sum = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self._init()
        cksum = ChkSUM()
        file_data = StringIO("qwerty")
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum._hashlib_sha256("filename")
            self.assertEqual(status, sha256sum)

    @mock.patch('udocker.utils.uprocess.Uprocess.get_output')
    @mock.patch('udocker.msg.Msg')
    def test_04__openssl_sha256(self, mock_msg, mock_subproc):
        """Test ChkSUM()._openssl_sha256()."""
        self._init()
        Msg = mock_msg
        Msg.return_value.chlderr = open("/dev/null", "w")
        Msg.chlderr = open("/dev/null", "w")
        mock_subproc.return_value = "123456 "
        cksum = ChkSUM()
        status = cksum._openssl_sha256("filename")
        self.assertEqual(status, "123456")


if __name__ == '__main__':
    unittest.main()
