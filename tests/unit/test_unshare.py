#!/usr/bin/env python
"""
udocker unit tests: Unshare
"""

from unittest import TestCase, main
from unittest.mock import patch, MagicMock
from udocker.helper.unshare import Unshare


class UnshareTestCase(TestCase):
    """Test Unshare()."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('udocker.helper.unshare.Msg.err')
    @patch('udocker.helper.unshare.ctypes.CDLL')
    def test_01_unshare(self, mock_cdll, mock_msg):
        """Test01 Unshare().unshare"""
        mock_msg.level = 0
        status = Unshare().unshare(False)
        self.assertTrue(mock_cdll.return_value.unshare.called)
        self.assertTrue(status)

        mock_cdll.return_value.unshare.return_value = -1
        status = Unshare().unshare(True)
        self.assertTrue(mock_cdll.return_value.unshare.called)
        self.assertFalse(status)

    @patch('udocker.helper.unshare.os._exit')
    @patch.object(Unshare, 'unshare')
    @patch('udocker.helper.unshare.os.setgroups')
    @patch('udocker.helper.unshare.os.setuid')
    @patch('udocker.helper.unshare.os.setgid')
    @patch('udocker.helper.unshare.Msg.err')
    @patch('udocker.helper.unshare.os.waitpid')
    @patch('udocker.helper.unshare.NixAuthentication.user_in_subgid')
    @patch('udocker.helper.unshare.subprocess.call')
    @patch('udocker.helper.unshare.NixAuthentication.user_in_subuid')
    @patch('udocker.helper.unshare.HostInfo')
    @patch('udocker.helper.unshare.os.read')
    @patch('udocker.helper.unshare.os.close')
    @patch('udocker.helper.unshare.os.fork')
    @patch('udocker.helper.unshare.os.pipe')
    def test_02_namespace_exec(self, mock_pipe, mock_fork, mock_close,
                               mock_read, mock_hinfo, mock_usubuid,
                               mock_call, mock_usubgid, mock_wait, mock_msg,
                               mock_setgid, moc_setuid, mock_setgrp,
                               mock_ush, mock_exit):
        """Test02 Unshare().namespace_exec"""

        # cpid exists waitpid=0
        mock_msg.level = 0
        mock_pipe.side_effect = [('rfid1', 'wfid1'), ('rfid2', 'wfid2')]
        mock_fork.return_value = 1234
        mock_close.side_effect = [None, None]
        mock_read.return_value = None
        mock_hinfo.return_value.username.return_value = 'user'
        mock_hinfo.uid = 1000
        mock_usubuid.return_value = [(1000, 1000)]
        mock_usubgid.return_value = [(1000, 1000)]
        mock_call.side_effect = [None, None]
        mock_wait.return_value = (123, 0)
        status = Unshare().namespace_exec('1')
        self.assertEqual(mock_pipe.call_count, 2)
        self.assertTrue(mock_fork.called)
        self.assertEqual(mock_close.call_count, 2)
        self.assertTrue(mock_hinfo.return_value.username.called)
        self.assertTrue(mock_usubuid.called)
        self.assertTrue(mock_usubgid.called)
        self.assertEqual(mock_call.call_count, 2)
        self.assertFalse(mock_msg.called)
        self.assertTrue(status)

        # cpid not exists
        mock_method = MagicMock(name='method')
        mock_pipe.side_effect = [('rfid1', 'wfid1'), ('rfid2', 'wfid2')]
        mock_fork.return_value = None
        mock_ush.return_value = None
        mock_close.side_effect = [None, None]
        mock_read.return_value = None
        mock_setgid.return_value = None
        moc_setuid.return_value = None
        mock_setgrp.return_value = None
        mock_exit.return_value = 1
        status = Unshare().namespace_exec(mock_method)
        self.assertTrue(status)


if __name__ == '__main__':
    main()
