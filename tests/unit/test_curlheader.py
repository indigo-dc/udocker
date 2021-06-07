#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CurlHeader
"""
import sys
from unittest import TestCase, main
from udocker.utils.curl import CurlHeader
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


class CurlHeaderTestCase(TestCase):
    """Test CurlHeader() http header parser."""

    def test_01_init(self):
        """Test01 CurlHeader() constructor."""
        curl_header = CurlHeader()
        self.assertFalse(curl_header.sizeonly)
        self.assertIsInstance(curl_header.data, dict)
        self.assertEqual("", curl_header.data["X-ND-HTTPSTATUS"])
        self.assertEqual("", curl_header.data["X-ND-CURLSTATUS"])

    def test_02_write(self):
        """Test02 CurlHeader().write()."""
        buff = ["HTTP/1.1 200 OK",
                "Content-Type: application/octet-stream",
                "Content-Length: 32", ]
        curl_header = CurlHeader()
        for line in buff:
            curl_header.write(line)
        status = curl_header.data["content-type"]
        self.assertEqual(status, "application/octet-stream")
        status = curl_header.data["X-ND-HTTPSTATUS"]
        self.assertEqual(status, "HTTP/1.1 200 OK")

        curl_header = CurlHeader()
        for line in buff:
            curl_header.write(line)
        buff_out = curl_header.getvalue()
        self.assertTrue("HTTP/1.1 200 OK" in buff_out)

        line = ""
        curl_header = CurlHeader()
        curl_header.sizeonly = True
        self.assertEqual(-1, curl_header.write(line))

    @patch.object(CurlHeader, 'write')
    def test_03_setvalue_from_file(self, mock_write):
        """Test03 CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            curl_header = CurlHeader()
            self.assertTrue(curl_header.setvalue_from_file("filename"))
            self.assertTrue(mock_write.called_with('XXXX'))

    def test_04_getvalue(self):
        """Test04 CurlHeader().getvalue()."""
        curl_header = CurlHeader()
        curl_header.data = "XXXX"
        status = curl_header.getvalue()
        self.assertEqual(status, curl_header.data)


if __name__ == '__main__':
    main()
