#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CurlHeader
"""

from unittest import TestCase, main
from unittest.mock import patch
from io import StringIO
from udocker.utils.curl import CurlHeader
from udocker.utils.curl import GetURL
from udocker.utils.curl import GetURLpyCurl
from udocker.utils.curl import GetURLexeCurl
from udocker.config import Config

BUILTINS = "builtins"


class CurlHeaderTestCase(TestCase):
    """Test CurlHeader() http header parser."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

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


class GetURLTestCase(TestCase):
    """Test GetURL() perform http operations portably."""

    def setUp(self):
        Config().getconf()
        Config().conf['timeout'] = 1
        Config().conf['ctimeout'] = 1
        Config().conf['download_timeout'] = 1
        Config().conf['http_agent'] = ""
        Config().conf['http_proxy'] = ""
        Config().conf['http_insecure'] = 0
        Config().conf['use_curl_exec'] = ""

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
        """Test01 GetURL() constructor."""
        mock_msg.level = 0
        mock_gupycurl.return_value = False
        mock_guexecurl.return_value = True
        geturl = GetURL()
        mock_select.assert_called()
        self.assertEqual(geturl.ctimeout, Config().conf['ctimeout'])
        self.assertEqual(geturl.insecure, Config().conf['http_insecure'])
        self.assertFalse(geturl.cache_support)

    @patch('udocker.utils.curl.Msg')
    @patch.object(GetURLexeCurl, 'is_available')
    @patch.object(GetURLpyCurl, 'is_available')
    def test_02__select_implementation(self, mock_gupycurl,
                                       mock_guexecurl, mock_msg):
        """Test02 GetURL()._select_implementation()."""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        geturl = GetURL()
        geturl._select_implementation()
        # self.assertTrue(geturl.cache_support)

        mock_gupycurl.return_value = False
        geturl = GetURL()
        geturl._select_implementation()
        self.assertFalse(geturl.cache_support)

        mock_guexecurl.return_value = False
        with self.assertRaises(NameError):
            GetURL()

    def test_03_get_content_length(self):
        """Test03 GetURL().get_content_length()."""
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        geturl = GetURL()
        self.assertEqual(geturl.get_content_length(hdr), 10)

        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": dict(), }
        geturl = GetURL()
        self.assertEqual(geturl.get_content_length(hdr), -1)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test04 GetURL().set_insecure()."""
        mock_gupycurl.return_value = True
        geturl = GetURL()
        geturl.set_insecure()
        self.assertEqual(geturl.insecure, True)

        geturl = GetURL()
        geturl.set_insecure(False)
        self.assertEqual(geturl.insecure, False)

    @patch.object(GetURLpyCurl, 'is_available')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test05 GetURL().set_proxy()."""
        mock_gupycurl.return_value = True
        geturl = GetURL()
        geturl.set_proxy("http://host")
        self.assertEqual(geturl.http_proxy, "http://host")

    def test_06_get(self):
        """Test06 GetURL().get()."""
        geturl = GetURL()
        self.assertRaises(TypeError, geturl.get)

        geturl = GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")

    def test_07_post(self):
        """Test07 GetURL().post()."""
        geturl = GetURL()
        self.assertRaises(TypeError, geturl.post)
        self.assertRaises(TypeError, geturl.post, "http://host")

        geturl = GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        status = geturl.post("http://host", {"DATA": 1, })
        self.assertEqual(status, "http://host")

    # def test_08_get_status_code(self):
    #     """Test08 GetURL().get_status_code()."""


class GetURLpyCurlTestCase(TestCase):
    """GetURLpyCurl TestCase."""

    def setUp(self):
        Config().getconf()
        Config().conf['timeout'] = 1
        Config().conf['ctimeout'] = 1
        Config().conf['download_timeout'] = 1
        Config().conf['http_agent'] = ""
        Config().conf['http_proxy'] = ""
        Config().conf['http_insecure'] = 0

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    # def test_01_init(self):
    #     """Test01 GetURLpyCurl() constructor."""

    @patch('udocker.utils.curl.Msg')
    @patch.object(GetURLpyCurl, 'is_available')
    def test_02_is_available(self, mock_gupycurl, mock_msg):
        """Test02 GetURLpyCurl()._is_available()."""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        geturl = GetURLpyCurl()
        geturl.is_available()
        self.assertTrue(geturl.is_available())

        mock_gupycurl.return_value = False
        geturl = GetURLpyCurl()
        self.assertFalse(geturl.is_available())

    # def test_03__select_implementation(self):
    #     """Test03 GetURLpyCurl()._select_implementation()."""

    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.pycurl')
    @patch('udocker.utils.curl.CurlHeader')
    def test_04__set_defaults(self, mock_hdr, mock_pyc,
                              mock_msg, mock_selinsec):
        """Test04 GetURLpyCurl()._set_defaults()."""
        mock_selinsec.return_value = True
        mock_msg.level = 0
        mock_msg.VER = 4
        geturl = GetURLpyCurl()
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

        # when Msg.level >= Msg.VER = 4: AND insecure
        mock_msg.level = 5
        mock_msg.VER = 4
        geturl = GetURLpyCurl()
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 18)

        mock_selinsec.return_value = True
        # when Msg.level < Msg.VER = 4: AND secure
        mock_msg.level = 2
        mock_msg.VER = 4
        geturl = GetURLpyCurl()
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 27)

    # @patch.object(GetURLpyCurl, 'is_available')
    # @patch('udocker.utils.curl.Msg')
    # @patch('udocker.utils.curl.pycurl')
    # @patch('udocker.utils.curl.CurlHeader')
    # def test_05__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
    #     """Test05 GetURLpyCurl()._mkpycurl()."""
    #     mock_sel.return_value = True
    #     geturl = GetURLpyCurl()
    #     geturl._mkpycurl(mock_pyc, mock_hdr)
    #     self.assertTrue(mock_pyc.setopt.called)

    def test_06_get(self):
        """Test06 GetURLpyCurl().get() generic get."""
        geturl = GetURLpyCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        status = geturl.get("http://host")
        self.assertEqual(status, "http://host")


class GetURLexeCurlTestCase(TestCase):
    """GetURLexeCurl TestCase."""

    def setUp(self):
        Config().getconf()
        Config().conf['timeout'] = 1
        Config().conf['ctimeout'] = 1
        Config().conf['download_timeout'] = 1
        Config().conf['http_agent'] = ""
        Config().conf['http_proxy'] = ""
        Config().conf['http_insecure'] = 0

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    def test_01_init(self):
        """Test01 GetURLexeCurl() constructor."""
        geturl = GetURLexeCurl()
        self.assertIsNone(geturl._opts)

        geturl = GetURLexeCurl()
        self.assertIsNone(geturl._files)

    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.FileUtil.find_exec')
    def test_02_is_available(self, mock_findexec, mock_msg):
        """Test02 GetURLexeCurl()._is_available()."""
        mock_msg.level = 0
        mock_findexec.return_value = "/tmp"
        geturl = GetURLexeCurl()
        self.assertTrue(geturl.is_available())

        mock_findexec.return_value = ""
        geturl = GetURLexeCurl()
        self.assertFalse(geturl.is_available())

    # def test_03__select_implementation(self):
    #     """Test03 GetURLexeCurl()._select_implementation()."""

    # @patch('udocker.utils.curl.Msg')
    # def test_04__set_defaults(self, mock_msg):
    #     """Test04 GetURLexeCurl()._set_defaults()"""
    #     mock_msg.return_value.level = 0
    #     mock_msg.VER = 4
    #     geturl = GetURLexeCurl()
    #     geturl._set_defaults()
    #     self.assertEqual(geturl._opts["insecure"], "")

    #     mock_msg.return_value.level = 0
    #     mock_msg.VER = 4
    #     geturl = GetURLexeCurl()
    #     geturl.insecure = True
    #     geturl._set_defaults()
    #     self.assertEqual(geturl._opts["insecure"], "-k")

    #     mock_msg.return_value.level = 5
    #     mock_msg.VER = 4
    #     geturl = GetURLexeCurl()
    #     geturl._set_defaults()
    #     self.assertEqual(geturl._opts["verbose"], "-v")
    #     self.assertEqual(geturl._files["url"], "")

    # def test_05__mkcurlcmd(self):
    #     """Test05 GetURLexeCurl()._mkcurlcmd()."""

    def test_06_get(self):
        """Test06 GetURLexeCurl().get()."""
        geturl = GetURLexeCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")


if __name__ == '__main__':
    main()
