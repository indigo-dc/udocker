#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURLpyCurl
"""
import pytest
from udocker.utils.curl import GetURLpyCurl


def _get(self, *args, **kwargs):
    """Mock for pycurl.get."""
    return args[0]


@pytest.fixture
def geturl():
    return GetURLpyCurl()


def test_01_is_available(geturl, mocker):
    """Test01 GetURLpyCurl().is_available()."""
    mock_pycurl = mocker.patch('udocker.utils.curl.pycurl.Curl', return_value=True)
    assert geturl.is_available()
    mock_pycurl.assert_called()


def test_02_is_available(geturl, mocker):
    """Test02 GetURLpyCurl().is_available()."""
    mock_pycurl = mocker.patch('udocker.utils.curl.pycurl.Curl', side_effect=NameError)
    assert not geturl.is_available()


def test_03__select_implementation(geturl):
    """Test03 GetURLpyCurl()._select_implementation()."""
    assert geturl._select_implementation() is None


# @patch.object(GetURLpyCurl, 'is_available')
# @patch('udocker.utils.curl.pycurl.Curl')
# @patch('udocker.utils.curl.CurlHeader')
# def test_04__set_defaults(self, mock_hdr, mock_pyc, mock_selinsec):
#     """Test04 GetURLpyCurl()._set_defaults()."""
#     mock_selinsec.return_value = True
#     geturl = GetURLpyCurl()
#     geturl._set_defaults(mock_pyc, mock_hdr)
#     self.assertTrue(mock_pyc.setopt.called)

#     # when insecure
#     geturl = GetURLpyCurl()
#     geturl._set_defaults(mock_pyc, mock_hdr)
#     self.assertEqual(mock_pyc.setopt.call_count, 18)

#     mock_selinsec.return_value = True
#     # when secure
#     geturl = GetURLpyCurl()
#     geturl._set_defaults(mock_pyc, mock_hdr)
#     self.assertEqual(mock_pyc.setopt.call_count, 27)

# @patch('udocker.utils.curl.json.dumps')
# def test_05__mkpycurl(self, mock_jdump):
#     """Test05 GetURLpyCurl()._mkpycurl()."""
#     curl_patch = patch("udocker.utils.curl.CurlHeader")
#     curlhdr = curl_patch.start()
#     mock_curlhdr = Mock()
#     curlhdr.return_value = mock_curlhdr

#     pyc_patch = patch("udocker.utils.curl.pycurl.Curl")
#     pycurl = pyc_patch.start()
#     mock_pycurl = Mock()
#     pycurl.return_value = mock_pycurl

#     buff = strio()
#     argl = ["http://host"]

#     geturl = GetURLpyCurl()
#     status = geturl._mkpycurl(pycurl, curlhdr, buff, argl)
#     self.assertTrue(pycurl.setopt.called)
#     self.assertEqual(status, ("", None))

#     kargl = {"post":  "pst1", "sizeonly": True,
#                 "proxy": "http://proxy", "ctimeout": 1000,
#                 "header": "Authorization: Bearer", "v": True,
#                 "nobody": True, "timeout": 50, }
#     mock_jdump.return_value = {"post": "pst1"}
#     geturl = GetURLpyCurl()
#     status = geturl._mkpycurl(pycurl, curlhdr, buff, argl, kargl)
#     self.assertTrue(pycurl.setopt.called)
#     self.assertTrue(curlhdr.sizeonly)
#     self.assertEqual(status, ("", None))

#     curlhdr = curl_patch.stop()
#     pycurl = pyc_patch.stop()

# ## Needs works
# @patch.object(GetURLpyCurl, 'is_available')
# def test_06_get(self, mock_sel):
#     """Test06 GetURLpyCurl().get() generic get."""
#     mock_sel.return_value = True
#     geturl = GetURLpyCurl()
#     geturl._geturl = type('test', (object,), {})()
#     geturl.get = self._get
#     status = geturl.get("http://host")
#     self.assertEqual(status, "http://host")
