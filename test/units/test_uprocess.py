#!/usr/bin/env python
"""
udocker unit tests: Uprocess
"""
import logging
import subprocess

import pytest

from udocker.config import Config
from udocker.utils.uprocess import Uprocess


def test_01_get_stderr(mocker):
    """Test01 Uprocess().get_stderr() info level."""
    mock_subproc = mocker.patch('udocker.utils.uprocess.subprocess')
    mock_config = mocker.patch('udocker.config.Config.getconf')
    mock_config.return_value = None
    mocker.patch('udocker.config.Config.conf', {'verbose_level': logging.INFO})

    mock_subproc.DEVNULL = -3
    Config().getconf()
    Config.conf['verbose_level'] = logging.INFO
    status = Uprocess().get_stderr()
    assert status == -3


def test_02_get_stderr(mocker):
    """Test01 Uprocess().get_stderr() debug level."""
    mocker.patch('udocker.utils.uprocess.subprocess')
    mocker.patch('udocker.config.Config.getconf').return_value = None
    mocker.patch('udocker.config.Config.conf', {'verbose_level': logging.DEBUG})

    mocker.patch('sys.stderr', 1)

    status = Uprocess().get_stderr()
    assert status == 1


def test_03_find_inpath(mocker):
    """Test03 Uprocess().find_inpath() empty fname and path."""
    fname = ''
    path = ''
    mock_base = mocker.patch('udocker.utils.uprocess.os.path.basename')
    mock_debug = mocker.patch('udocker.utils.uprocess.LOG.debug')
    status = Uprocess().find_inpath(fname, path)
    assert status == ''
    mock_base.assert_not_called()
    mock_debug.assert_not_called()


def test_04_find_inpath(mocker):
    """Test04 Uprocess().find_inpath() fname and path not empty."""
    fname = 'ls'
    path = 'PATH=/usr/bin'
    full_path = '/usr/bin/ls'
    mock_base = mocker.patch('udocker.utils.uprocess.os.path.basename', return_value=fname)
    mock_debug = mocker.patch('udocker.utils.uprocess.LOG.debug')
    mock_lexists = mocker.patch('udocker.utils.uprocess.os.path.lexists', return_value=True)
    status = Uprocess().find_inpath(fname, path)
    assert status == full_path
    mock_base.assert_called()
    mock_debug.assert_called()
    mock_lexists.assert_called()


def test_05_find_inpath(mocker):
    """Test05 Uprocess().find_inpath() fname and path is multiple."""
    fname = 'ls'
    path = 'PATH=/usr/bin:/bin'
    full_path = '/bin/ls'
    mock_base = mocker.patch('udocker.utils.uprocess.os.path.basename', return_value=fname)
    mock_debug = mocker.patch('udocker.utils.uprocess.LOG.debug')
    mock_lexists = mocker.patch('udocker.utils.uprocess.os.path.lexists', side_effect=[False, True])
    status = Uprocess().find_inpath(fname, path)
    assert status == full_path
    mock_base.assert_called()
    mock_debug.assert_called()
    mock_lexists.assert_called()


def test_06_check_output(mocker):
    """Test06 Uprocess().check_output() raise OSError."""
    mock_subp_chkout = mocker.patch('udocker.utils.uprocess.subprocess.check_output',
                                    side_effect=OSError("fail"))
    status = Uprocess().check_output()
    assert status == ""
    mock_subp_chkout.assert_called()


def test_07_check_output(mocker):
    """Test06 Uprocess().check_output()."""
    chkout = b"some_check"
    mock_subp_chkout = mocker.patch('udocker.utils.uprocess.subprocess.check_output',
                                    return_value=chkout)
    status = Uprocess().check_output()
    assert status == "some_check"
    mock_subp_chkout.assert_called()


def test_08_get_output(mocker):
    """Test08 Uprocess().get_output()."""
    mock_getenv = mocker.patch('udocker.utils.uprocess.os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', return_value='/usr/bin/ls')
    mock_chkout = mocker.patch.object(Uprocess, 'check_output', return_value='OUTPUT')
    status = Uprocess().get_output(['ls', '-a'])
    assert status == "OUTPUT"
    mock_getenv.assert_called()
    mock_findinpath.assert_called()
    mock_chkout.assert_called()


def test_09_get_output(mocker):
    """Test09 Uprocess().get_output() raise error."""
    mock_getenv = mocker.patch('udocker.utils.uprocess.os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', return_value='/usr/bin/ls')
    mock_chkout = mocker.patch.object(Uprocess, 'check_output',
                                      side_effect=subprocess.CalledProcessError(1, "CMD"))
    status = Uprocess().get_output(['ls', '-a'])
    assert status is None
    mock_getenv.assert_called()
    mock_findinpath.assert_called()
    mock_chkout.assert_called()


def test_10_call(mocker):
    """Test10 Uprocess().call()."""
    mock_getenv = mocker.patch('udocker.utils.uprocess.os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', return_value='/usr/bin/ls')
    mock_subcall = mocker.patch('udocker.utils.uprocess.subprocess.call', return_value='OUTPUT')
    status = Uprocess().call(['ls', '-a'])
    assert status == "OUTPUT"
    mock_getenv.assert_called()
    mock_findinpath.assert_called()
    mock_subcall.assert_called()


@pytest.mark.parametrize('error_proc1, error_proc2, count_findinpath, count_popen', [
    (False, False, 2, 2),
    (True, True, 2, 1),
    (True, False, 2, 1),
    (False, True, 2, 2),
])
def test_11_pipe(mocker, error_proc1, error_proc2, count_findinpath, count_popen):
    """Test11 Uprocess().pipe()."""
    mock_getenv = mocker.patch('udocker.utils.uprocess.os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', side_effect=['/usr/bin/ls', '/usr/bin/grep'])
    mock_popen = mocker.patch('udocker.utils.uprocess.subprocess.Popen')

    mock_proc1 = mocker.Mock()
    mock_proc2 = mocker.Mock()

    proc1_returncode_mock = mocker.PropertyMock(side_effect=[None, 0, 0, 0])
    proc2_returncode_mock = mocker.PropertyMock(side_effect=[None, 0, 0, 0])

    type(mock_proc1).returncode = proc1_returncode_mock
    type(mock_proc2).returncode = proc2_returncode_mock

    mock_popen.side_effect = [OSError if error_proc1 else mock_proc1, OSError if error_proc2 else mock_proc2]

    status = Uprocess().pipe(['ls', '-a'], ['grep', '-r'])

    mock_getenv.assert_called_once_with("PATH", "")
    assert mock_findinpath.call_count == count_findinpath
    assert mock_popen.call_count == count_popen

    if error_proc2 and not error_proc1:
        mock_proc1.kill.assert_called()
    if error_proc2 or error_proc1:
        assert status is False

    if not error_proc1 and not error_proc2:
        assert status is True
        mock_proc1.wait.assert_called()
        mock_proc2.wait.assert_called()
