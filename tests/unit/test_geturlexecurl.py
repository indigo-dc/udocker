#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURLexeCurl
"""

from unittest import TestCase, main
from unittest.mock import patch
from udocker.utils.curl import GetURLexeCurl
from udocker.config import Config


class GetURLexeCurlTestCase(TestCase):
    """GetURLexeCurl TestCase."""

    def setUp(self):
        Config().getconf()
        Config().conf['timeout'] = 1
        Config().conf['ctimeout'] = 1
        Config().conf['download_timeout'] = 1
        Config().conf['http_agent'] = ""
        Config().conf['http_proxy'] = ""

    def tearDown(self):
        pass

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    def test_01_init(self):
        """Test01 GetURLexeCurl() constructor."""
        geturl = GetURLexeCurl()
        self.assertIsNone(geturl._opts)
        self.assertIsNone(geturl._files)

    @patch('udocker.utils.curl.FileUtil.find_exec')
    def test_02_is_available(self, mock_findexec):
        """Test02 GetURLexeCurl()._is_available()."""
        mock_findexec.return_value = "/tmp"
        geturl = GetURLexeCurl()
        self.assertTrue(geturl.is_available())

        mock_findexec.return_value = ""
        geturl = GetURLexeCurl()
        self.assertFalse(geturl.is_available())

    # def test_03__select_implementation(self):
    #     """Test03 GetURLexeCurl()._select_implementation()."""

    @patch('udocker.utils.curl.FileUtil.mktmp')
    def test_04__set_defaults(self, mock_mktemp):
        """Test04 GetURLexeCurl()._set_defaults()"""
        mock_mktemp.side_effect = ["/tmp/err", "/tmp/out", "/tmp/hdr"]
        geturl = GetURLexeCurl()
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], list())

        mock_mktemp.side_effect = ["/tmp/err", "/tmp/out", "/tmp/hdr"]
        geturl = GetURLexeCurl()
        geturl.insecure = True
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], ["-k"])

        mock_mktemp.side_effect = ["/tmp/err", "/tmp/out", "/tmp/hdr"]
        geturl = GetURLexeCurl()
        geturl._set_defaults()
        self.assertEqual(geturl._files["url"], "")
        self.assertEqual(geturl._files["error_file"], "/tmp/err")
        self.assertEqual(geturl._files["header_file"], "/tmp/hdr")

    @patch('udocker.utils.curl.FileUtil.remove')
    @patch('udocker.utils.curl.json.dumps')
    def test_05__mkcurlcmd(self, mock_jdump, mock_furm):
        """Test05 GetURLexeCurl()._mkcurlcmd()."""
        argl = ["http://host"]
        kargl = list()
        Config.conf['use_curl_executable'] = ""
        mock_jdump.return_value = {"post": "pst1"}
        mock_furm.return_value = None
        res = ["curl", "-D", "/tmp/hdr", "-o", "/tmp/out",
               "--stderr", "/tmp/err", "['http://host']"]
        geturl = GetURLexeCurl()
        geturl._opts = dict()
        geturl._files = {"url": "", "error_file": "/tmp/err",
                         "output_file": "/tmp/out",
                         "header_file": "/tmp/hdr"}
        status = geturl._mkcurlcmd(argl, kargl)
        self.assertFalse(mock_jdump.called)
        self.assertEqual(status, res)

        # argl = ["http://host"]
        # kargl = {"post":  "pst1", "ctimeout": 1000,
        #          "timeout": 50, "proxy": "http://proxy",
        #          "header": ["Authorization: Bearer"], "v": True,
        #          "nobody": True, "resume": True,}
        # Config.conf['use_curl_executable'] = ""
        # mock_jdump.return_value = {"post": "pst1"}
        # mock_furm.return_value = None
        # res = ["curl", "-X", "POST", "-H",
        #        "Content-Type: application/json",
        #        "-d", "pst1", "--connect-timeout", "1000",
        #        "-m", "50", "--proxy", "http://proxy",
        #        "-H", "Authorization: Bearer", "-v",
        #        "-D", "/tmp/hdr", "-o", "/tmp/out",
        #        "--stderr", "/tmp/err", "['http://host']"]
        # geturl = GetURLexeCurl()
        # geturl._opts = dict()
        # geturl._files = {"url": "", "error_file": "/tmp/err",
        #                  "output_file": "/tmp/out",
        #                  "header_file": "/tmp/hdr"}
        # status = geturl._mkcurlcmd(argl, kargl)
        # self.assertFalse(mock_jdump.called)
        # self.assertEqual(status, res)

    def test_06_get(self):
        """Test06 GetURLexeCurl().get()."""
        geturl = GetURLexeCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")


if __name__ == '__main__':
    main()
