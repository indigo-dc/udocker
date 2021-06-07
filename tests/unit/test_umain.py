#!/usr/bin/env python
"""
udocker unit tests: UMain
"""

from udocker.config import Config
from unittest import TestCase, main
from udocker.umain import UMain
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock


class UMainTestCase(TestCase):
    """Test UMain() class main udocker program."""

    def setUp(self):
        Config().getconf()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test01 UMain(argv) constructor."""
        argv = ["udocker", "-h"]
        udoc = UMain(argv)
        self.assertEqual(udoc.argv, argv)

    @patch('udocker.umain.UdockerCLI')
    @patch('udocker.umain.LocalRepository')
    @patch('udocker.umain.os.geteuid')
    def test_02__prepare_exec(self, mock_getuid,
                              mock_local, mock_ucli):
        """Test02 UMain()._prepare_exec()."""
        argv = ["udocker", "-h"]
        mock_getuid.return_value = 0
        with patch('sys.exit') as mock_exit:
            um = UMain(argv)
            status = um._prepare_exec()
            self.assertTrue(mock_exit.called)

        argv = ["udocker", "-h", "--debug", "--insecure"]
        mock_getuid.return_value = 100
        mock_local.return_value.is_repo.return_value = True
        mock_local.return_value.create_repo.return_value = None
        mock_ucli.return_value = None
        um = UMain(argv)
        um._prepare_exec()
        self.assertTrue(mock_getuid.called)
        self.assertTrue(mock_local.return_value.is_repo.called)
        self.assertTrue(mock_ucli.called)

    # @patch('udocker.umain.Msg')
    # @patch('udocker.umain.UdockerCLI')
    # @patch.object(UMain, '_prepare_exec')
    # def test_03_execute(self, mock_prep, mock_ucli, mock_msg):
    #     """Test03 UMain().execute()."""
    #     mock_msg.level = 0
    #     argv = ["udocker", "-h"]
    #     mock_prep.return_value = None
    #     mock_ucli.return_value.do_help.return_value = 0
    #     um = UMain(argv)
    #     status = um.execute()
    #     self.assertTrue(mock_prep.called)
    #     self.assertTrue(mock_ucli.return_value.do_help.called)
    #     self.assertEqual(status, 0)

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
