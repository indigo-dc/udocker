#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURL
"""

from unittest import TestCase, main
from unittest.mock import patch
from udocker.utils.curl import GetURL
from udocker.utils.curl import GetURLpyCurl
from udocker.utils.curl import GetURLexeCurl
from udocker.config import Config


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
        Config.conf['use_curl_executable'] = ""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        geturl = GetURL()
        geturl._select_implementation()
        self.assertTrue(geturl.cache_support)
        self.assertTrue(mock_gupycurl.called)

        mock_gupycurl.return_value = False
        geturl = GetURL()
        geturl._select_implementation()
        self.assertFalse(geturl.cache_support)

        mock_gupycurl.return_value = False
        mock_guexecurl.return_value = False
        with self.assertRaises(NameError) as nameerr:
            geturl = GetURL()
            geturl._select_implementation()
            self.assertEqual(nameerr.exception.code, 1)

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

    def test_08_get_status_code(self):
        """Test08 GetURL().get_status_code()."""
        sline = "HTTP-Version 400 Reason-Phrase"
        geturl = GetURL()
        status = geturl.get_status_code(sline)
        self.assertEqual(status, 400)

        sline = "HTTP-Version Reason-Phrase"
        geturl = GetURL()
        status = geturl.get_status_code(sline)
        self.assertEqual(status, 400)

        sline = ""
        geturl = GetURL()
        status = geturl.get_status_code(sline)
        self.assertEqual(status, 404)


if __name__ == '__main__':
    main()
