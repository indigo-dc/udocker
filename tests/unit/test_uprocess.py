#!/usr/bin/env python
"""
udocker unit tests: Uprocess
"""

import subprocess
from unittest import TestCase, main
from unittest.mock import patch
from udocker.utils.uprocess import Uprocess
from udocker.config import Config


class UprocessTestCase(TestCase):
    """Test case for the Uprocess class."""

    def setUp(self):
        Config().getconf()

    def tearDown(self):
        pass

    @patch('udocker.utils.uprocess.os.path.lexists')
    @patch('udocker.utils.uprocess.os.path.basename')
    def test_01_find_inpath(self, mock_base, mock_lexists):
        """Test01 Uprocess().find_inpath()."""
        fname = ''
        path = ''
        uproc = Uprocess()
        status = uproc.find_inpath(fname, path)
        self.assertEqual(status, '')

        fname = 'ls'
        path = '/bin'
        mock_base.return_value = 'ls'
        mock_lexists.return_value = True
        uproc = Uprocess()
        status = uproc.find_inpath(fname, path)
        self.assertEqual(status, '/bin/ls')

    @patch('udocker.utils.uprocess.subprocess.Popen')
    def test_02__check_output(self, mock_popen):
        """Test02 Uprocess()._check_output()."""
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 0
        uproc = Uprocess()
        status = uproc._check_output("CMD")
        self.assertEqual(status, "OUTPUT")

        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 1
        uproc = Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc._check_output, "CMD")

    @patch('udocker.utils.uprocess.subprocess.check_output')
    def test_03_check_output(self, mock_subp_chkout):
        """Test03 Uprocess().check_output()."""
        uproc = Uprocess()
        uproc.check_output("CMD")
        self.assertTrue(mock_subp_chkout.called)

    @patch('udocker.utils.uprocess.Uprocess.check_output')
    def test_04_get_output(self, mock_uproc_chkout):
        """Test04 Uprocess().get_output()."""
        mock_uproc_chkout.return_value = "OUTPUT"
        uproc = Uprocess()
        self.assertEqual("OUTPUT", uproc.get_output("CMD"))

        # uproc = Uprocess()
        # self.assertRaises(subprocess.CalledProcessError,
        #                   uproc.get_output("/bin/false"))

    # def test_05_call(self, mock_popen):
    #     """Test05 Uprocess().call()."""

    # def test_06_pipe(self, mock_popen):
    #     """Test06 Uprocess().pipe()."""


if __name__ == '__main__':
    main()
