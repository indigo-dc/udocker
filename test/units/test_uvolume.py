#!/usr/bin/env python
"""
udocker unit tests: Uvolume
"""
import pytest

from udocker.utils.uvolume import Uvolume


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.utils.uvolume.LOG')


data_cleanp = [('/bin/ls', '/bin/ls', '/data'),
               ('//bin//ls', '/bin/ls', '/data')]


@pytest.mark.parametrize("path,path_clean,volm", data_cleanp)
def test_01_cleanpath(mocker, path, path_clean, volm, logger):
    """Test01 Uvolume().cleanpath()."""
    result = Uvolume(volm).cleanpath(path)
    assert result == path_clean
    logger.debug.assert_called_with("removing dupl and trail slashes: %s", mocker.ANY)


data_split = [('/data:/contdata', ('/data', '/contdata')),
              ('/data', ('/data', '/data')),
              ('/data:', ('/data', '/data'))]


@pytest.mark.parametrize("volm,expected", data_split)
def test_02_split(mocker, volm, expected, logger):
    """Test02 Uvolume().split()."""
    result = Uvolume(volm).split()
    assert result == expected
    expected_calls = [
        mocker.call.debug("Spliting volume string"),
        mocker.call.debug("removing dupl and trail slashes: %s", mocker.ANY)
    ]
    logger.assert_has_calls(expected_calls, any_order=True)
