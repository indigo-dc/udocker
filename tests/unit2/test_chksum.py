#!/usr/bin/env python
"""
udocker unit tests: ChkSUM
"""

import pytest
from udocker.utils.chksum import ChkSUM


def test_01_hash256(mocker):
    """Test01 ChkSUM().hash sha256."""
    mocked_file_data = mocker.mock_open(read_data=b'qwertyui\n')
    mocker.patch("builtins.open", mocked_file_data)
    sha256sum = ("42e6d97f00bff046ae2dea5c6db56d866ae749fb7dc05319e08e5fbee31d851c")
    cksum = ChkSUM()
    ret_function = cksum.hash(mocked_file_data, "sha256")
    assert ret_function == sha256sum

def test_02_hash512(mocker):
    """Test01 ChkSUM().hash sha512."""
    mocked_file_data = mocker.mock_open(read_data=b'qwertyui\n')
    mocker.patch("builtins.open", mocked_file_data)
    sha512sum =("2a260f37d0e522ecb43d93f23bfbbe88846da321f9eb1a9b552b74"
                "d1fe356ef20506b06f1ab639e0e0b028e85404e0f6eee3deba3f7a2367de54af8a079ba823")
    cksum = ChkSUM()
    ret_function = cksum.hash(mocked_file_data, "sha512")
    assert ret_function == sha512sum
