#!/usr/bin/env python
"""
udocker unit tests: FakechrootEngine
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.engine.fakechroot import FakechrootEngine


class FakechrootEngineTestCase(TestCase):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['valid_host_env'] = "HOME"
        self.conf['username'] = "user"
        self.conf['userhome'] = "/"
        self.conf['oskernel'] = "4.8.13"
        self.conf['location'] = ""

        self.local = LocalRepository(self.conf)
        self.xmode = "F1"
        self.ufake = FakechrootEngine(self.conf, self.local, self.xmode)

    def tearDown(self):
        pass

    @patch('udocker.container.localrepo.LocalRepository')
    def test_01__init(self, mock_local):
        """Test FakechrootEngine Constructor."""
        self.assertEqual(self.ufake._fakechroot_so, "")
        self.assertIsNone(self.ufake._elfpatcher)

    # @patch('udocker.msg.Msg.err')
    # @patch('udocker.engine.fakechroot.os.path')
    # @patch('udocker.utils.fileutil.FileUtil')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_02__select_fakechroot_so(self, mock_local, mock_futil,
    #                                   mock_path, mock_msg):
    #     """Select fakechroot sharable object library."""
    #     out = self.ufake._select_fakechroot_so()
    #     self.assertTrue(mock_msg.called)


    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_03__uid_check(self, mock_local, mock_msg):
    #     """Set the uid_map string for container run command"""
    #     self.ufake.opt["user"] = "root"
    #     self.ufake._uid_check_noroot()
    #     self.assertTrue(mock_msg.return_value.err.called)

    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.localrepo.LocalRepository')
    # @patch('udocker.helper.nixauth.NixAuthentication')
    # @patch('udocker.engine.base.ExecutionEngineCommon._uid_gid_from_str')
    # def test_04__setup_container_user(self, mock_eecom, mock_auth,
    #                                   mock_local, mock_msg):
    #     """ Override method ExecutionEngineCommon._setup_container_user()."""
    #     mock_eecom.side_effect = (None, None)
    #     status = self.ufake._setup_container_user(":lalves")
    #     self.assertFalse(status)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Get the volume bindings string for fakechroot run."""
        out = self.ufake._get_volume_bindings()
        self.assertEqual(out, ("", ""))

    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__get_access_filesok(self, mock_local):
        """Circumvent mpi init issues when calling access().
        A list of certain existing files is provided
        """
        out = self.ufake._get_access_filesok()
        self.assertEqual(out, "")

    # @patch('udocker.utils.fileutil.FileUtil')
    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.structure.ContainerStructure')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_07__fakechroot_env_set(self, mock_local, mock_struct,
    #                                 mock_msg, mock_futil):
    #     """fakechroot environment variables to set."""
    #     mock_futil.return_value.find_file_in_dir.return_value = True
    #     self.ufake._fakechroot_env_set()
    #     self.assertTrue(mock_eecom.return_value.exec_mode.called)

    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.structure.ContainerStructure')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_08_run(self, mock_local, mock_struct, mock_msg):
    #     """Execute a Docker container using Fakechroot.
    #     This is the main
    #     method invoked to run the a container with Fakechroot.
    #       * argument: container_id or name
    #       * options:  many via self.opt see the help
    #     """
    #     status = self.ufake.run("container_id")
    #     self.assertEqual(status, 2)


if __name__ == '__main__':
    main()
