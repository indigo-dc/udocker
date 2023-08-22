#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: GetURLexeCurl
"""
import pytest
from udocker.utils.curl import GetURLexeCurl


@pytest.fixture
def geturl():
    return GetURLexeCurl()


data_curl = (('/bin/curl', True),
             ('', False))


@pytest.mark.parametrize('exec,expected', data_curl)
def test_01_is_available(geturl, mocker, exec, expected):
    """Test01 GetURLpyCurl().is_available()."""
    mock_findexec = mocker.patch('udocker.utils.curl.FileUtil.find_exec', return_value=exec)
    assert geturl.is_available() == expected
    mock_findexec.assert_called()


def test_02__select_implementation(geturl):
    """Test02 GetURLexeCurl()._select_implementation()."""
    assert geturl._select_implementation() is None


def test_03__set_defaults(geturl, mocker):
    """Test03 GetURLexeCurl()._set_defaults()"""
    mock_mktemp = mocker.patch('udocker.utils.curl.FileUtil.mktmp',
                               side_effect=['/tmp/err', '/tmp/out', '/tmp/hdr'])
    geturl._set_defaults()
    assert geturl._opts['insecure'] == []


def test_04__set_defaults(geturl, mocker):
    """Test04 GetURLexeCurl()._set_defaults()"""
    mock_mktemp = mocker.patch('udocker.utils.curl.FileUtil.mktmp',
                               side_effect=['/tmp/err', '/tmp/out', '/tmp/hdr'])
    geturl.insecure = True
    geturl._set_defaults()
    assert geturl._opts['insecure'] == ['-k']
    assert geturl._files['url'] == ''
    assert geturl._files['error_file'] == '/tmp/err'
    assert geturl._files['header_file'] == '/tmp/hdr'


def test_05__mkcurlcmd(geturl, mocker):
    """Test05 GetURLexeCurl()._mkcurlcmd()."""
    mock_jdump = mocker.patch('udocker.utils.curl.json.dumps', return_value={"post": "pst1"})
    mock_furm = mocker.patch('udocker.utils.curl.FileUtil.remove')
    res = ["curl", "-D", "/tmp/hdr", "-o", "/tmp/out",
           "--stderr", "/tmp/err", "['http://host']"]
    geturl._opts = dict()
    geturl._files = {"url": "", "error_file": "/tmp/err", "output_file": "/tmp/out",
                     "header_file": "/tmp/hdr"}
    resout = geturl._mkcurlcmd(['http://host'])
    assert resout == res
    mock_jdump.assert_not_called()
    mock_furm.assert_not_called()


def test_06__mkcurlcmd(geturl, mocker):
    """Test06 GetURLexeCurl()._mkcurlcmd()."""
    hdrlist = ["Authorization: Bearer", "xxx"]
    res = ["curl", "-X", "POST", "-H", "Content-Type: application/json", "-d", {'post': 'pst1'},
           "--connect-timeout", "1000", "-m", "50", "--proxy", "http://proxy", '-H',
           'Authorization: Bearer', '-H', 'xxx', "-v", "--head", "-D", "/tmp/hdr", "-o",
           "/tmp/out", "--stderr", "/tmp/err", "['http://host']"]
    mock_jdump = mocker.patch('udocker.utils.curl.json.dumps', return_value={"post": "pst1"})
    mock_furm = mocker.patch('udocker.utils.curl.FileUtil.remove')
    geturl._opts = dict()
    geturl._files = {"url": "", "error_file": "/tmp/err", "output_file": "/tmp/out",
                     "header_file": "/tmp/hdr"}
    resout = geturl._mkcurlcmd(['http://host'], post="pst1", ctimeout=1000, timeout=50,
                               proxy="http://proxy", header=hdrlist,
                               v=True, nobody=True, resume=True)
    assert resout == res
    mock_jdump.assert_called()
    mock_furm.assert_not_called()


def test_07__mkcurlcmd(geturl, mocker):
    """Test07 GetURLexeCurl()._mkcurlcmd()."""
    hdrlist = ["Authorization: Bearer", "xxx"]
    res = ["curl", '-L', "-X", "POST", "-H", "Content-Type: application/json", "-d",
           {'post': 'pst1'}, "--connect-timeout", "1000", "-m", "1800", "--proxy",
           "http://proxy", '-H', 'Authorization: Bearer', '-H', 'xxx', "-v", "--head", "-C",
           '-', '-D', "/tmp/hdr", "-o", "outfile.tmp", "--stderr", "/tmp/err", "['http://host']"]
    mock_jdump = mocker.patch('udocker.utils.curl.json.dumps', return_value={"post": "pst1"})
    mock_furm = mocker.patch('udocker.utils.curl.FileUtil.remove')
    geturl._opts = dict()
    geturl._files = {"url": "", "error_file": "/tmp/err", "output_file": "/tmp/out",
                     "header_file": "/tmp/hdr"}
    resout = geturl._mkcurlcmd(['http://host'], follow=True, post="pst1", ctimeout=1000, timeout=50,
                               proxy="http://proxy", header=hdrlist,
                               v=True, nobody=True, resume=True, ofile='outfile')
    assert resout == res
    mock_jdump.assert_called()
    mock_furm.assert_called()


# ## Needs works
# def test_06_get(self):
#     """Test06 GetURLexeCurl().get()."""
#     geturl = GetURLexeCurl()
#     geturl._geturl = type('test', (object,), {})()
#     geturl.get = self._get
#     self.assertEqual(geturl.get("http://host"), "http://host")
