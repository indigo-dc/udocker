#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURLpyCurl
"""
from io import BytesIO as strio
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


def test_04__set_defaults(geturl, mocker):
    """Test04 GetURLpyCurl()._set_defaults()."""
    mock_pyc = mocker.patch('udocker.utils.curl.pycurl.Curl')
    mock_hdr = mocker.patch('udocker.utils.curl.CurlHeader')
    geturl._set_defaults(mock_pyc, mock_hdr)
    assert geturl._url == ''
    assert mock_pyc.setopt.call_count == 9


def test_05__mkpycurl(geturl, mocker):
    """Test05 GetURLpyCurl()._mkpycurl()."""
    argl = 'http://host'
    kargl = {"follow": True, "post": "pst1", "sizeonly": True,
             "proxy": "http://proxy", "ctimeout": 1000,
             "header": "Authorization: Bearer", "v": True,
             "nobody": True, "timeout": 50, }
    buff = strio()
    mock_pyc = mocker.patch('udocker.utils.curl.pycurl.Curl')
    mock_hdr = mocker.patch('udocker.utils.curl.CurlHeader')
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    resout = geturl._mkpycurl(mock_pyc, mock_hdr, buff, 'http://host',
                              follow=True, post='pst1', sizeonly=True, proxy="http://proxy",
                              ctimeout=1000, header="Authorization: Bearer", v=True, nobody=True,
                              timeout=50, ofile='somefile', resume=True)
    assert resout == ('somefile', mock_file.return_value)
    assert mock_hdr.sizeonly
    mock_pyc.setopt.assert_called()


# def test_06_get(geturl, mocker):
#     """Test06 GetURLpyCurl().get() generic get."""
#     geturl._geturl = type('test', (object,), {})()
#     resout = geturl.get("http://host")


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
