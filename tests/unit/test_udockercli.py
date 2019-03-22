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
import unittest
import mock

from udocker.cli import UdockerCLI


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class UdockerCLITestCase(unittest.TestCase):
    """Test UdockerTestCase() command line interface."""

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
        Config.keystore = "KEYSTORE"

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_dioapi, mock_dlocapi, mock_ks):
        """Test Udocker() constructor."""
        self._init()
        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_dlocapi.return_value = 789
        #
        udoc = UdockerCLI(mock_local)
        self.assertEqual(udoc.keystore, 123)
        self.assertEqual(udoc.dockerioapi, 456)
        self.assertEqual(udoc.dockerlocalfileapi, 789)

    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02__cdrepo(self, mock_local, mock_dioapi, mock_dlocapi, mock_ks,
                        mock_cmdp, mock_futil):
        """Test Udocker()._cdrepo()."""
        self._init()
        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_dlocapi.return_value = 789
        #
        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = True
        udoc = UdockerCLI(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = False
        mock_futil.return_value.isdir.return_value = False
        udoc = UdockerCLI(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = False
        mock_futil.return_value.isdir.return_value = True
        udoc = UdockerCLI(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03__check_imagespec(self, mock_local, mock_msg, mock_dioapi,
                                 mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker()._check_imagespec()."""
        self._init()
        mock_msg.level = 0
        #
        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(mock_local)
        status = udoc._check_imagespec("")
        self.assertEqual(status, (None, None))
        #
        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(mock_local)
        status = udoc._check_imagespec("AAA")
        self.assertEqual(status, ("AAA", "latest"))
        #
        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(mock_local)
        status = udoc._check_imagespec("AAA:45")
        self.assertEqual(status, ("AAA", "45"))

    @mock.patch('os.path.exists')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04_do_mkrepo(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_exists):
        """Test Udocker().do_mkrepo()."""
        self._init()
        mock_msg.level = 0
        #
        mock_cmdp.get.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = UdockerCLI(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.get.return_value = ""
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = UdockerCLI(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertTrue(status)
        #
        mock_cmdp.get.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = False
        udoc = UdockerCLI(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertFalse(status)

    @mock.patch('raw_input')
    @mock.patch('udocker.cli.UdockerCLI._search_print_v2')
    @mock.patch('udocker.cli.UdockerCLI._search_print_v1')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05_do_search(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp,
                          mock_print1, mock_print2, mock_rinput):
        """Test Udocker().do_search()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_search(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.return_value = None
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["results", ], ["repositories", ], [], ])
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_print1.called)
        self.assertTrue(mock_print2.called)
        #
        mock_print1.reset_mock()
        mock_print2.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        self.assertFalse(mock_print1.called)
        self.assertTrue(mock_print2.called)
        #
        mock_print1.reset_mock()
        mock_print2.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_rinput.return_value = "q"
        mock_dioapi.return_value.search_ended = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        self.assertFalse(mock_print1.called)
        self.assertFalse(mock_print2.called)

    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06_do_load(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_load()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = []
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = ["REPO", ]
        status = udoc.do_load(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07_do_import(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_import()."""
        self._init()
        mock_msg.level = 0
        cmd_options = [False, False, "", False,
                       "INFILE", "IMAGE", "" "", "", ]
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "", "", "", "", "", "", "", ]
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("", "")
        mock_cmdp.missing_options.return_value = False
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "")
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = False
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = True
        status = udoc.do_import(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('getpass')
    @mock.patch('raw_input')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08_do_login(self, mock_local, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp,
                         mock_rinput, mock_gpass):
        """Test Udocker().do_login()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["user", "pass", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        status = udoc.do_login(mock_cmdp)
        self.assertFalse(status)
        self.assertFalse(mock_rinput.called)
        self.assertFalse(mock_gpass.called)
        #
        mock_rinput.reset_mock()
        mock_gpass.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        status = udoc.do_login(mock_cmdp)
        self.assertFalse(status)
        self.assertTrue(mock_rinput.called)
        self.assertTrue(mock_gpass.called)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = True
        status = udoc.do_login(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_09_do_logout(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_logout()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        status = udoc.do_logout(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["ALL", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        mock_ks.return_value.erase.return_value = True
        status = udoc.do_logout(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_ks.return_value.erase.called)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = True
        status = udoc.do_logout(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_ks.return_value.delete.called)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_10_do_pull(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_pull()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = []
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = ["F1", "F2", ]
        status = udoc.do_pull(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._create')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_11_do_create(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_create):
        """Test Udocker().do_create()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = udoc.do_create(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = udoc.do_create(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = "CONTAINER_ID"
        status = udoc.do_create(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.container.structure.ContainerStructure')
    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_12__create(self, mock_local, mock_msg, mock_dioapi, mock_chkimg,
                        mock_cstruct):
        """Test Udocker()._create()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = False
        status = udoc._create("IMAGE:TAG")
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = True
        mock_chkimg.return_value = ("", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = udoc._create("IMAGE:TAG")
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = True
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = udoc._create("IMAGE:TAG")
        self.assertTrue(status)

    #    @mock.patch('udocker.cmdparser.CmdParser')
    #    @mock.patch('udocker.container.localrepo.LocalRepository')
    #    def test_14__get_run_options(self, mock_local, mock_cmdp):
    #        """Test Udocker()._get_run_options()"""
    #        self._init()
    #        #
    #        udoc = UdockerCLI(mock_local)
    #        udocker.engine.proot.PRootEngine = mock.MagicMock()
    #        udocker.engine.proot.PRootEngine.opt = dict()
    #        udocker.engine.proot.PRootEngine.opt["vol"] = []
    #        udocker.engine.proot.PRootEngine.opt["env"] = []
    #        mock_cmdp.get.return_value = "VALUE"
    #        udoc._get_run_options(mock_cmdp, udocker.engine.proot.PRootEngine)
    #        self.assertEqual(udocker.engine.proot.PRootEngine.opt["dns"], "VALUE")

    @mock.patch('udocker.cli.UdockerCLI._get_run_options')
    @mock.patch('udocker.engine.proot.PRootEngine')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.container.localrepo.LocalRepository.del_container')
    @mock.patch('os.path.realpath')
    def test_15_do_run(self, mock_realpath, mock_del, mock_local,
                       mock_msg, mock_dioapi, mock_dlocapi,
                       mock_ks, mock_cmdp, mock_eng, mock_getopt):
        """Test Udocker().do_run()."""
        self._init()
        mock_msg.level = 0
        mock_realpath.return_value = "/tmp"
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.return_value.missing_options.return_value = True
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        udoc = UdockerCLI(mock_local)
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udocker.Config.location = "/"
        mock_eng.return_value.run.return_value = True
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = True
        # mock_del.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = False
        # mock_del.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # # self.assertTrue(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = ""
        # mock_eng.return_value.run.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = UdockerCLI(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = False
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)

    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_16_do_images(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_images()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_images(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_values = []
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.isprotected_imagerepo.called)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["LONG", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        mock_local.get_layers.return_value = []
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.get_layers.called)

    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_17_do_ps(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_ps()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_ps(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = []
        udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.get_containers_list.called)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = [("ID", "NAME", ""), ]
        mock_local.isprotected_container.return_value = True
        mock_local.iswriteable_container.return_value = True
        udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.isprotected_container.called)

    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_18_do_rm(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_rm()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "12", "" "", "", ]
        mock_local.get_container_id.return_value = ""
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = True
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = False
        status = udoc.do_rm(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_19_do_rmi(self, mock_local, mock_msg, mock_dioapi,
                       mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_rmi()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = True
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = False
        status = udoc.do_rmi(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_20_do_protect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_protect()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = False
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_21_do_unprotect(self, mock_local, mock_msg, mock_dioapi,
                             mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_unprotect()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_unprotect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = False
        status = udoc.do_unprotect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = True
        status = udoc.do_unprotect(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.unprotect_imagerepo.return_value = True
        status = udoc.do_unprotect(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.unprotect_imagerepo.called)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_22_do_name(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_name()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = False
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = True
        status = udoc.do_name(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_23_do_rmname(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_rmname()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_rmname(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = False
        status = udoc.do_rmname(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = True
        status = udoc.do_rmname(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('json')
    @mock.patch('udocker.container.structure.ContainerStructure')
    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_24_do_inspect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg,
                           mock_cstruct, mock_json):
        """Test Udocker().do_inspect()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_inspect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = ("", "")
        status = udoc.do_inspect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "PRINT", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = ("DIR", "")
        status = udoc.do_inspect(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = (
            "", "JSON")
        status = udoc.do_inspect(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.cli.UdockerCLI._check_imagespec')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_25_do_verify(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_verify()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "")
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = False
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = True
        mock_local.verify_image.return_value = True
        status = udoc.do_verify(mock_cmdp)
        self.assertTrue(status)

    #@mock.patch('udocker.cmdparser.CmdParser')
    #@mock.patch('udocker.container.localrepo.LocalRepository')
    #def test_25_do_version(self, mock_local, mock_cmdp):
    #    """Test Udocker().do_version()."""
    #    self._init()
    #   udoc = UdockerCLI(mock_local)
    #   mock_cmdp.get.side_effect = ["run", "", "" "", "", ]
    #   version = udoc.do_version(mock_cmdp)
    #   self.assertIsNotNone(version)

    @mock.patch('udocker.msg.Msg.out')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_26_do_help(self, mock_local, mock_cmdp, mock_msgout):
        """Test Udocker().do_help()."""
        self._init()

        udoc = UdockerCLI(mock_local)
        mock_cmdp.get.side_effect = ["run", "help", "" "", "", ]
        udoc.do_help(mock_cmdp)
        self.assertTrue(mock_msgout.called)

    @mock.patch('udocker.tools.UdockerCLITools')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_27_do_install(self, mock_local, mock_msg, mock_cmdp,
                           mock_utools):
        """Test Udocker().do_install()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(False))
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

    @mock.patch('udocker.engine.execmode.ExecutionMode')
    @mock.patch('udocker.cmdparser.CmdParser')
    @mock.patch('udocker.helper.keystore.KeyStore')
    @mock.patch('udocker.docker.DockerLocalFileAPI')
    @mock.patch('udocker.docker.DockerIoAPI')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_28_do_setup(self, mock_local, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp, mock_exec):
        """Test Udocker().do_setup()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = False
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_exec.set_mode.return_value = False
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_exec.set_mode.return_value = True
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_local.isprotected_container.return_value = True
        mock_exec.set_mode.return_value = True
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = UdockerCLI(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_local.isprotected_container.return_value = False
        mock_exec.set_mode.return_value = True
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
