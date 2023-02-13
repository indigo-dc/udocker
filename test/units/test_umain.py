#!/usr/bin/env python
"""
udocker unit tests: UMain
"""
from unittest.mock import patch
from udocker.umain import UMain
from udocker.config import Config


def test_01__prepare_exec(mocker):
    """Test01 UMain()._prepare_exec() userid=0."""
    argv = ["udocker", "-h"]
    Config().getconf()
    mock_cmdp = mocker.patch('udocker.umain.CmdParser')
    mock_getuid = mocker.patch('os.geteuid', return_value=0)
    mock_logerr = mocker.patch('udocker.umain.LOG.error')
    with patch('sys.exit') as mock_exit:
        umain = UMain(argv)
        umain._prepare_exec()
        mock_exit.assert_called()
        mock_cmdp.assert_called()
        mock_getuid.assert_called()
        mock_logerr.assert_called()


# def test_02__prepare_exec(mocker):
#     """Test02 UMain()._prepare_exec() userid=2000."""
#     argv = ["udocker", "-h"]
#     Config().getconf()
#     mock_cmdp = mocker.patch('udocker.umain.CmdParser')
#     mock_getuid = mocker.patch('os.geteuid', return_value=2000)
#     with patch('sys.exit') as mock_exit:
#         umain = UMain(argv)
#         umain._prepare_exec()
#         mock_exit.assert_called()
#         mock_cmdp.assert_called()
#         mock_getuid.assert_called()


# def test_03_execute(mocker):
#     """Test03 UMain().execute() help."""
#     Config().getconf()
#     argv = ['udocker', '--allow-root', '-h']
#     mock_lrepo = mocker.patch('udocker.umain.LocalRepository')
#     mock_ucli = mocker.patch('udocker.umain.UdockerCLI')
#     mock_lrepo.return_value.is_repo.return_value = True
#     mock_ucli.return_value.do_help.return_value = 0

#     umain = UMain(argv)
#     status = umain.execute()
#     assert status == 0
#     mock_ucli.assert_called()
#     mock_lrepo.return_value.is_repo.assert_called()
#     mock_ucli.return_value.do_help.assert_called()


# def test_04_execute(mocker):
#     """Test04 UMain().execute() version."""
#     Config().getconf()
#     argv = ['udocker', '--allow-root', '--version']
#     mock_lrepo = mocker.patch('udocker.umain.LocalRepository')
#     mock_ucli = mocker.patch('udocker.umain.UdockerCLI')
#     mock_lrepo.return_value.is_repo.return_value = True
#     mock_ucli.return_value.do_version.return_value = 0

#     umain = UMain(argv)
#     status = umain.execute()
#     assert status == 0
#     mock_ucli.assert_called()
#     mock_lrepo.return_value.is_repo.assert_called()
#     mock_ucli.return_value.do_version.assert_called()


# def test_05_execute(mocker):
#     """Test05 UMain().execute() version with error."""
#     Config().getconf()
#     argv = ['udocker', '--allow-root', '--config=udocker.conf']
#     mock_lrepo = mocker.patch('udocker.umain.LocalRepository')
#     mock_ucli = mocker.patch('udocker.umain.UdockerCLI')
#     mock_lrepo.return_value.is_repo.return_value = True
#     mock_ucli.return_value.do_version.return_value = 0

#     umain = UMain(argv)
#     status = umain.execute()
#     assert status == 1
#     mock_ucli.assert_called()
#     mock_lrepo.return_value.is_repo.assert_called()
#     mock_ucli.return_value.do_version.assert_called()


# def test_06_execute(mocker):
#     """Test06 UMain().execute() version."""
#     Config().getconf()
#     argv = ['udocker', '--allow-root', 'install']
#     mock_lrepo = mocker.patch('udocker.umain.LocalRepository')
#     mock_ucli = mocker.patch('udocker.umain.UdockerCLI')
#     mock_lrepo.return_value.is_repo.return_value = True
#     mock_ucli.return_value.do_install.return_value = 0

#     umain = UMain(argv)
#     status = umain.execute()
#     assert status == 0
#     mock_ucli.assert_called()
#     mock_lrepo.return_value.is_repo.assert_called()
#     mock_ucli.return_value.do_install.assert_called()



    #     argv = ['udocker', '--allow-root', 'showconf']
    #     mock_local.return_value.is_repo.return_value = True
    #     mock_local.return_value.create_repo.return_value = None
    #     mock_ucli.return_value.do_showconf.return_value = 0
    #     umain = UMain(argv)
    #     status = umain.execute()
    #     self.assertTrue(mock_ucli.return_value.do_showconf.called)
    #     self.assertEqual(status, 0)

    #     argv = ['udocker', '--allow-root', 'rm']
    #     mock_local.return_value.is_repo.return_value = True
    #     mock_local.return_value.create_repo.return_value = None
    #     mock_ucli.return_value.do_rm.return_value = 0
    #     umain = UMain(argv)
    #     status = umain.execute()
    #     self.assertTrue(mock_ucli.return_value.do_rm.called)
    #     self.assertEqual(status, 0)

    #     argv = ['udocker', '--allow-root', 'faking']
    #     mock_local.return_value.is_repo.return_value = True
    #     mock_local.return_value.create_repo.return_value = None
    #     umain = UMain(argv)
    #     status = umain.execute()
    #     self.assertEqual(status, 1)
