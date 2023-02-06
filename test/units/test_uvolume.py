#!/usr/bin/env python
"""
udocker unit tests: Uvolume
"""
import pytest
from udocker.utils.uvolume import Uvolume, LOG


def test_01_cleanpath_01():
    """Test01_01 Uvolume().cleanpath() no duplicate /."""
    path = '/bin/ls'
    volm = '/data'
    uvol = Uvolume(volm)
    result = uvol.cleanpath(path)
    assert result == path

def test_01_cleanpath_02():
    """Test01_01 Uvolume().cleanpath() with duplicate /."""
    path = '//bin//ls'
    path_clean = '/bin/ls'
    volm = '/data'
    uvol = Uvolume(volm)
    result = uvol.cleanpath(path)
    assert result == path_clean

def test_03_split_01():
    """Test03_01 Uvolume().split()."""
    volm = '/data:/contdata'
    uvol = Uvolume(volm)
    result = uvol.split()
    assert result == ('/data', '/contdata')

def test_03_split_02():
    """Test03_02 Uvolume().split()."""
    volm = '/data'
    uvol = Uvolume(volm)
    result = uvol.split()
    assert result == ('/data', '/data')
