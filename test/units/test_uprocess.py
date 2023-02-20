#!/usr/bin/env python
"""
udocker unit tests: Uprocess
"""
import logging
import subprocess
from udocker.utils.uprocess import Uprocess
from udocker.config import Config


def test_01_get_stderr(mocker):
    """Test01 Uprocess().get_stderr() info level."""
    mock_subproc = mocker.patch('udocker.utils.uprocess.subprocess')
    mock_subproc.DEVNULL = -3
    Config().getconf()
    Config.conf['verbose_level'] = logging.INFO
    status = Uprocess().get_stderr()
    assert status == -3


# def test_02_get_stderr(mocker):
#     """Test01 Uprocess().get_stderr() debug level."""
#     mock_subproc = mocker.patch('udocker.utils.uprocess.subprocess')
#     mock_sysstderr = mocker.patch('sys.stderr', return_value=1)
#     mock_subproc.DEVNULL = -3
#     Config().getconf()
#     Config.conf['verbose_level'] = logging.DEBUG
#     status = Uprocess().get_stderr()
#     assert status == 1
#     mock_sysstderr.assert_called()


def test_03_find_inpath(mocker):
    """Test03 Uprocess().find_inpath() empty fname and path."""
    fname = ''
    path = ''
    mock_base = mocker.patch('os.path.basename')
    mock_debug = mocker.patch('udocker.LOG.debug')
    status = Uprocess().find_inpath(fname, path)
    assert status == ''
    mock_base.assert_not_called()
    mock_debug.assert_not_called()


def test_04_find_inpath(mocker):
    """Test04 Uprocess().find_inpath() fname and path not empty."""
    fname = 'ls'
    path = 'PATH=/usr/bin'
    full_path = '/usr/bin/ls'
    mock_base = mocker.patch('os.path.basename', return_value=fname)
    mock_debug = mocker.patch('udocker.LOG.debug')
    mock_lexists = mocker.patch('os.path.lexists', return_value=True)
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
    mock_base = mocker.patch('os.path.basename', return_value=fname)
    mock_debug = mocker.patch('udocker.LOG.debug')
    mock_lexists = mocker.patch('os.path.lexists', side_effect=[False, True])
    status = Uprocess().find_inpath(fname, path)
    assert status == full_path
    mock_base.assert_called()
    mock_debug.assert_called()
    mock_lexists.assert_called()


def test_06_check_output(mocker):
    """Test06 Uprocess().check_output() raise OSError."""
    mock_subp_chkout = mocker.patch('subprocess.check_output', side_effect=OSError("fail"))
    status = Uprocess().check_output()
    assert status == ""
    mock_subp_chkout.assert_called()


def test_07_check_output(mocker):
    """Test06 Uprocess().check_output()."""
    chkout = b"some_check"
    mock_subp_chkout = mocker.patch('subprocess.check_output', return_value=chkout)
    status = Uprocess().check_output()
    assert status == "some_check"
    mock_subp_chkout.assert_called()


def test_08_get_output(mocker):
    """Test08 Uprocess().get_output()."""
    mock_getenv = mocker.patch('os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', return_value='/usr/bin/ls')
    mock_chkout = mocker.patch.object(Uprocess, 'check_output', return_value='OUTPUT')

    status = Uprocess().get_output(['ls', '-a'])
    assert status == "OUTPUT"
    mock_getenv.assert_called()
    mock_findinpath.assert_called()
    mock_chkout.assert_called()


def test_09_get_output(mocker):
    """Test09 Uprocess().get_output() raise error."""
    mock_getenv = mocker.patch('os.getenv', return_value='/usr/bin')
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
    mock_getenv = mocker.patch('os.getenv', return_value='/usr/bin')
    mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath', return_value='/usr/bin/ls')
    mock_subcall = mocker.patch('subprocess.call', return_value='OUTPUT')

    status = Uprocess().call(['ls', '-a'])
    assert status == "OUTPUT"
    mock_getenv.assert_called()
    mock_findinpath.assert_called()
    mock_subcall.assert_called()


# def test_11_pipe(mocker):
#     """Test11 Uprocess().pipe()."""
#     mock_getenv = mocker.patch('os.getenv', return_value='/usr/bin')
#     mock_findinpath = mocker.patch.object(Uprocess, 'find_inpath',
#                                           side_effect=['/usr/bin/ls', '/usr/bin/grep'])
#     mock_subpopen = mocker.patch('subprocess.Popen', side_effect=[None, None])
#     mock_subret = mocker.patch('subprocess.Popen.returncode', side_effect=[True, True])

#     status = Uprocess().pipe(['ls', '-a'], ['grep', '-r'])
#     assert status
#     mock_getenv.assert_called()
#     assert mock_findinpath.call_count == 2
#     assert mock_subpopen.call_count == 2
#     assert mock_subret.call_count == 2
