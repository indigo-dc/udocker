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

sys.path.append('.')

from udocker.engine.fakechroot import FakechrootEngine


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class FakechrootEngineTestCase(unittest.TestCase):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.MagicMock()
        Config.hostauth_list = ("/etc/passwd", "/etc/group")
        Config.cmd = "/bin/bash"
        Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                                          ["taskset", "-c", "%s", ])
        Config.valid_host_env = "HOME"
        Config.return_value.username.return_value = "user"
        Config.return_value.userhome.return_value = "/"
        Config.return_value.oskernel.return_value = "4.8.13"
        Config.location = ""

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01__init(self, mock_local):
        """Test FakechrootEngine Constructor."""
        self._init()

        ufake = FakechrootEngine(mock_local)
        self.assertEqual(ufake._fakechroot_so, "")
        self.assertIsNone(ufake._elfpatcher)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('os.path')
    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02__select_fakechroot_so(self, mock_local, mock_futil,
                                      mock_config, mock_path, mock_msg):
        """Select fakechroot sharable object library."""

        self._init()

        #ufake = udocker.FakechrootEngine(mock_local)
        #out = ufake._select_fakechroot_so()
        #self.assertTrue(mock_msg.return_value.err.called)


    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03__uid_check(self, mock_local, mock_msg):
        """Set the uid_map string for container run command"""
        self._init()

        ufake = FakechrootEngine(mock_local)
        ufake.opt["user"] = "root"
        ufake._uid_check_noroot()
        self.assertTrue(mock_msg.return_value.err.called)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.nixauth.NixAuthentication')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon')
    def test_04__setup_container_user(self, mock_eecom, mock_auth,
                                      mock_local, mock_msg):
        """ Override method ExecutionEngineCommon._setup_container_user()."""
        self._init()

        mock_eecom.return_value._uid_gid_from_str.side_effect = (None, None)
        ufake = FakechrootEngine(mock_local)
        status = ufake._setup_container_user(":lalves")
        self.assertFalse(status)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Get the volume bindings string for fakechroot run."""
        self._init()

        ufake = FakechrootEngine(mock_local)
        out = ufake._get_volume_bindings()
        self.assertEqual(out, ("", ""))

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__get_access_filesok(self, mock_local):
        """Circumvent mpi init issues when calling access().

        A list of certain existing files is provided
        """
        self._init()

        ufake = FakechrootEngine(mock_local)
        out = ufake._get_access_filesok()
        self.assertEqual(out, "")

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.structure.ContainerStructure')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07__fakechroot_env_set(self, mock_local, mock_struct,
                                    mock_msg, mock_futil):
        """fakechroot environment variables to set."""
        self._init()

        # mock_futil.return_value.find_file_in_dir.return_value = True
        # ufake = udocker.FakechrootEngine(mock_local)
        #
        # ufake._fakechroot_env_set()
        # self.assertTrue(mock_eecom.return_value.exec_mode.called)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.structure.ContainerStructure')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08_run(self, mock_local, mock_struct, mock_msg):
        """Execute a Docker container using Fakechroot.

        This is the main
        method invoked to run the a container with Fakechroot.
          * argument: container_id or name
          * options:  many via self.opt see the help
        """
        self._init()

        ufake = FakechrootEngine(mock_local)
        status = ufake.run("container_id")
        self.assertEqual(status, 2)


if __name__ == '__main__':
    unittest.main()
