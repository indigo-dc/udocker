#!/usr/bin/env python
"""
udocker unit tests: UMain
"""
import pytest
from unittest.mock import patch
from udocker.umain import UMain
from udocker.config import Config


@pytest.fixture
def config():
    return Config().getconf()


@pytest.fixture
def mock_lrepo(mocker):
    return mocker.patch('udocker.umain.LocalRepository')


@pytest.fixture
def mock_ucli(mocker):
    return mocker.patch('udocker.umain.UdockerCLI')


def test_01__prepare_exec(mocker, config):
    """Test01 UMain()._prepare_exec() userid=0."""
    argv = ["udocker", "-h"]
    mock_cmdp = mocker.patch('udocker.umain.CmdParser')
    mock_getuid = mocker.patch('os.geteuid', return_value=0)
    mock_logerr = mocker.patch('udocker.umain.LOG.error')
    with patch('sys.exit') as mock_exit:
        UMain(argv)._prepare_exec()
        mock_exit.assert_called()
        mock_cmdp.assert_called()
        mock_getuid.assert_called()
        mock_logerr.assert_called()


def test_02__prepare_exec(mocker, config):
    """Test02 UMain()._prepare_exec() userid=2000."""
    argv = ["udocker", "-h"]
    mock_cmdp = mocker.patch('udocker.umain.CmdParser')
    mock_getuid = mocker.patch('os.geteuid', return_value=2000)
    with patch('sys.exit') as mock_exit:
        UMain(argv)._prepare_exec()
        mock_exit.assert_called()
        mock_cmdp.assert_called()
        mock_getuid.assert_called()


def test_03_execute(config, mock_lrepo, mock_ucli):
    """Test03 UMain().execute() help."""
    argv = ['udocker', '--allow-root', '-h']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_ucli.return_value.do_help.return_value = 0

    status = UMain(argv).execute()
    assert status == 0
    mock_ucli.assert_called()
    mock_lrepo.return_value.is_repo.assert_called()
    mock_ucli.return_value.do_help.assert_called()


def test_04_execute(config, mock_lrepo, mock_ucli):
    """Test04 UMain().execute() version."""
    argv = ['udocker', '--allow-root', '--version']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_ucli.return_value.do_version.return_value = 0

    status = UMain(argv).execute()
    assert status == 0
    mock_ucli.return_value.do_version.assert_called()


def test_05_execute(mocker, config, mock_lrepo, mock_ucli):
    """Test05 UMain().execute() version with error."""
    argv = ['udocker', '--allow-root', 'install', '--help']
    mock_msginfo = mocker.patch('udocker.umain.MSG.info')
    mock_lrepo.return_value.is_repo.return_value = True

    status = UMain(argv).execute()
    assert status == 0
    mock_msginfo.assert_called()


def test_06_execute(config, mock_lrepo, mock_ucli):
    """Test06 UMain().execute() version."""
    argv = ['udocker', '--allow-root', 'version']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_ucli.return_value.do_version.return_value = 0

    status = UMain(argv).execute()
    assert status == 0
    mock_ucli.return_value.do_version.assert_called()


def test_07_execute(config, mock_lrepo, mock_ucli):
    """Test07 UMain().execute() showconf."""
    argv = ['udocker', '--allow-root', 'showconf']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_ucli.return_value.do_showconf.return_value = 0

    status = UMain(argv).execute()
    assert status == 0
    mock_ucli.return_value.do_showconf.assert_called()


def test_08_execute(config, mock_lrepo, mock_ucli):
    """Test08 UMain().execute() install."""
    argv = ['udocker', '--allow-root', 'install']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_ucli.return_value.do_install.return_value = 0

    status = UMain(argv).execute()
    assert status == 0
    mock_ucli.return_value.do_install.assert_called()


def test_09_execute(config, mock_lrepo, mock_ucli):
    """Test09 UMain().execute() rm."""
    argv = ['udocker', '--allow-root', 'rm']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_ucli.return_value.do_rm.return_value = 0

    status = UMain(argv).execute()
    assert status == 0
    mock_ucli.return_value.do_rm.assert_called()


def test_10_execute(config, mock_lrepo, mock_ucli):
    """Test10 UMain().execute() faking."""
    argv = ['udocker', '--allow-root', 'faking']
    mock_lrepo.return_value.is_repo.return_value = True
    mock_lrepo.return_value.create_repo.return_value = None

    status = UMain(argv).execute()
    assert status == 1
