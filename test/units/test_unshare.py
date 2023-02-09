#!/usr/bin/env python
"""
udocker unit tests: Unshare
"""
from unittest.mock import MagicMock
from udocker.helper.unshare import Unshare


def test_01_unshare(mocker):
    """Test01 Unshare().unshare"""
    mock_cdll = mocker.patch('ctypes.CDLL')
    status = Unshare().unshare(False)
    mock_cdll.return_value.unshare.assert_called()
    assert status


def test_02_unshare(mocker):
    """Test02 Unshare().unshare"""
    mock_cdll = mocker.patch('ctypes.CDLL')
    mock_cdll.return_value.unshare.return_value = -1
    status = Unshare().unshare(False)
    mock_cdll.return_value.unshare.assert_called()
    assert not status


def test_03_unshare(mocker):
    """Test03 Unshare().unshare"""
    mock_cdll = mocker.patch('ctypes.CDLL', side_effect=OSError)
    mock_logerr = mocker.patch('udocker.LOG.error')
    status = Unshare().unshare(False)
    mock_cdll.assert_called()
    mock_logerr.assert_called()
    assert not status


def test_04_namespace_exec(mocker):
    """Test04 Unshare().namespace_exec cpid = 0"""
    mock_method = MagicMock(name='method')
    mock_pipe = mocker.patch('os.pipe', side_effect=[('pread1', 'pwrite1'),('pread1', 'pwrite1')])
    mock_fork = mocker.patch('os.fork', return_value=0)
    mock_unshare = mocker.patch.object(Unshare, 'unshare', return_value=True)
    mock_close = mocker.patch('os.close', side_effect=[None, None])
    mock_read = mocker.patch('os.read')
    mock_setgid = mocker.patch('os.setgid')
    moc_setuid = mocker.patch('os.setuid')
    mock_setgrp = mocker.patch('os.setgroups')
    mock_sysexit = mocker.patch('sys.exit', return_value=1)

    status = Unshare().namespace_exec(mock_method)
    assert status is None
    assert mock_pipe.call_count == 2
    mock_fork.assert_called()
    mock_unshare.assert_called()
    assert mock_close.call_count == 2
    mock_read.assert_called()
    mock_setgid.assert_called()
    moc_setuid.assert_called()
    mock_setgrp.assert_called()
    mock_sysexit.assert_called()


def test_05_namespace_exec(mocker):
    """Test05 Unshare().namespace_exec cpid = 0, Raises"""
    mock_method = MagicMock(name='method')
    mock_pipe = mocker.patch('os.pipe', side_effect=[('pread1', 'pwrite1'), ('pread1', 'pwrite1')])
    mock_fork = mocker.patch('os.fork', return_value=0)
    mock_unshare = mocker.patch.object(Unshare, 'unshare', return_value=True)
    mock_close = mocker.patch('os.close', side_effect=[None, None])
    mock_read = mocker.patch('os.read')
    mock_setgid = mocker.patch('os.setgid', side_effect=OSError)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_sysexit = mocker.patch('sys.exit', return_value=1)

    status = Unshare().namespace_exec(mock_method)
    assert not status
    assert mock_pipe.call_count == 2
    mock_fork.assert_called()
    mock_unshare.assert_called()
    assert mock_close.call_count == 2
    mock_read.assert_called()
    mock_setgid.assert_called()
    mock_logerr.assert_called()
    mock_sysexit.assert_not_called()


def test_06_namespace_exec(mocker):
    """Test06 Unshare().namespace_exec cpid = 1 status 0"""
    mock_method = MagicMock(name='method')
    mock_pipe = mocker.patch('os.pipe', side_effect=[('pread1', 'pwrite1'), ('pread1', 'pwrite1')])
    mock_fork = mocker.patch('os.fork', return_value=1)
    mock_close = mocker.patch('os.close', side_effect=[None, None])
    mock_read = mocker.patch('os.read')
    mock_hinfo = mocker.patch('udocker.helper.unshare.HostInfo')
    mock_hinfo.return_value.username.return_value = 'user'
    mock_hinfo.uid = 1000
    mock_nixauth = mocker.patch('udocker.helper.unshare.NixAuthentication')
    mock_nixauth.return_value.user_in_subuid.return_value = [(1000, 1000)]
    mock_nixauth.return_value.user_in_subgid.return_value = [(1000, 1000)]
    mock_subcall = mocker.patch('subprocess.call', side_effect=[None, None])
    mock_wait = mocker.patch('os.waitpid', return_value=(123, 0))

    status = Unshare().namespace_exec(mock_method)
    assert status
    assert mock_pipe.call_count == 2
    mock_fork.assert_called()
    assert mock_close.call_count == 2
    mock_read.assert_called()
    mock_hinfo.return_value.username.assert_called()
    mock_nixauth.return_value.user_in_subuid.assert_called()
    mock_nixauth.return_value.user_in_subgid.assert_called()
    assert mock_subcall.call_count == 2
    mock_wait.assert_called()


def test_07_namespace_exec(mocker):
    """Test07 Unshare().namespace_exec cpid = 1 status 1"""
    mock_method = MagicMock(name='method')
    mock_pipe = mocker.patch('os.pipe', side_effect=[('pread1', 'pwrite1'), ('pread1', 'pwrite1')])
    mock_fork = mocker.patch('os.fork', return_value=1)
    mock_close = mocker.patch('os.close', side_effect=[None, None])
    mock_read = mocker.patch('os.read')
    mock_hinfo = mocker.patch('udocker.helper.unshare.HostInfo')
    mock_hinfo.return_value.username.return_value = 'user'
    mock_hinfo.uid = 1000
    mock_nixauth = mocker.patch('udocker.helper.unshare.NixAuthentication')
    mock_nixauth.return_value.user_in_subuid.return_value = [(1000, 1000)]
    mock_nixauth.return_value.user_in_subgid.return_value = [(1000, 1000)]
    mock_subcall = mocker.patch('subprocess.call', side_effect=[None, None])
    mock_wait = mocker.patch('os.waitpid', return_value=(123, 1))
    mock_logerr = mocker.patch('udocker.LOG.error')

    status = Unshare().namespace_exec(mock_method)
    assert not status
    assert mock_pipe.call_count == 2
    mock_fork.assert_called()
    assert mock_close.call_count == 2
    mock_read.assert_called()
    mock_hinfo.return_value.username.assert_called()
    mock_nixauth.return_value.user_in_subuid.assert_called()
    mock_nixauth.return_value.user_in_subgid.assert_called()
    assert mock_subcall.call_count == 2
    mock_wait.assert_called()
    mock_logerr.assert_called()
