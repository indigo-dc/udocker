#!/usr/bin/env python
"""
udocker unit tests: CurlHeader
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

sys.path.append('.')

from udocker.utils.curl import CurlHeader

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"



class CurlHeaderTestCase(TestCase):
    """Test CurlHeader() http header parser."""

    def setUp(self):
        self.curl_header = CurlHeader()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test CurlHeader() constructor."""
        self.assertFalse(self.curl_header.sizeonly)
        self.assertIsInstance(self.curl_header.data, dict)
        self.assertEqual("", self.curl_header.data["X-ND-HTTPSTATUS"])
        self.assertEqual("", self.curl_header.data["X-ND-CURLSTATUS"])

    def test_02_write(self):
        """Test CurlHeader().write()."""
        buff = ["HTTP/1.1 200 OK",
                "Content-Type: application/octet-stream",
                "Content-Length: 32", ]
        for line in buff:
            self.curl_header.write(line)
        status = self.curl_header.data["content-type"]
        self.assertEqual(status, "application/octet-stream")
        status = self.curl_header.data["X-ND-HTTPSTATUS"]
        self.assertEqual(status, "HTTP/1.1 200 OK")
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

    @patch('udocker.utils.curl.CurlHeader.write')
    def test_03_setvalue_from_file(self, mock_write):
        """Test CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            self.assertTrue(self.curl_header.setvalue_from_file("filename"))
            mock_write.assert_called_with('XXXX')

    def test_04_getvalue(self):
        """Test CurlHeader().getvalue()."""
        self.curl_header.data = "XXXX"
        status = self.curl_header.getvalue()
        self.assertEqual(status, self.curl_header.data)


if __name__ == '__main__':
    main()
