#!/usr/bin/env python
"""
udocker unit tests: Uprocess
"""
import subprocess
import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

sys.path.append('.')

from udocker.utils.uprocess import Uprocess


class UprocessTestCase(TestCase):
    """Test case for the Uprocess class."""

    @patch('subprocess.Popen')
    def test_01__check_output(self, mock_popen):
        """Test _check_output()."""
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 0
        uproc = Uprocess()
        status = uproc._check_output("CMD")
        self.assertEqual(status, "OUTPUT")
        #
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 1
        uproc = Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc._check_output, "CMD")

    @patch('subprocess.check_output')
    def test_02_check_output(self, mock_subp_chkout):
        """Test check_output()."""
        uproc = Uprocess()
        uproc.check_output("CMD")
        self.assertTrue(mock_subp_chkout.called)

    @patch('udocker.utils.uprocess.Uprocess.check_output')
    def test_03_get_output(self, mock_uproc_chkout):
        """Test get_output()."""
        mock_uproc_chkout.return_value = "OUTPUT"
        uproc = Uprocess()
        self.assertEqual("OUTPUT", uproc.get_output("CMD"))

    def test_04_get_output(self):
        """Test get_output()."""
        uproc = Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc.get_output("/bin/false"))


if __name__ == '__main__':
    main()
