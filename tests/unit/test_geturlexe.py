#!/usr/bin/env python2
"""
udocker unit tests: GetURLexeCurl
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.utils.curl import GetURLexeCurl
from udocker.config import Config


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

    @patch('udocker.msg.Msg')
    @patch('udocker.utils.curl.GetURL')
    def test_01_init(self, mock_gcurl, mock_msg):
        """Test GetURLexeCurl() constructor."""
        self.assertIsNone(GetURLexeCurl(self.conf)._opts)
        self.assertIsNone(GetURLexeCurl(self.conf)._files)

    @patch('udocker.msg.Msg.level')
    @patch('udocker.utils.fileutil.FileUtil.find_exec')
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

    @patch('udocker.msg.Msg.level')
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
