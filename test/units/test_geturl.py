#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURL
"""
import pytest
from udocker.utils.curl import GetURL


@pytest.fixture
def geturl():
    return GetURL()


def _get(self, *args, **kwargs):
    """Mock for pycurl.get."""
    return args[0]


def test_01__select_implementation(geturl, mocker):
    """Test01 GetURL()._select_implementation()."""
    mock_gupycurl = mocker.patch('udocker.utils.curl.GetURLpyCurl')
    mock_guexecurl = mocker.patch('udocker.utils.curl.GetURLexeCurl')
    mock_gupycurl.return_value.is_available.return_value = True
    geturl._select_implementation()
    assert geturl.cache_support
    mock_gupycurl.assert_called()
    mock_guexecurl.assert_not_called()


def test_02__select_implementation(geturl, mocker):
    """Test02 GetURL()._select_implementation()."""
    mock_gupycurl = mocker.patch('udocker.utils.curl.GetURLpyCurl')
    mock_guexecurl = mocker.patch('udocker.utils.curl.GetURLexeCurl')
    mock_gupycurl.return_value.is_available.return_value = False
    mock_guexecurl.return_value.is_available.return_value = True
    geturl._select_implementation()
    assert not geturl.cache_support
    mock_gupycurl.assert_called()
    mock_guexecurl.assert_called()


def test_03__select_implementation(geturl, mocker):
    """Test03 GetURL()._select_implementation()."""
    mock_gupycurl = mocker.patch('udocker.utils.curl.GetURLpyCurl')
    mock_guexecurl = mocker.patch('udocker.utils.curl.GetURLexeCurl')
    mock_gupycurl.return_value.is_available.return_value = False
    mock_guexecurl.return_value.is_available.return_value = False
    pytest.raises(NameError, geturl._select_implementation)
    mock_gupycurl.assert_called()
    mock_guexecurl.assert_called()


def test_04_get_content_length(geturl):
    """Test04 GetURL().get_content_length()."""
    hdr = type('test', (object,), {})()
    hdr.data = {"content-length": 10, }
    assert geturl.get_content_length(hdr) == 10


def test_05_get_content_length(geturl):
    """Test05 GetURL().get_content_length()."""
    hdr = type('test', (object,), {})()
    hdr.data = {"content-length": dict(), }
    assert geturl.get_content_length(hdr) == -1


def test_06_set_insecure(geturl):
    """Test06 GetURL().set_insecure()."""
    geturl.set_insecure()
    assert geturl.insecure


def test_07_set_insecure(geturl):
    """Test07 GetURL().set_insecure()."""
    geturl.set_insecure(False)
    assert not geturl.insecure


def test_08_set_proxy(geturl):
    """Test08 GetURL().set_insecure()."""
    geturl.set_proxy('http://host')
    assert geturl.http_proxy == 'http://host'


def test_09_get(geturl):
    """Test09 GetURL().get()."""
    pytest.raises(TypeError, geturl.get)


# def test_10_get(geturl):
#     """Test10 GetURL().get()."""
#     geturl._geturl = type('test', (object,), {})()
#     geturl._geturl.get = _get
#     assert geturl.get('http://host') == 'http://host'


# def test_06_get(self):
#     """Test06 GetURL().get()."""
#     geturl = GetURL()
#     self.assertRaises(TypeError, geturl.get)

#     geturl = GetURL()
#     geturl._geturl = type('test', (object,), {})()
#     geturl._geturl.get = self._get
#     self.assertEqual(geturl.get("http://host"), "http://host")


def test_11_post(geturl):
    """Test11 GetURL().post()."""
    pytest.raises(TypeError, geturl.post)


# def test_07_post(self):
#     """Test07 GetURL().post()."""
#     geturl = GetURL()
#     self.assertRaises(TypeError, geturl.post)
#     self.assertRaises(TypeError, geturl.post, "http://host")

#     geturl = GetURL()
#     geturl._geturl = type('test', (object,), {})()
#     geturl._geturl.get = self._get
#     status = geturl.post("http://host", {"DATA": 1, })
#     self.assertEqual(status, "http://host")


data_code = (('HTTP-Version 400 Reason-Phrase', 400),
             ('HTTP-Version Reason-Phrase', 400),
             ('', 404),)


@pytest.mark.parametrize('sline,expected', data_code)
def test_13_get_status_code(geturl, sline, expected):
    """Test13 GetURL().get_status_code()."""
    assert geturl.get_status_code(sline) == expected
