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

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
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

    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    def test_01_init(self, mock_dioapi, mock_dlocapi, mock_ks):
        """Test UdockerCLI() constructor."""

        # Test self.conf['keystore'] starts with /
        self.conf['keystore'] = "/xxx"
        udoc = UdockerCLI(self.local, self.conf)
        self.assertTrue(mock_dioapi.called)
        self.assertTrue(mock_dlocapi.called)
        self.assertTrue(mock_ks.called_with(self.conf['keystore']))
        mock_ks.reset_mock()

        # Test self.conf['keystore'] does not starts with /
        self.conf['keystore'] = "xx"
        udoc = UdockerCLI(self.local, self.conf)
        self.assertTrue(mock_ks.called_with(self.conf['keystore']))

    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_02__check_imagespec(self, mock_msg, mock_dioapi,
                                 mock_dlocapi, mock_ks):
        """Test UdockerCLI()._check_imagespec()."""

        mock_msg.level = 0
        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc._check_imagespec("")
        self.assertEqual(status, (None, None))

        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc._check_imagespec("AAA")
        self.assertEqual(status, ("AAA", "latest"))

        mock_dioapi.is_repo_name = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc._check_imagespec("AAA:45")
        self.assertEqual(status, ("AAA", "45"))

    @patch('udocker.cmdparser.CmdParser.get')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.os.path.exists')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_03_do_mkrepo(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_exists, mock_cmdp, mock_cmdget):
        """Test UdockerCLI().do_mkrepo()."""

        mock_msg.level = 0
        mock_cmdget.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdget.return_value = ""
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertEqual(status, 0)

        mock_cmdget.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertEqual(status, 1)

    def test_04__search_print_v1(self):
        """Test UdockerCLI()._search_print_v1()."""
        pass

    def test_05__search_print_v2(self):
        """Test UdockerCLI()._search_print_v2()."""
        pass

    @patch('udocker.cli.input')
    @patch('udocker.cli.UdockerCLI._search_print_v2')
    @patch('udocker.cli.UdockerCLI._search_print_v1')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_06_do_search(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_cmdp, mock_print1, mock_print2, mock_input):
        """Test UdockerCLI().do_search()."""

        mock_msg.level = 0
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.return_value = None
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(mock_cmdp)
        self.assertEqual(status, 0)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["results", ], ["repositories", ], [], ])
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_print1.called)
        self.assertTrue(mock_print2.called)

        mock_print1.reset_mock()
        mock_print2.reset_mock()
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertFalse(mock_print1.called)
        self.assertTrue(mock_print2.called)

        mock_print1.reset_mock()
        mock_print2.reset_mock()
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_input.return_value = "q"
        mock_dioapi.return_value.search_ended = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertFalse(mock_print1.called)
        self.assertFalse(mock_print2.called)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_07_do_load(self, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_load()."""

        mock_msg.level = 0
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = []
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = ["REPO", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_08_do_import(self, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_import()."""

        mock_msg.level = 0
        cmd_options = [False, False, "", False,
                       "INFILE", "IMAGE", "" "", "", ]
        mock_cmdp.get.side_effect = ["", "", "", "", "", "", "", "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()

        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("", "")
        mock_cmdp.missing_options.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()

        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "")
        mock_cmdp.missing_options.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()

        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()

        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(mock_cmdp)
        self.assertEqual(status, 0)

    def test_09_do_export(self):
        """Test UdockerCLI().do_export()."""
        pass

    def test_10_do_clone(self):
        """Test UdockerCLI().do_clone()."""
        pass

    @patch('udocker.cli.getpass')
    @patch('udocker.cli.input')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_11_do_login(self, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp,
                         mock_rinput, mock_gpass):
        """Test UdockerCLI().do_login()."""

        mock_msg.level = 0
        mock_cmdp.get.side_effect = ["user", "pass", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_login(mock_cmdp)
        self.assertEqual(status, 1)
        self.assertFalse(mock_rinput.called)
        self.assertFalse(mock_gpass.called)

        mock_rinput.reset_mock()
        mock_gpass.reset_mock()
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_login(mock_cmdp)
        self.assertEqual(status, 1)
        self.assertTrue(mock_rinput.called)
        self.assertTrue(mock_gpass.called)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_login(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_12_do_logout(self, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test UdockerCLI().do_logout()."""

        mock_msg.level = 0
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = 1
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_logout(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["ALL", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = 1
        mock_ks.return_value.erase.return_value = 0
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_logout(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_ks.return_value.erase.called)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = 0
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_logout(mock_cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_ks.return_value.delete.called)

    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_13_do_pull(self, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test UdockerCLI().do_pull()."""

        mock_msg.level = 0
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = []
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = ["F1", "F2", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(mock_cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cli.UdockerCLI._create')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_14_do_create(self, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_create):
        """Test UdockerCLI().do_create()."""

        mock_msg.level = 0
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_create(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_create(mock_cmdp)
        self.assertEqual(status, 1)

        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = "CONTAINER_ID"
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_create(mock_cmdp)
        self.assertEqual(status, 0)

    # @patch('udocker.cli.ContainerStructure')
    # @patch('udocker.cli.UdockerCLI._check_imagespec')
    # @patch('udocker.cli.DockerIoAPI.is_repo_name')
    # @patch('udocker.cli.Msg')
    # def test_15__create(self, mock_msg, mock_reponame, mock_chkimg,
    #                     mock_cstruct):
    #     """Test UdockerCLI()._create()."""
    #
    #     mock_msg.level = 0
    #     mock_reponame.return_value = 1
    #     udoc = UdockerCLI(self.local, self.conf)
    #     status = udoc._create("IMAGE:TAG")
    #     self.assertEqual(status, 1)
    #
    #     mock_reponame.return_value = 0
    #     mock_chkimg.return_value = ("", "TAG")
    #     mock_cstruct.return_value.create.return_value = True
    #     udoc = UdockerCLI(self.local, self.conf)
    #     status = udoc._create("IMAGE:TAG")
    #     self.assertEqual(status, 1)
    #
    #     mock_reponame.return_value = 0
    #     mock_chkimg.return_value = ("IMAGE", "TAG")
    #     mock_cstruct.return_value.create.return_value = True
    #     udoc = UdockerCLI(self.local, self.conf)
    #     status = udoc._create("IMAGE:TAG")
    #     self.assertEqual(status, 0)

    # TODO: need to implement the test
    # @patch('udocker.cmdparser.CmdParser')
    # def test_16__get_run_options(self, mock_cmdp):
    #    """Test UdockerCLI()._get_run_options()"""
    #
    #    udocker.engine.proot.PRootEngine = mock.MagicMock()
    #    udocker.engine.proot.PRootEngine.opt = dict()
    #    udocker.engine.proot.PRootEngine.opt["vol"] = []
    #    udocker.engine.proot.PRootEngine.opt["env"] = []
    #    mock_cmdp.get.return_value = "VALUE"
    #    self.udoc._get_run_options(mock_cmdp, udocker.engine.proot.PRootEngine)
    #    self.assertEqual(udocker.engine.proot.PRootEngine.opt["dns"], "VALUE")

    @patch('udocker.cli.UdockerCLI._get_run_options')
    @patch('udocker.engine.proot.PRootEngine')
    @patch('udocker.cmdparser.CmdParser')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    @patch('udocker.cli.os.path.realpath')
    def test_17_do_run(self, mock_realpath, mock_msg, mock_dioapi, mock_dlocapi,
                       mock_ks, mock_cmdp, mock_eng, mock_getopt):
        """Test UdockerCLI().do_run()."""

        mock_msg.level = 0
        mock_realpath.return_value = "/tmp"
        mock_cmdp.return_value.missing_options.return_value = True
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_run(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()

        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        self.conf['location'] = "/"
        mock_eng.return_value.run.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_run(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()

        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        self.conf['location'] = "/"
        mock_eng.return_value.run.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_run(mock_cmdp)
        self.assertEqual(status, 1)
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()

        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # self.conf['location'] = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = True
        # mock_del.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(mock_del.called)
        # self.assertFalse(status)
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # self.conf['location'] = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = False
        # mock_del.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(mock_cmdp)
        # # self.assertTrue(mock_del.called)
        # self.assertFalse(status)
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = ""
        # mock_eng.return_value.run.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        #
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = False
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)


if __name__ == '__main__':
    main()
