#!/usr/bin/env python
"""
udocker unit tests: Uvolume
"""
import pytest
from udocker.utils.uvolume import Uvolume


data_cleanp = [('/bin/ls', '/bin/ls', '/data'),
               ('//bin//ls', '/bin/ls', '/data')]


@pytest.mark.parametrize("path,path_clean,volm", data_cleanp)
def test_01_cleanpath(path, path_clean, volm):
    """Test01 Uvolume().cleanpath()."""
    result = Uvolume(volm).cleanpath(path)
    assert result == path_clean


data_split = [('/data:/contdata', ('/data', '/contdata')),
              ('/data', ('/data', '/data')),
              ('/data:', ('/data', '/data'))]


@pytest.mark.parametrize("volm,expected", data_split)
def test_02_split(volm, expected):
    """Test02 Uvolume().split()."""
    result = Uvolume(volm).split()
    assert result == expected
