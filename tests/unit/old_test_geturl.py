#!/usr/bin/env python
"""
udocker unit tests: GetURL
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.utils.curl import GetURL
from udocker.config import Config


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

    @patch('udocker.utils.curl.GetURLexeCurl._select_implementation')
    @patch('udocker.utils.curl.GetURLexeCurl.is_available')
    @patch('udocker.utils.curl.GetURLpyCurl.is_available')
    @patch('udocker.msg.Msg.level')
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

    @patch('udocker.msg.Msg')
    @patch('udocker.utils.curl.GetURLexeCurl.is_available')
    @patch('udocker.utils.curl.GetURLpyCurl.is_available')
    def test_02__select_implementation(self, mock_gupycurl, mock_guexecurl, mock_msg):
        """Test GetURL()._select_implementation()."""
        mock_msg.level = 0
        mock_gupycurl.return_value = True
        self.geturl._select_implementation()
        self.assertTrue(self.geturl.cache_support)
        #
        mock_gupycurl.return_value = False
        self.geturl = GetURL(self.conf)
        self.geturl._select_implementation()
        self.assertFalse(self.geturl.cache_support)
        #
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

    @patch('udocker.utils.curl.GetURLpyCurl.is_available')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test GetURL().set_insecure()."""
        mock_gupycurl.return_value = True
        self.geturl.set_insecure()
        self.assertEqual(self.geturl.insecure, True)
        #
        self.geturl.set_insecure(False)
        self.assertEqual(self.geturl.insecure, False)

    @patch('udocker.utils.curl.GetURLpyCurl.is_available')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test GetURL().set_proxy()."""
        mock_gupycurl.return_value = True
        self.geturl.set_proxy("http://host")
        self.assertEqual(self.geturl.http_proxy, "http://host")

    def test_06_get(self):
        """Test GetURL().get() generic get."""
        self.assertRaises(TypeError, self.geturl.get)
        #
        self.geturl._geturl = type('test', (object,), {})()
        self.geturl._geturl.get = self._get
        self.assertEqual(self.geturl.get("http://host"), "http://host")

    def test_07_post(self):
        """Test GetURL().post() generic post."""
        self.assertRaises(TypeError, self.geturl.post)
        self.assertRaises(TypeError, self.geturl.post, "http://host")
        #
        self.geturl._geturl = type('test', (object,), {})()
        self.geturl._geturl.get = self._get
        status = self.geturl.post("http://host", {"DATA": 1, })
        self.assertEqual(status, "http://host")


if __name__ == '__main__':
    main()
