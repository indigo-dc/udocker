#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `udocker` package."""

import pytest
from udocker.utils.fileutil import ChkSUM


###############################
# Tests of fileutils.ChkSUM
def test_sha256(tmpdir):
    """Test ChkSUM()._hashlib_sha256()."""
    sha256sum = (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    fcks = tmpdir.mkdir("test").join("cksum")
    fcks.write("qwerty")
    cksum = ChkSUM()
    status = cksum.sha256(fcks)
    assert status == sha256sum
