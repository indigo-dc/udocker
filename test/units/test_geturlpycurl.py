#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURLpyCurl
"""
from io import BytesIO as strio

import pytest

from udocker.utils.curl import GetURLpyCurl
from udocker.utils.fileutil import FileUtil

try:
    import pycurl
except ImportError:
    pass


def _get(self, *args, **kwargs):
    """Mock for pycurl.get."""
    return args[0]


@pytest.fixture
def geturl():
    return GetURLpyCurl()


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.docker.LOG')


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


def test_06_get(mocker, geturl):
    geturl._geturl = type('test', (object,), {})()
    resout = geturl.get("http://host")


@pytest.mark.parametrize("url, kwargs, perform, status_code, expected_hdr_data, mycurl_error, expected_exception", [
    ("http://example.com", {}, None, 200, {'X-ND-CURLSTATUS': '', 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"timeout": 10, "header": ["User-Agent: custom"]}, None, 200,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"timeout": 10, "header": ["User-Agent: custom"]}, None, 200,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, True, True),
    ("http://example.com", {"ofile": "test", "timeout": 10, "header": ["User-Agent: custom"]}, None, 200,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"ofile": "test", "timeout": 10, "header": ["User-Agent: custom"]}, None, 401,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"ofile": "test", "timeout": 10, "header": ["User-Agent: custom"]}, None, 301,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"ofile": "test", "timeout": 10, "header": ["User-Agent: custom"]}, None, 206,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"ofile": "test", "resume": "", "timeout": 10, "header": ["User-Agent: custom"]}, None, 206,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {"ofile": "test", "timeout": 10, "header": ["User-Agent: custom"]}, None, 416,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    # ("http://example.com", {"ofile": "test", "resume": "", "timeout": 10, "header": ["User-Agent: custom"]}, None, 416,
    #  {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None), # FIXME: recursive
    ("http://example.com", {"ofile": "test", "timeout": 10, "header": ["User-Agent: custom"]}, None, 405,
     {'X-ND-CURLSTATUS': '', 'X-ND-HEADERS': ['User-Agent: custom'], 'X-ND-HTTPSTATUS': ''}, False, None),
    ("http://example.com", {}, (pycurl.error(0, 'error'),), 200, {'X-ND-CURLSTATUS': 0, 'X-ND-HTTPSTATUS': 'error'},
     False, pycurl.error),
])
def test_06_get(mocker, geturl, url, kwargs, perform, status_code, expected_hdr_data, mycurl_error, expected_exception):
    """Test06 GetURLpyCurl().get() generic get."""
    mocker.patch.object(geturl, '_set_defaults')

    if mycurl_error:
        mock_mkpycurl = mocker.patch.object(geturl, '_mkpycurl', side_effect=OSError)
    else:
        mock_mkpycurl = mocker.patch.object(geturl, '_mkpycurl')
        mock_pycurl_instance = mocker.Mock(spec=pycurl.Curl)
        mock_output_file = mocker.Mock()
        mock_filep = mocker.Mock()
        mock_mkpycurl.return_value = (mock_output_file, mock_filep)
        mock_pycurl_instance.perform.side_effect = perform
        mocker.patch('pycurl.Curl', return_value=mock_pycurl_instance)

    mocker.patch.object(geturl, 'get_status_code', return_value=status_code)
    mocker.patch.object(FileUtil, 'remove')

    result = geturl.get(url, **kwargs)

    if expected_exception and mycurl_error:
        assert result == (None, None)
    elif expected_exception:
        assert result[0].data == expected_hdr_data
    else:
        assert result[0].data == expected_hdr_data
        geturl._set_defaults.assert_called_once()
        mock_mkpycurl.assert_called_once()
