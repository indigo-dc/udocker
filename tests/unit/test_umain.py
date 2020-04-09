#!/usr/bin/env python
"""
udocker unit tests: UMain
"""

from unittest import TestCase, main
from udocker.umain import UMain
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock


class UMainTestCase(TestCase):
    """Test UMain() class main udocker program."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test01 UMain(argv) constructor."""

    @patch('udocker.umain.UdockerCLI')
    @patch('udocker.umain.LocalRepository')
    @patch('udocker.umain.Config')
    @patch('udocker.umain.os.geteuid')
    @patch('udocker.umain.CmdParser')
    @patch('udocker.umain.Msg')
    def test_02__prepare_exec(self, mock_msg, mock_cmdp, mock_getuid,
                              mock_conf, mock_local, mock_ucli):
        """Test02 UMain()._prepare_exec()."""
        argv = ['udocker']
        mock_cmdp.return_value.parse.return_value = None
        mock_cmdp.return_value.get.return_value = False
        mock_getuid.return_value = False
        with patch('sys.exit') as mock_exit:
            um = UMain(argv)
            status = um._prepare_exec()
            self.assertTrue(mock_exit.called)
            self.assertTrue(mock_msg.return_value.err.called)

        argv = ['udocker']
        mock_cmdp.return_value.parse.return_value = None
        mock_getuid.return_value = True
        mock_local.return_value.is_repo.return_value = True
        mock_local.return_value.create_repo.return_value = None
        mock_ucli.return_value = None
        mock_cmdp.return_value.get.side_effect = [True, False, False,
                                                  False, False, False,
                                                  False, 'topdir']
        um = UMain(argv)
        status = um._prepare_exec()
        self.assertTrue(mock_msg.return_value.err.called)
        self.assertTrue(mock_getuid.called)
        self.assertTrue(mock_local.return_value.is_repo.called)
        self.assertTrue(mock_ucli.called)

    # @patch('udocker.umain.Msg')
    # @patch('udocker.umain.UdockerCLI')
    # @patch.object(UMain, '_prepare_exec')
    # def test_03_execute(self, mock_prep, mock_ucli, mock_msg):
    #     """Test03 UMain().execute()."""
    #     argv = ['udocker']
    #     mock_prep.return_value = None
    #     mock_ucli.return_value.do_help.return_value = 0
    #     um = UMain(argv)
    #     um.cli = mock_ucli
    #     status = um.execute()
    #     self.assertTrue(mock_prep.called)
    #     self.assertTrue(mock_ucli.do_help.called)
    #     # self.assertEqual(status, 0)

    #     argv = ['udocker', '--version']
    #     mock_prep.return_value = None
    #     mock_ucli.return_value.do_help.return_value = 0
    #     mock_ucli.return_value.do_version.return_value = 0
    #     um = UMain(argv)
    #     um.cli = mock_ucli
    #     status = um.execute()
    #     self.assertTrue(mock_ucli.do_version.called)


if __name__ == '__main__':
    main()
