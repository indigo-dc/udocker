#!/usr/bin/env python
"""
udocker unit tests: UMain
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')
from udocker.umain import UMain


class UMainTestCase(TestCase):
    """Test UMain() class main udocker program."""

    # def setUp(self):
    #     pass
    #
    # def tearDown(self):
    #     pass

    @patch('udocker.umain.sys.exit')
    @patch('udocker.umain.os')
    @patch('udocker.umain.UdockerCLI')
    @patch('udocker.umain.LocalRepository')
    @patch('udocker.umain.Config')
    @patch('udocker.umain.CmdParser')
    @patch('udocker.umain.Msg')
    def test_01_init(self, mock_msg, mock_cmdp, mock_conf,
                     mock_local, mock_cli, mock_os, mock_exit):
        """Test UMain(argv) constructor."""

        # mock_cmdp.return_value.get.side_effect call order
        # --allow-root --config --debug    -D
        # --quiet      -q       --insecure --repo
        argv = ['udocker']
        conf = mock_conf.getconf()
        conf['verbose_level'] = 3
        mock_cmdp.return_value.parse.return_value = True

        # Test with no cmd options
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, False, False]
        UMain(argv)
        self.assertTrue(mock_cmdp.called)
        self.assertTrue(mock_conf.called)
        self.assertTrue(mock_conf.getconf.called)
        self.assertTrue(mock_msg.setlevel.called_with(conf['verbose_level']))
        self.assertTrue(mock_local.called)
        self.assertTrue(mock_cli.called)

        # Test root with no --allow-root
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, False, False]
        mock_os.geteuid.return_value = 0
        UMain(argv)
        self.assertTrue(mock_exit.called)
        mock_exit.reset_mock()

        # Test root with --allow-root
        mock_cmdp.return_value.get.side_effect = [True, False, False, False,
                                                  False, False, False, False]
        mock_os.geteuid.return_value = 0
        UMain(argv)
        self.assertFalse(mock_exit.called)
        mock_exit.reset_mock()
        mock_conf.reset_mock()

        # Test --debug
        mock_cmdp.return_value.get.side_effect = [False, False, True, False,
                                                  False, False, False, False]
        UMain(argv)
        #self.assertEqual(confget['verbose_level'], 5)

    @patch('udocker.umain.sys.exit')
    @patch('udocker.umain.os')
    @patch('udocker.umain.UdockerCLI')
    @patch('udocker.umain.LocalRepository')
    @patch('udocker.umain.Config')
    @patch('udocker.umain.CmdParser')
    @patch('udocker.umain.Msg')
    def test_02__execute(self, mock_msg, mock_cmdp, mock_conf,
                     mock_local, mock_cli, mock_os, mock_exit):
        """Test UMain()._execute()."""
        argv = ['udocker']
        um = UMain(argv)
        status = um._execute()
        self.assertEqual(status, 0)
        self.assertTrue(mock_cli.do_help.called)

    def test_03_start(self):
        """Test UMain().start()."""
        pass


if __name__ == '__main__':
    main()
