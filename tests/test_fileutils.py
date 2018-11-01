#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `udocker` package."""

import pytest
from udocker.utils.fileutils import *
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


###############################
# Tests of fileutils.ChkSUM
def test__hashlib_sha256():
    """Test ChkSUM()._hashlib_sha256()."""
    sha256sum = (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    cksum = ChkSUM()
    file_data = StringIO("qwerty")


    with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
        mopen.return_value.__iter__ = (
            lambda self: iter(file_data.readline, ''))
        status = cksum._hashlib_sha256("filename")
        self.assertEqual(status, sha256sum)

def test_sha256(self):
    """Test ChkSUM().sha256()."""
    self._init()
    mock_call = mock.MagicMock()
    cksum = udocker.ChkSUM()
    #
    mock_call.return_value = True
    cksum._sha256_call = mock_call
    status = cksum.sha256("filename")
    self.assertTrue(status)
    #
    mock_call.return_value = False
    cksum._sha256_call = mock_call
    status = cksum.sha256("filename")
    self.assertFalse(status)

