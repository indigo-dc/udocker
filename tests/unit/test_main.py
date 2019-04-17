#!/usr/bin/env python
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

sys.path.append('.')
from udocker.umain import UMain


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class UMainTestCase(unittest.TestCase):
    """Test UMain() class main udocker program."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.MagicMock()
        Config.hostauth_list = ("/etc/passwd", "/etc/group")
        Config.cmd = "/bin/bash"
        #udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
        #                       ["taskset", "-c", "%s", ])
        Config.cpu_affinity_exec_tools = ("taskset -c ", "numactl -C ")
        Config.valid_host_env = "HOME"
        Config.username.return_value = "user"
        Config.userhome.return_value = "/"
        Config.location = ""
        Config.oskernel.return_value = "4.8.13"
        Config.verbose_level = 3
        Config.http_insecure = False
        Config.topdir = "/.udocker"

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.cmdparser.CmdParser')
    def test_01_init(self, mock_cmdp, mock_msg):
        """Test UMain() constructor."""
        self._init()
        mock_cmdp.return_value.parse.return_value = False
        with self.assertRaises(SystemExit) as mainexpt:
            UMain()
        self.assertEqual(mainexpt.exception.code, 0)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.cli.UdockerCLI')
    @mock.patch('udocker.config.Config.user_init')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.cmdparser.CmdParser')
    def test_02_init(self, mock_cmdp, mock_msg, mock_conf_init, mock_udocker,
                     mock_localrepo):
        """Test UMain() constructor."""
        self._init()
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, False, False,
                                                  False]
        UMain()
        self.assertEqual(udocker.Config.verbose_level, 3)
        # --debug
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, True, False,
                                                  False, False, False, False,
                                                  False]
        UMain()
        self.assertNotEqual(udocker.Config.verbose_level, 3)
        # -D
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, True,
                                                  False, False, False, False,
                                                  False]
        UMain()
        self.assertNotEqual(udocker.Config.verbose_level, 3)
        # --quiet
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  True, False, False, False,
                                                  False]
        UMain()
        self.assertNotEqual(udocker.Config.verbose_level, 3)
        # -q
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, True, False, False,
                                                  False]
        UMain()
        self.assertNotEqual(udocker.Config.verbose_level, 3)
        # --insecure
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, True, False,
                                                  False, False]
        UMain()
        self.assertTrue(udocker.Config.http_insecure)
        # --repo=
        mock_localrepo.return_value.is_repo.return_value = True
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, False, True,
                                                  "/TOPDIR"]
        with self.assertRaises(SystemExit) as mainexpt:
            UMain()
        self.assertEqual(mainexpt.exception.code, 0)


    @mock.patch('udocker.UMain.__init__')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.cli.UdockerCLI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.cmdparser.CmdParser')
    def test_03_execute(self, mock_cmdp, mock_msg, mock_udocker,
                        mock_localrepo, mock_main_init):
        """Test UMain().execute()."""
        self._init()
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [True, False, False, False,
                                                  False, False, False, False]
        umain = UMain()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        status = umain._execute()
        self.assertEqual(status, 0)
        #
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, True, False, False,
                                                  False, False, False, False]
        umain = UMain()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        status = umain._execute()
        self.assertEqual(status, 0)
        #
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, False, "ERR", False,
                                                  False, False, False, False]
        umain = UMain()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        umain.cmdp.reset_mock()
        status = umain._execute()
        self.assertTrue(umain.udocker.do_help.called)
        #
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, False, "run", True,
                                                  False, False, False, False]
        umain = UMain()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        umain.cmdp.reset_mock()
        status = umain.execute()
        self.assertTrue(umain.udocker.do_help.called)

    @mock.patch('udocker.UMain.__init__')
    @mock.patch('udocker.UMain._execute')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.msg.Msg')
    def test_04_start(self, mock_msg, mock_futil, mock_main_execute,
                      mock_main_init):
        """Test UMain().start()."""
        self._init()
        mock_main_init.return_value = None
        mock_main_execute.return_value = 2
        umain = UMain()
        status = umain.start()
        self.assertEqual(status, 2)
        #
        self._init()
        mock_main_init.return_value = None
        mock_main_execute.return_value = 2
        mock_main_execute.side_effect = KeyboardInterrupt("CTRLC")
        umain = UMain()
        status = umain.start()
        self.assertEqual(status, 1)


if __name__ == '__main__':
    unittest.main()
