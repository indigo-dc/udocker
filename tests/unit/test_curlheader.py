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
from StringIO import StringIO

sys.path.append('.')

from udocker.utils.curl import CurlHeader

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"

def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class CurlHeaderTestCase(unittest.TestCase):
    """Test CurlHeader() http header parser."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test CurlHeader() constructor."""
        curl_header = CurlHeader()
        self.assertFalse(curl_header.sizeonly)
        self.assertIsInstance(curl_header.data, dict)
        self.assertEqual("", curl_header.data["X-ND-HTTPSTATUS"])
        self.assertEqual("", curl_header.data["X-ND-CURLSTATUS"])

    def test_02_write(self):
        """Test CurlHeader().write()."""
        buff = ["HTTP/1.1 200 OK",
                "Content-Type: application/octet-stream",
                "Content-Length: 32", ]
        curl_header = CurlHeader()
        for line in buff:
            curl_header.write(line)
        self.assertEqual(curl_header.data["content-type"],
                         "application/octet-stream")
        self.assertEqual(curl_header.data["X-ND-HTTPSTATUS"],
                         "HTTP/1.1 200 OK")
        #
        curl_header = CurlHeader()
        for line in buff:
            curl_header.write(line)
        buff_out = curl_header.getvalue()
        self.assertTrue("HTTP/1.1 200 OK" in buff_out)
        #
        line = ""
        curl_header = CurlHeader()
        curl_header.sizeonly = True
        self.assertEqual(-1, curl_header.write(line))

    @mock.patch('udocker.utils.curl.CurlHeader.write')
    def test_03_setvalue_from_file(self, mock_write):
        """Test CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            curl_header = CurlHeader()
            self.assertTrue(curl_header.setvalue_from_file("filename"))
            mock_write.assert_called_with('XXXX')

    def test_04_getvalue(self):
        """Test CurlHeader().getvalue()."""
        curl_header = CurlHeader()
        curl_header.data = "XXXX"
        self.assertEqual(curl_header.getvalue(), curl_header.data)


if __name__ == '__main__':
    unittest.main()
