#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: UdockerCLI
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.cli import UdockerCLI

if sys.version_info[0] >= 3:
    BUILTIN = "builtins"
else:
    BUILTIN = "__builtin__"

BOPEN = BUILTIN + '.open'


class UdockerCLITestCase(TestCase):
    """Test UdockerTestCase() command line interface."""

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
        self.conf['keystore'] = "KEYSTORE"

        self.local = LocalRepository(self.conf)
        self.udoc = UdockerCLI(self.local, self.conf)

    def tearDown(self):
        pass

    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_dioapi, mock_dlocapi, mock_ks):
        """Test UdockerCLI() constructor."""

        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_dlocapi.return_value = 789
        #

        self.assertEqual(self.udoc.keystore, 123)
        self.assertEqual(self.udoc.dockerioapi, 456)
        self.assertEqual(self.udoc.dockerlocalfileapi, 789)

    # @patch('udocker.utils.fileutil.FileUtil')
    # @patch('udocker.cmdparser.CmdParser')
    # @patch('udocker.helper.keystore.KeyStore')
    # @patch('udocker.docker.DockerLocalFileAPI')
    # @patch('udocker.docker.DockerIoAPI')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_02__cdrepo(self, mock_local, mock_dioapi, mock_dlocapi, mock_ks,
    #                     mock_cmdp, mock_futil):
    #     """Test UdockerCLI()._cdrepo()."""
    #
    #     mock_local.homedir = "/h/u/.udocker"
    #     mock_ks.return_value = 123
    #     mock_dioapi.return_value = 456
    #     mock_dlocapi.return_value = 789
    #     #
    #     mock_cmdp.get.return_value = "/u/containers/AAAA"
    #     mock_cmdp.missing_options.return_value = True
    #
    #     status = self.udoc._cdrepo(mock_cmdp)
    #     self.assertFalse(status)
    #     #
    #     mock_cmdp.get.return_value = "/u/containers/AAAA"
    #     mock_cmdp.missing_options.return_value = False
    #     mock_futil.return_value.isdir.return_value = False
    #
    #     status = self.udoc._cdrepo(mock_cmdp)
    #     self.assertFalse(status)
    #     #
    #     mock_cmdp.get.return_value = "/u/containers/AAAA"
    #     mock_cmdp.missing_options.return_value = False
    #     mock_futil.return_value.isdir.return_value = True
    #
    #     status = self.udoc._cdrepo(mock_cmdp)
    #     self.assertTrue(status)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_03__check_imagespec(self, mock_local, mock_msg, mock_dioapi,
                                 mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI()._check_imagespec()."""

        mock_msg.level = 0
        #
        mock_dioapi.is_repo_name = False

        status = self.udoc._check_imagespec("")
        self.assertEqual(status, (None, None))
        #
        mock_dioapi.is_repo_name = False

        status = self.udoc._check_imagespec("AAA")
        self.assertEqual(status, ("AAA", "latest"))
        #
        mock_dioapi.is_repo_name = False

        status = self.udoc._check_imagespec("AAA:45")
        self.assertEqual(status, ("AAA", "45"))

    @patch('udocker.cmdparser.CmdParser.get')
    @patch('udocker.cli.os.path.exists')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_04_do_mkrepo(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_exists,
                          mock_cmdget):
        """Test UdockerCLI().do_mkrepo()."""

        mock_msg.level = 0
        #
        mock_cmdget.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True

        status = self.udoc.do_mkrepo(mock_cmdp)
        self.assertEqual(status, 1)
        #
        mock_cmdget.return_value = ""
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True

        status = self.udoc.do_mkrepo(mock_cmdp)
        self.assertEqual(status, 0)
        #
        mock_cmdget.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = False

        status = self.udoc.do_mkrepo(mock_cmdp)
        self.assertEqual(status, 1)

    # @patch.object(BUILTIN, 'raw_input')
    # @patch('udocker.cli.UdockerCLI._search_print_v2')
    # @patch('udocker.cli.UdockerCLI._search_print_v1')
    # @patch('udocker.cmdparser.CmdParser')
    # @patch('udocker.helper.keystore.KeyStore')
    # @patch('udocker.docker.DockerLocalFileAPI')
    # @patch('udocker.docker.DockerIoAPI')
    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_05_do_search(self, mock_local, mock_msg, mock_dioapi,
    #                       mock_dlocapi, mock_ks, mock_cmdp,
    #                       mock_print1, mock_print2, mock_rinput):
    #     """Test UdockerCLI().do_search()."""
    #
    #     mock_msg.level = 0
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_cmdp.missing_options.return_value = True
    #     status = self.udoc.do_search(mock_cmdp)
    #     self.assertFalse(status)
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dioapi.return_value.search_get_page.return_value = None
    #     status = self.udoc.do_search(mock_cmdp)
    #     self.assertTrue(status)
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dioapi.return_value.search_get_page.side_effect = (
    #         [["results", ], ["repositories", ], [], ])
    #     status = self.udoc.do_search(mock_cmdp)
    #     self.assertTrue(status)
    #     self.assertTrue(mock_print1.called)
    #     self.assertTrue(mock_print2.called)
    #     #
    #     mock_print1.reset_mock()
    #     mock_print2.reset_mock()
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dioapi.return_value.search_get_page.side_effect = (
    #         [["zzz", ], ["repositories", ], [], ])
    #     status = self.udoc.do_search(mock_cmdp)
    #     self.assertTrue(status)
    #     self.assertFalse(mock_print1.called)
    #     self.assertTrue(mock_print2.called)
    #     #
    #     mock_print1.reset_mock()
    #     mock_print2.reset_mock()
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_cmdp.missing_options.return_value = False
    #     mock_rinput.return_value = "q"
    #     mock_dioapi.return_value.search_ended = False
    #     mock_dioapi.return_value.search_get_page.side_effect = (
    #         [["zzz", ], ["repositories", ], [], ])
    #     status = self.udoc.do_search(mock_cmdp)
    #     self.assertTrue(status)
    #     self.assertFalse(mock_print1.called)
    #     self.assertFalse(mock_print2.called)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_06_do_load(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_load()."""

        mock_msg.level = 0
        #

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        status = self.udoc.do_load(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        status = self.udoc.do_load(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = []
        status = self.udoc.do_load(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = ["REPO", ]
        status = self.udoc.do_load(mock_cmdp)
        self.assertEqual(status, 0)

    # @patch('udocker.cli.UdockerCLI._check_imagespec')
    # @patch('udocker.cmdparser.CmdParser')
    # @patch('udocker.helper.keystore.KeyStore')
    # @patch('udocker.docker.DockerLocalFileAPI')
    # @patch('udocker.docker.DockerIoAPI')
    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_07_do_import(self, mock_local, mock_msg, mock_dioapi,
    #                       mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
    #     """Test UdockerCLI().do_import()."""
    #
    #     mock_msg.level = 0
    #     cmd_options = [False, False, "", False,
    #                    "INFILE", "IMAGE", "" "", "", ]
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "", "", "", "", "", "", "", ]
    #     status = self.udoc.do_import(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #     mock_cmdp.reset_mock()
    #
    #     mock_cmdp.get.side_effect = cmd_options
    #     mock_chkimg.return_value = ("", "")
    #     mock_cmdp.missing_options.return_value = False
    #     status = self.udoc.do_import(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #     mock_cmdp.reset_mock()
    #
    #     mock_cmdp.get.side_effect = cmd_options
    #     mock_chkimg.return_value = ("IMAGE", "")
    #     mock_cmdp.missing_options.return_value = True
    #     status = self.udoc.do_import(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #     mock_cmdp.reset_mock()
    #
    #     mock_cmdp.get.side_effect = cmd_options
    #     mock_chkimg.return_value = ("IMAGE", "TAG")
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dlocapi.return_value.import_toimage.return_value = False
    #     status = self.udoc.do_import(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #     mock_cmdp.reset_mock()
    #
    #     mock_cmdp.get.side_effect = cmd_options
    #     mock_chkimg.return_value = ("IMAGE", "TAG")
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dlocapi.return_value.import_toimage.return_value = True
    #     status = self.udoc.do_import(mock_cmdp)
    #     self.assertEqual(status, 0)

    # @patch('gudocker.cli.etpass.getpass')
    # @patch.object(BUILTIN, 'raw_input')
    # @patch('udocker.cmdparser.CmdParser')
    # @patch('udocker.helper.keystore.KeyStore')
    # @patch('udocker.docker.DockerLocalFileAPI')
    # @patch('udocker.docker.DockerIoAPI')
    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_08_do_login(self, mock_local, mock_msg, mock_dioapi,
    #                      mock_dlocapi, mock_ks, mock_cmdp,
    #                      mock_rinput, mock_gpass):
    #     """Test UdockerCLI().do_login()."""
    #
    #     mock_msg.level = 0
    #     #
    #
    #     mock_cmdp.get.side_effect = ["user", "pass", "" "", "", ]
    #     mock_rinput.return_value = "user"
    #     mock_gpass.return_value = "pass"
    #     mock_ks.return_value.put.return_value = False
    #     status = self.udoc.do_login(mock_cmdp)
    #     self.assertFalse(status)
    #     self.assertFalse(mock_rinput.called)
    #     self.assertFalse(mock_gpass.called)
    #     #
    #     mock_rinput.reset_mock()
    #     mock_gpass.reset_mock()
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_rinput.return_value = "user"
    #     mock_gpass.return_value = "pass"
    #     mock_ks.return_value.put.return_value = False
    #     status = self.udoc.do_login(mock_cmdp)
    #     self.assertFalse(status)
    #     self.assertTrue(mock_rinput.called)
    #     self.assertTrue(mock_gpass.called)
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_rinput.return_value = "user"
    #     mock_gpass.return_value = "pass"
    #     mock_ks.return_value.put.return_value = True
    #     status = self.udoc.do_login(mock_cmdp)
    #     self.assertTrue(status)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_09_do_logout(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_logout()."""

        mock_msg.level = 0
        #

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        status = self.udoc.do_logout(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.get.side_effect = ["ALL", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        mock_ks.return_value.erase.return_value = True
        status = self.udoc.do_logout(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_ks.return_value.erase.called)
        #

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = True
        status = self.udoc.do_logout(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_ks.return_value.delete.called)

    # @patch('udocker.cli.UdockerCLI._check_imagespec')
    # @patch('udocker.cmdparser.CmdParser')
    # @patch('udocker.helper.keystore.KeyStore')
    # @patch('udocker.docker.DockerLocalFileAPI')
    # @patch('udocker.docker.DockerIoAPI')
    # @patch('udocker.msg.Msg')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_10_do_pull(self, mock_local, mock_msg, mock_dioapi,
    #                     mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
    #     """Test UdockerCLI().do_pull()."""
    #
    #     mock_msg.level = 0
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_chkimg.return_value = ("", "TAG")
    #     status = self.udoc.do_pull(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_chkimg.return_value = ("IMAGE", "TAG")
    #     mock_cmdp.missing_options.return_value = True
    #     status = self.udoc.do_pull(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_chkimg.return_value = ("IMAGE", "TAG")
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dioapi.return_value.get.return_value = []
    #     status = self.udoc.do_pull(mock_cmdp)
    #     self.assertEqual(status, 1)
    #     #
    #
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_chkimg.return_value = ("IMAGE", "TAG")
    #     mock_cmdp.missing_options.return_value = False
    #     mock_dioapi.return_value.get.return_value = ["F1", "F2", ]
    #     status = self.udoc.do_pull(mock_cmdp)
    #     self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._create')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_11_do_create(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_create):
        """Test UdockerCLI().do_create()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = self.udoc.do_create(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = self.udoc.do_create(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = "CONTAINER_ID"
        status = self.udoc.do_create(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.container.structure.ContainerStructure')
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.docker.DockerIoAPI.is_repo_name')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_12__create(self, mock_local, mock_msg, mock_reponame, mock_chkimg,
                        mock_cstruct):
        """Test UdockerCLI()._create()."""

        mock_msg.level = 0
        #

        mock_reponame.return_value = False
        status = self.udoc._create("IMAGE:TAG")
        self.assertEqual(status, 1)
        #

        mock_reponame.return_value = True
        mock_chkimg.return_value = ("", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = self.udoc._create("IMAGE:TAG")
        self.assertEqual(status, 1)
        #

        mock_reponame.return_value = True
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = self.udoc._create("IMAGE:TAG")
        self.assertEqual(status, 0)

    #    @patch('udocker.cmdparser.CmdParser')
    #    @patch('udocker.container.localrepo.LocalRepository')
    #    def test_14__get_run_options(self, mock_local, mock_cmdp):
    #        """Test UdockerCLI()._get_run_options()"""
    #
    #        #
    #
    #        udocker.engine.proot.PRootEngine = mock.MagicMock()
    #        udocker.engine.proot.PRootEngine.opt = dict()
    #        udocker.engine.proot.PRootEngine.opt["vol"] = []
    #        udocker.engine.proot.PRootEngine.opt["env"] = []
    #        mock_cmdp.get.return_value = "VALUE"
    #        self.udoc._get_run_options(mock_cmdp, udocker.engine.proot.PRootEngine)
    #        self.assertEqual(udocker.engine.proot.PRootEngine.opt["dns"], "VALUE")

    @patch('udocker.cli.UdockerCLI._get_run_options')
    @patch('udocker.engine.proot.PRootEngine')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.container.localrepo.LocalRepository.del_container')
    @patch('os.path.realpath')
    def test_15_do_run(self, mock_realpath, mock_del, mock_local,
                       mock_msg, mock_dioapi, mock_dlocapi,
                       mock_ks, mock_cmdp, mock_eng, mock_getopt):
        """Test UdockerCLI().do_run()."""

        mock_msg.level = 0
        mock_realpath.return_value = "/tmp"
        #

        mock_cmdp.return_value.missing_options.return_value = True
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        status = self.udoc.do_run(mock_cmdp)
        self.assertEqual(status, 1)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()

        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        self.conf['location'] = "/"
        mock_eng.return_value.run.return_value = True
        status = self.udoc.do_run(mock_cmdp)
        self.assertEqual(status, 1)

        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # status = self.udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = True
        # mock_del.return_value = True
        # status = self.udoc.do_run(mock_cmdp)
        # self.assertFalse(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = False
        # mock_del.return_value = True
        # status = self.udoc.do_run(mock_cmdp)
        # # self.assertTrue(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = ""
        # mock_eng.return_value.run.return_value = True
        # status = self.udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # status = self.udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = True
        # status = self.udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = False
        # status = self.udoc.do_run(mock_cmdp)
        # self.assertFalse(status)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_16_do_images(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_images()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = self.udoc.do_images(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_values = []
        status = self.udoc.do_images(mock_cmdp)
        self.assertEqual(status, 0)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        status = self.udoc.do_images(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_local.isprotected_imagerepo.called)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["LONG", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        mock_local.get_layers.return_value = []
        status = self.udoc.do_images(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_local.get_layers.called)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_17_do_ps(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_ps()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = self.udoc.do_ps(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = []
        self.udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.get_containers_list.called)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = [("ID", "NAME", ""), ]
        mock_local.isprotected_container.return_value = True
        mock_local.iswriteable_container.return_value = True
        self.udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.isprotected_container.called)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_18_do_rm(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_rm()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = self.udoc.do_rm(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = self.udoc.do_rm(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "12", "" "", "", ]
        mock_local.get_container_id.return_value = ""
        status = self.udoc.do_rm(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = True
        status = self.udoc.do_rm(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = False
        status = self.udoc.do_rm(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_19_do_rmi(self, mock_local, mock_msg, mock_dioapi,
                       mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_rmi()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_rmi(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = self.udoc.do_rmi(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = True
        status = self.udoc.do_rmi(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = False
        status = self.udoc.do_rmi(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_20_do_protect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_protect()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_protect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = False
        status = self.udoc.do_protect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = True
        status = self.udoc.do_protect(mock_cmdp)
        self.assertEqual(status, 0)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = self.udoc.do_protect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = self.udoc.do_protect(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_21_do_unprotect(self, mock_local, mock_msg, mock_dioapi,
                             mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_unprotect()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_unprotect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = False
        status = self.udoc.do_unprotect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = True
        status = self.udoc.do_unprotect(mock_cmdp)
        self.assertEqual(status, 0)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.unprotect_imagerepo.return_value = True
        status = self.udoc.do_unprotect(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_local.unprotect_imagerepo.called)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_22_do_name(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_name()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_name(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        status = self.udoc.do_name(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = False
        status = self.udoc.do_name(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = True
        status = self.udoc.do_name(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_23_do_rmname(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_rmname()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_rmname(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = False
        status = self.udoc.do_rmname(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = True
        status = self.udoc.do_rmname(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.get_container_id')
    @patch('udocker.cmdparser.CmdParser.missing_options')
    @patch('udocker.container.structure.ContainerStructure')
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.container.structure.ContainerStructure.get_container_attr')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_24_do_inspect(self, mock_local, mock_msg, mock_contattr,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg,
                           mock_cstruct, mock_missopt, mock_contid):
        """Test UdockerCLI().do_inspect()."""

        mock_msg.level = 0
        #

        mock_missopt.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_inspect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_missopt.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_contattr.return_value = ("", "")
        status = self.udoc.do_inspect(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_missopt.return_value = False
        mock_cmdp.get.side_effect = ["", "PRINT", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_contattr.return_value = ("DIR", "")
        status = self.udoc.do_inspect(mock_cmdp)
        self.assertEqual(status, 0)
        #

        mock_missopt.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_contattr.return_value = ("", "JSON")
        status = self.udoc.do_inspect(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_25_do_verify(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_verify()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = self.udoc.do_verify(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "")
        status = self.udoc.do_verify(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = False
        status = self.udoc.do_verify(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = True
        mock_local.verify_image.return_value = True
        status = self.udoc.do_verify(mock_cmdp)
        self.assertEqual(status, 0)

    #@patch('udocker.cmdparser.CmdParser')
    #@patch('udocker.container.localrepo.LocalRepository')
    #def test_25_do_version(self, mock_local, mock_cmdp):
    #    """Test UdockerCLI().do_version()."""
    #
    #
    #   mock_cmdp.get.side_effect = ["run", "", "" "", "", ]
    #   version = self.udoc.do_version(mock_cmdp)
    #   self.assertIsNotNone(version)

    @patch('udocker.msg.Msg.out')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_26_do_help(self, mock_local, mock_cmdp, mock_msgout):
        """Test UdockerCLI().do_help()."""



        mock_cmdp.get.side_effect = ["run", "help", "" "", "", ]
        self.udoc.do_help()
        self.assertTrue(mock_msgout.called)

    @patch('udocker.tools.UdockerCLITools')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_27_do_install(self, mock_local, mock_msg, mock_cmdp,
                           mock_utools):
        """Test UdockerCLI().do_install()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = self.udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called)
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = self.udoc.do_install(mock_cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(False))
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = self.udoc.do_install(mock_cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = self.udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

    @patch('udocker.engine.execmode.ExecutionMode')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.helper.keystore.KeyStore')
    @patch('udocker.docker.DockerLocalFileAPI')
    @patch('udocker.docker.DockerIoAPI')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_28_do_setup(self, mock_local, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp, mock_exec):
        """Test UdockerCLI().do_setup()."""

        mock_msg.level = 0
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = False
        status = self.udoc.do_setup(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_exec.set_mode.return_value = False
        status = self.udoc.do_setup(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_exec.set_mode.return_value = True
        status = self.udoc.do_setup(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_local.isprotected_container.return_value = True
        mock_exec.set_mode.return_value = True
        status = self.udoc.do_setup(mock_cmdp)
        self.assertEqual(status, 1)
        #

        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_local.isprotected_container.return_value = False
        mock_exec.set_mode.return_value = True
        status = self.udoc.do_setup(mock_cmdp)
        self.assertEqual(status, 1)


if __name__ == '__main__':
    main()
