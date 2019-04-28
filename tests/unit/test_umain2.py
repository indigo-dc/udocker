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
        argv = 'udocker'
        mock_cmdp.parse.return_value = True
        mock_os.geteuid.return_value = 0
        # mock_cmdp.get.return_value = None
        UMain(argv)
        assert mock_exit.called

        conf = mock_conf.getconf()

    def test_02__execute(self):
        """Test UMain()._execute()."""
        pass

    def test_03_start(self):
        """Test UMain().start()."""
        pass


if __name__ == '__main__':
    main()
