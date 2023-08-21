#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: CurlHeader
"""
import pytest
from udocker.utils.curl import CurlHeader


@pytest.fixture
def curl_header():
    return CurlHeader()


def test_01_write(curl_header):
    """Test01 CurlHeader().write()."""
    buff = ['HTTP/1.1 200 OK', 'Content-Type: application/octet-stream', 'Content-Length: 32']
    for line in buff:
        curl_header.write(line)

    resout = curl_header.data['content-type']
    assert resout == 'application/octet-stream'


def test_02_write(curl_header):
    """Test02 CurlHeader().write()."""
    buff = ['HTTP/1.1 200 OK', 'Content-Type: application/octet-stream', 'Content-Length: 32']
    for line in buff:
        curl_header.write(line)

    resout = curl_header.data['X-ND-HTTPSTATUS']
    assert resout == 'HTTP/1.1 200 OK'


def test_03_write(curl_header):
    """Test03 CurlHeader().write()."""
    curl_header.sizeonly = True
    resout = curl_header.write('')
    assert resout == -1


def test_04_setvalue_from_file(curl_header, mocker):
    """Test04 CurlHeader().setvalue_from_file()."""
    fakedata = StringIO('XXXX')
    with patch('builtins.open') as mopen:
        mopen.return_value = fakedata
        curl_header = CurlHeader()
        self.assertTrue(curl_header.setvalue_from_file("filename"))
        self.assertTrue(mock_write.called_with('XXXX'))


# @patch.object(CurlHeader, 'write')
# def test_03_setvalue_from_file(self, mock_write):
#     """Test03 CurlHeader().setvalue_from_file()."""
#     fakedata = StringIO('XXXX')
#     with patch('builtins.open') as mopen:
#         mopen.return_value = fakedata
#         curl_header = CurlHeader()
#         self.assertTrue(curl_header.setvalue_from_file("filename"))
#         self.assertTrue(mock_write.called_with('XXXX'))


def test_05_getvalue(curl_header):
    """Test05 CurlHeader().getvalue()."""
    curl_header.data = "XXXX"
    resout = curl_header.getvalue()
    assert resout == curl_header.data
