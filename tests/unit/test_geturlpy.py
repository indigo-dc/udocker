#!/usr/bin/env python2
"""
udocker unit tests: GetURLpyCurl
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.utils.curl import GetURLpyCurl
from udocker.config import Config


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

    @patch('udocker.msg.Msg.level')
    @patch('udocker.utils.curl.GetURLpyCurl.is_available')
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

    @patch('udocker.utils.curl.GetURLpyCurl._select_implementation')
    @patch('udocker.msg.Msg.level')
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

    @patch('udocker.utils.curl.GetURLpyCurl._select_implementation')
    @patch('udocker.msg.Msg')
    @patch('udocker.utils.curl.pycurl')
    @patch('udocker.utils.curl.CurlHeader')
    def test_04__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
        """Test GetURL()._mkpycurl()."""
        mock_sel.return_value = True
        self.geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

    @patch('udocker.utils.curl.GetURLpyCurl._select_implementation')
    def test_05_get(self, mock_sel):
        """Test GetURLpyCurl().get() generic get."""
        self.geturl._geturl = type('test', (object,), {})()
        self.geturl.get = self._get
        status = self.geturl.get("http://host")
        self.assertEqual(status, "http://host")


if __name__ == '__main__':
    main()
