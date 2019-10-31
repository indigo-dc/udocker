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
        pass

    def tearDown(self):
        pass

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
        """Test CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            curl_header = CurlHeader()
            self.assertTrue(curl_header.setvalue_from_file("filename"))
            self.assertTrue(mock_write.called_with('XXXX'))

    def test_04_getvalue(self):
        """Test CurlHeader().getvalue()."""
        curl_header = CurlHeader()
        curl_header.data = "XXXX"
        status = curl_header.getvalue()
        self.assertEqual(status, curl_header.data)


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
        self.conf['use_curl_exec'] = ""

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @patch.object(GetURLexeCurl, '_select_implementation')
    @patch.object(GetURLexeCurl, 'is_available')
    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg')
    def test_01_init(self, mock_msg, mock_gupycurl,
                     mock_guexecurl, mock_select):
        """Test GetURL() constructor."""
        mock_msg.level = 0
        mock_gupycurl.return_value = False
        mock_guexecurl.return_value = True
        geturl = GetURL(self.conf)
        mock_select.assert_called()
        self.assertEqual(geturl.ctimeout, self.conf['ctimeout'])
        self.assertEqual(geturl.insecure, self.conf['http_insecure'])
        self.assertFalse(geturl.cache_support)

    @patch('udocker.utils.curl.Msg')
    @patch.object(GetURLexeCurl, 'is_available')
    @patch.object(GetURLpyCurl, 'is_available')
    def test_02__select_implementation(self, mock_gupycurl, mock_guexecurl, mock_msg):
        """Test GetURL()._select_implementation()."""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        geturl = GetURL(self.conf)
        geturl._select_implementation()
        self.assertTrue(geturl.cache_support)

        mock_gupycurl.return_value = False
        geturl = GetURL(self.conf)
        geturl._select_implementation()
        self.assertFalse(geturl.cache_support)

        mock_guexecurl.return_value = False
        with self.assertRaises(NameError):
            GetURL(self.conf)

    def test_03_get_content_length(self):
        """Test GetURL().get_content_length()."""
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        geturl = GetURL(self.conf)
        self.assertEqual(geturl.get_content_length(hdr), 10)

        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": dict(), }
        geturl = GetURL(self.conf)
        self.assertEqual(geturl.get_content_length(hdr), -1)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test GetURL().set_insecure()."""
        mock_gupycurl.return_value = True
        geturl = GetURL(self.conf)
        geturl.set_insecure()
        self.assertEqual(geturl.insecure, True)

        geturl = GetURL(self.conf)
        geturl.set_insecure(False)
        self.assertEqual(geturl.insecure, False)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test GetURL().set_proxy()."""
        mock_gupycurl.return_value = True
        geturl = GetURL(self.conf)
        geturl.set_proxy("http://host")
        self.assertEqual(geturl.http_proxy, "http://host")

    def test_06_get(self):
        """Test GetURL().get() generic get."""
        geturl = GetURL(self.conf)
        self.assertRaises(TypeError, geturl.get)

        geturl = GetURL(self.conf)
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")

    def test_07_post(self):
        """Test GetURL().post() generic post."""
        geturl = GetURL(self.conf)
        self.assertRaises(TypeError, geturl.post)
        self.assertRaises(TypeError, geturl.post, "http://host")

        geturl = GetURL(self.conf)
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        status = geturl.post("http://host", {"DATA": 1, })
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

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @patch('udocker.utils.curl.Msg')
    @patch.object(GetURLpyCurl, 'is_available')
    def test_01_is_available(self, mock_gupycurl, mock_msg):
        """Test GetURLpyCurl()._is_available()."""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        geturl = GetURLpyCurl(self.conf)
        geturl.is_available()
        self.assertTrue(geturl.is_available())

        mock_gupycurl.return_value = False
        geturl = GetURLpyCurl(self.conf)
        self.assertFalse(geturl.is_available())

    def test_02__select_implementation(self):
        """Test GetURLpyCurl()._select_implementation()."""
        pass

    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.pycurl')
    @patch('udocker.utils.curl.CurlHeader')
    def test_03__set_defaults(self, mock_hdr, mock_pyc,
                              mock_msg, mock_selinsec):
        """Test GetURLpyCurl()._set_defaults()."""
        mock_selinsec.return_value = True
        mock_msg.level = 0
        mock_msg.VER = 4
        geturl = GetURLpyCurl(self.conf)
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

        # when Msg.level >= Msg.VER = 4: AND insecure
        mock_msg.level = 5
        mock_msg.VER = 4
        geturl = GetURLpyCurl(self.conf)
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 18)

        mock_selinsec.return_value = True
        # when Msg.level < Msg.VER = 4: AND secure
        mock_msg.level = 2
        mock_msg.VER = 4
        geturl = GetURLpyCurl(self.conf)
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 27)

    # TODO: proper implement test
    # @patch.object(GetURLpyCurl, 'is_available')
    # @patch('udocker.utils.curl.Msg')
    # @patch('udocker.utils.curl.pycurl')
    # @patch('udocker.utils.curl.CurlHeader')
    # def test_04__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
    #     """Test GetURL()._mkpycurl()."""
    #     mock_sel.return_value = True
    #     geturl = GetURLpyCurl(self.conf)
    #     geturl._mkpycurl(mock_pyc, mock_hdr)
    #     self.assertTrue(mock_pyc.setopt.called)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_05_get(self, mock_sel):
        """Test GetURLpyCurl().get() generic get."""
        geturl = GetURLpyCurl(self.conf)
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        status = geturl.get("http://host")
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
        geturl = GetURLexeCurl(self.conf)
        self.assertIsNone(geturl._opts)

        geturl = GetURLexeCurl(self.conf)
        self.assertIsNone(geturl._files)

    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.FileUtil.find_exec')
    def test_02_is_available(self, mock_findexec, mock_msg):
        """Test GetURLexeCurl()._is_available()."""
        mock_msg.level = 0
        mock_findexec.return_value = "/tmp"
        geturl = GetURLexeCurl(self.conf)
        self.assertTrue(geturl.is_available())

        mock_findexec.return_value = ""
        geturl = GetURLexeCurl(self.conf)
        self.assertFalse(geturl.is_available())

    def test_03__select_implementation(self):
        """Test GetURLexeCurl()._select_implementation()."""
        pass

    @patch('udocker.utils.curl.Msg')
    def test_04__set_defaults(self, mock_msg):
        """Set defaults for curl command line options"""
        mock_msg.level = 0
        mock_msg.VER = 4
        geturl = GetURLexeCurl(self.conf)
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "")

        mock_msg.level = 0
        mock_msg.VER = 4
        geturl = GetURLexeCurl(self.conf)
        geturl.insecure = True
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "-k")

        mock_msg.level = 5
        mock_msg.VER = 4
        geturl = GetURLexeCurl(self.conf)
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
