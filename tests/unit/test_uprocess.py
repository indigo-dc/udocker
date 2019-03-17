#!/usr/bin/env python2
"""
udocker unit tests.

Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import subprocess
import sys
import unittest
import mock

sys.path.append('../../')

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.utils.uprocess import Uprocess

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "0.0.3"
__date__ = "2016"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()

class UprocessTestCase(unittest.TestCase):
    """Test case for the Uprocess class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('subprocess.Popen')
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

    @mock.patch('subprocess.check_output')
    def test_02_check_output(self, mock_subp_chkout):
        """Test check_output()."""
        uproc = Uprocess()
        uproc.check_output("CMD")
        self.assertTrue(mock_subp_chkout.called)

    @mock.patch('udocker.utils.uprocess.Uprocess.check_output')
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

