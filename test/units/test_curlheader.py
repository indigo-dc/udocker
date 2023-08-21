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
    fakedata = 'XXXX'
    mock_write = mocker.patch.object(CurlHeader, 'write')
    mock_file = mocker.mock_open(read_data=str(fakedata))
    mocker.patch("builtins.open", mock_file)
    assert curl_header.setvalue_from_file('filename')
    mock_write.assert_called_with('XXXX')


def test_05_setvalue_from_file(curl_header, mocker):
    """Test05 CurlHeader().setvalue_from_file()."""
    mock_write = mocker.patch.object(CurlHeader, 'write')
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    assert not curl_header.setvalue_from_file('filename')


def test_06_getvalue(curl_header):
    """Test06 CurlHeader().getvalue()."""
    curl_header.data = "XXXX"
    resout = curl_header.getvalue()
    assert resout == curl_header.data
