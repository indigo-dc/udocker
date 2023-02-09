#!/usr/bin/env python
"""
udocker unit tests: Uvolume
"""
from udocker.utils.uvolume import Uvolume


def test_01_cleanpath():
    """Test01 Uvolume().cleanpath() no duplicate /."""
    path = '/bin/ls'
    volm = '/data'
    uvol = Uvolume(volm)
    result = uvol.cleanpath(path)
    assert result == path


def test_02_cleanpath():
    """Test02 Uvolume().cleanpath() with duplicate /."""
    path = '//bin//ls'
    path_clean = '/bin/ls'
    volm = '/data'
    uvol = Uvolume(volm)
    result = uvol.cleanpath(path)
    assert result == path_clean


def test_03_split():
    """Test03 Uvolume().split()."""
    volm = '/data:/contdata'
    uvol = Uvolume(volm)
    result = uvol.split()
    assert result == ('/data', '/contdata')


def test_04_split():
    """Test04 Uvolume().split()."""
    volm = '/data'
    uvol = Uvolume(volm)
    result = uvol.split()
    assert result == ('/data', '/data')
