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
import sys
import unittest
import mock
from StringIO import StringIO

sys.path.append('../../')

from udocker.msg import Msg

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"

def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()

def is_writable_file(obj):
    """Check if obj is a file."""
    try:
        obj.write("")
    except(AttributeError, OSError, IOError):
        return False
    else:
        return True


class MsgTestCase(unittest.TestCase):
    """Test Msg() class screen error and info messages."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _verify_descriptors(self, msg):
        """Verify Msg() file descriptors."""
        self.assertTrue(is_writable_file(msg.chlderr))
        self.assertTrue(is_writable_file(msg.chldout))
        self.assertTrue(is_writable_file(msg.chldnul))

    def test_01_init(self):
        """Test Msg() constructor."""
        msg = Msg(0)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)

    def test_02_setlevel(self):
        """Test Msg.setlevel() change of log level."""
        msg = Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)
        msg = Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)

    @mock.patch('udocker.sys.stdout', new_callable=StringIO)
    def test_03_out(self, mock_stdout):
        """Test Msg.out() screen messages."""
        msg = Msg(Msg.MSG)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR

    @mock.patch('sys.stderr', new_callable=StringIO)
    def test_04_err(self, mock_stderr):
        """Test Msg.err() screen messages."""
        msg = Msg(Msg.ERR)
        msg.err("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stderr.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR
