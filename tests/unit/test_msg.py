#!/usr/bin/env python
"""
udocker unit tests: Msg
"""
import sys
from unittest import TestCase, main
from unittest.mock import patch
from io import StringIO
from udocker.msg import Msg

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"
BUILTINS = "builtins"


def is_writable_file(obj):
    """Check if obj is a file."""
    try:
        obj.write("")
    except(AttributeError, OSError, IOError):
        return False
    else:
        return True


class MsgTestCase(TestCase):
    """Test Msg() class screen error and info messages."""

    def _verify_descriptors(self, msg):
        """Verify Msg() file descriptors."""
        self.assertTrue(is_writable_file(msg.chlderr))
        self.assertTrue(is_writable_file(msg.chldout))
        self.assertTrue(is_writable_file(msg.chldnul))

    def test_01_init(self):
        """Test01 Msg() constructor."""
        msg = Msg(0)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)

    def test_02_setlevel(self):
        """Test02 Msg.setlevel()."""
        msg = Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)

        msg = Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)

    @patch('sys.stdout', new_callable=StringIO)
    def test_03_out(self, mock_stdout):
        """Test03 Msg.out()."""
        msg = Msg(Msg.MSG)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR

    @patch('sys.stderr', new_callable=StringIO)
    def test_04_err(self, mock_stderr):
        """Test04 Msg.err()."""
        msg = Msg(Msg.ERR)
        msg.err("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stderr.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR


if __name__ == '__main__':
    main()
