#!/usr/bin/env python

# -*- coding: utf-8 -*-
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
from udocker.utils.curl import GetURL
from udocker.utils.curl import GetURLpyCurl
from udocker.utils.curl import GetURLexeCurl
from udocker.config import Config

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
        """Test CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            self.assertTrue(self.curl_header.setvalue_from_file("filename"))
            self.assertTrue(mock_write.called_with('XXXX'))

    def test_04_getvalue(self):
        """Test CurlHeader().getvalue()."""
        self.curl_header.data = "XXXX"
        status = self.curl_header.getvalue()
        self.assertEqual(status, self.curl_header.data)


class GetURLTestCase(TestCase):
    """Test GetURL() perform http operations portably."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['timeout'] = 1
        self.conf['ctimeout'] = 1
        self.conf['download_timeout'] = 1
        self.conf['http_agent'] = ""
        self.conf['http_proxy'] = ""
        self.conf['http_insecure'] = 0
        self.conf['use_curl_executable'] = ""
        self.geturl = GetURL(self.conf)

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @patch.object(GetURLexeCurl, '_select_implementation')
    @patch.object(GetURLexeCurl, 'is_available')
    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg.level')
    def test_01_init(self, mock_level, mock_gupycurl,
                     mock_guexecurl, mock_select):
        """Test GetURL() constructor."""
        mock_level.return_value = 0
        mock_gupycurl.return_value = False
        mock_guexecurl.return_value = True
        self.geturl = GetURL(self.conf)
        mock_select.assert_called()
        self.assertEqual(self.geturl.ctimeout, self.conf['ctimeout'])
        self.assertEqual(self.geturl.insecure, self.conf['http_insecure'])
        self.assertFalse(self.geturl.cache_support)

    @patch('udocker.utils.curl.Msg')
    @patch.object(GetURLexeCurl, 'is_available')
    @patch.object(GetURLpyCurl, 'is_available')
    def test_02__select_implementation(self, mock_gupycurl, mock_guexecurl, mock_msg):
        """Test GetURL()._select_implementation()."""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        self.geturl._select_implementation()
        self.assertTrue(self.geturl.cache_support)

        mock_gupycurl.return_value = False
        self.geturl = GetURL(self.conf)
        self.geturl._select_implementation()
        self.assertFalse(self.geturl.cache_support)

        mock_guexecurl.return_value = False
        with self.assertRaises(NameError):
            GetURL(self.conf)

    def test_03_get_content_length(self):
        """Test GetURL().get_content_length()."""
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        self.assertEqual(self.geturl.get_content_length(hdr), 10)

        hdr.data = {"content-length": dict(), }
        self.assertEqual(self.geturl.get_content_length(hdr), -1)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test GetURL().set_insecure()."""
        mock_gupycurl.return_value = True
        self.geturl.set_insecure()
        self.assertEqual(self.geturl.insecure, True)

        self.geturl.set_insecure(False)
        self.assertEqual(self.geturl.insecure, False)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test GetURL().set_proxy()."""
        mock_gupycurl.return_value = True
        self.geturl.set_proxy("http://host")
        self.assertEqual(self.geturl.http_proxy, "http://host")

    def test_06_get(self):
        """Test GetURL().get() generic get."""
        self.assertRaises(TypeError, self.geturl.get)

        self.geturl._geturl = type('test', (object,), {})()
        self.geturl._geturl.get = self._get
        self.assertEqual(self.geturl.get("http://host"), "http://host")

    def test_07_post(self):
        """Test GetURL().post() generic post."""
        self.assertRaises(TypeError, self.geturl.post)
        self.assertRaises(TypeError, self.geturl.post, "http://host")

        self.geturl._geturl = type('test', (object,), {})()
        self.geturl._geturl.get = self._get
        status = self.geturl.post("http://host", {"DATA": 1, })
        self.assertEqual(status, "http://host")


class GetURLpyCurlTestCase(TestCase):
    """GetURLpyCurl TestCase."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['timeout'] = 1
        self.conf['ctimeout'] = 1
        self.conf['download_timeout'] = 1
        self.conf['http_agent'] = ""
        self.conf['http_proxy'] = ""
        self.conf['http_insecure'] = 0
        self.geturl = GetURLpyCurl(self.conf)

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @patch('udocker.utils.curl.Msg.level')
    @patch.object(GetURLpyCurl, 'is_available')
    def test_01_is_available(self, mock_gupycurl, mock_level):
        """Test GetURLpyCurl()._is_available()."""
        mock_level.return_value = 0
        self.geturl.is_available()
        mock_gupycurl.return_value = True
        self.assertTrue(self.geturl.is_available())

        mock_gupycurl.return_value = False
        self.assertFalse(self.geturl.is_available())

    def test_02__select_implementation(self):
        """Test GetURLpyCurl()._select_implementation()."""
        pass

    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg.level')
    @patch('udocker.utils.curl.pycurl')
    @patch('udocker.utils.curl.CurlHeader')
    def test_03__set_defaults(self, mock_hdr, mock_pyc,
                              mock_level, mock_selinsec):
        """Test GetURLpyCurl()._set_defaults()."""
        mock_selinsec.return_value = True
        self.geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

        # when Msg.level >= Msg.VER = 4: AND insecure
        mock_level.return_value = 5
        self.geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 18)

        mock_selinsec.return_value = True
        # when Msg.level < Msg.VER = 4: AND secure
        mock_level.return_value = 2
        self.geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 27)

    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.pycurl')
    @patch('udocker.utils.curl.CurlHeader')
    def test_04__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
        """Test GetURL()._mkpycurl()."""
        mock_sel.return_value = True
        self.geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_05_get(self, mock_sel):
        """Test GetURLpyCurl().get() generic get."""
        self.geturl._geturl = type('test', (object,), {})()
        self.geturl.get = self._get
        status = self.geturl.get("http://host")
        self.assertEqual(status, "http://host")


class GetURLexeCurlTestCase(TestCase):
    """GetURLexeCurl TestCase."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['timeout'] = 1
        self.conf['ctimeout'] = 1
        self.conf['download_timeout'] = 1
        self.conf['http_agent'] = ""
        self.conf['http_proxy'] = ""
        self.conf['http_insecure'] = 0

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.GetURL')
    def test_01_init(self, mock_gcurl, mock_msg):
        """Test GetURLexeCurl() constructor."""
        self.assertIsNone(GetURLexeCurl(self.conf)._opts)
        self.assertIsNone(GetURLexeCurl(self.conf)._files)

    @patch('udocker.utils.curl.Msg.level')
    @patch('udocker.utils.curl.FileUtil.find_exec')
    def test_02_is_available(self, mock_findexec, mock_level):
        """Test GetURLexeCurl()._is_available()."""
        mock_level.return_value = 0
        geturl = GetURLexeCurl(self.conf)
        mock_findexec.return_value = "/tmp"
        self.assertTrue(geturl.is_available())

        mock_findexec.return_value = ""
        self.assertFalse(geturl.is_available())

    def test_03__select_implementation(self):
        """Test GetURLexeCurl()._select_implementation()."""
        pass

    @patch('udocker.utils.curl.Msg.level')
    def test_04__set_defaults(self, mock_level):
        """Set defaults for curl command line options"""
        geturl = GetURLexeCurl(self.conf)
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "")

        geturl.insecure = True
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "-k")

        mock_level.return_value = 5
        geturl._set_defaults()
        self.assertEqual(geturl._opts["verbose"], "-v")

        self.assertEqual(geturl._files["url"], "")

    def test_05__mkcurlcmd(self):
        """Test GetURLexeCurl()._mkcurlcmd()."""
        pass

    def test_06_get(self):
        """Test GetURLexeCurl().get() generic get."""
        geturl = GetURLexeCurl(self.conf)
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")


if __name__ == '__main__':
    main()
