#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURLpyCurl
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from io import BytesIO as strio
from udocker.utils.curl import GetURLpyCurl
from udocker.config import Config

BUILTINS = "builtins"


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

    def test_01_init(self):
        """Test01 GetURLpyCurl() constructor."""
        geturl = GetURLpyCurl()
        self.assertEqual(geturl._url, None)

    @patch('udocker.utils.curl.pycurl.Curl')
    def test_02_is_available(self, mock_pycurl):
        """Test02 GetURLpyCurl().is_available()."""
        mock_pycurl.return_value = True
        geturl = GetURLpyCurl()
        geturl.is_available()
        self.assertTrue(geturl.is_available())
        self.assertTrue(mock_pycurl.called)

        # mock_pycurl.side_effect = (NameError, AttributeError)
        # geturl = GetURLpyCurl()
        # with self.assertRaises(NameError, AttributeError):
        #     status = geturl.is_available()
        #     self.assertTrue(mock_pycurl.called)
        #     self.assertFalse(geturl.is_available())

        # mock_pycurl.return_value = None
        # geturl = GetURLpyCurl()
        # self.assertFalse(geturl.is_available())

    # def test_03__select_implementation(self):
    #     """Test03 GetURLpyCurl()._select_implementation()."""

    @patch.object(GetURLpyCurl, 'is_available')
    @patch('udocker.utils.curl.Msg')
    @patch('udocker.utils.curl.pycurl.Curl')
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

    @patch('udocker.utils.curl.json.dumps')
    def test_05__mkpycurl(self, mock_jdump):
        """Test05 GetURLpyCurl()._mkpycurl()."""
        curl_patch = patch("udocker.utils.curl.CurlHeader")
        curlhdr = curl_patch.start()
        mock_curlhdr = Mock()
        curlhdr.return_value = mock_curlhdr

        pyc_patch = patch("udocker.utils.curl.pycurl.Curl")
        pycurl = pyc_patch.start()
        mock_pycurl = Mock()
        pycurl.return_value = mock_pycurl

        buff = strio()
        argl = ["http://host"]

        geturl = GetURLpyCurl()
        status = geturl._mkpycurl(pycurl, curlhdr, buff, argl)
        self.assertTrue(pycurl.setopt.called)
        self.assertEqual(status, ("", None))

        kargl = {"post":  "pst1", "sizeonly": True,
                 "proxy": "http://proxy", "ctimeout": 1000,
                 "header": "Authorization: Bearer", "v": True,
                 "nobody": True, "timeout": 50, }
        mock_jdump.return_value = {"post": "pst1"}
        geturl = GetURLpyCurl()
        status = geturl._mkpycurl(pycurl, curlhdr, buff, argl, kargl)
        self.assertTrue(pycurl.setopt.called)
        self.assertTrue(curlhdr.sizeonly)
        self.assertEqual(status, ("", None))

        curlhdr = curl_patch.stop()
        pycurl = pyc_patch.stop()

    @patch.object(GetURLpyCurl, 'is_available')
    def test_06_get(self, mock_sel):
        """Test06 GetURLpyCurl().get() generic get."""
        mock_sel.return_value = True
        geturl = GetURLpyCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        status = geturl.get("http://host")
        self.assertEqual(status, "http://host")


if __name__ == '__main__':
    main()
