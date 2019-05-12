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
from udocker.cmdparser import CmdParser
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
        self.cmdp = CmdParser()

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

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cli.os.path.exists')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_03_do_mkrepo(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_exists, mock_cmdget):
        """Test UdockerCLI().do_mkrepo()."""

        mock_msg.level = 0
        mock_cmdget.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_mkrepo(self.cmdp)
        self.assertEqual(status, 1)

        mock_cmdget.return_value = ""
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_mkrepo(self.cmdp)
        self.assertEqual(status, 0)

        mock_cmdget.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_mkrepo(self.cmdp)
        self.assertEqual(status, 1)

    def test_04__search_print_v1(self):
        """Test UdockerCLI()._search_print_v1()."""
        pass

    def test_05__search_print_v2(self):
        """Test UdockerCLI()._search_print_v2()."""
        pass

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.input')
    @patch('udocker.cli.UdockerCLI._search_print_v2')
    @patch('udocker.cli.UdockerCLI._search_print_v1')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_06_do_search(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_print1, mock_print2, mock_input, mock_miss, mock_get):
        """Test UdockerCLI().do_search()."""

        mock_msg.level = 0
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = False
        mock_dioapi.return_value.search_get_page.return_value = None
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(self.cmdp)
        self.assertEqual(status, 0)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["results", ], ["repositories", ], [], ])
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_print1.called)
        self.assertTrue(mock_print2.called)

        mock_print1.reset_mock()
        mock_print2.reset_mock()
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(self.cmdp)
        self.assertEqual(status, 0)
        self.assertFalse(mock_print1.called)
        self.assertTrue(mock_print2.called)

        mock_print1.reset_mock()
        mock_print2.reset_mock()
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = False
        mock_input.return_value = "q"
        mock_dioapi.return_value.search_ended = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_search(self.cmdp)
        self.assertEqual(status, 0)
        self.assertFalse(mock_print1.called)
        self.assertFalse(mock_print2.called)

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_07_do_load(self, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_miss, mock_get):
        """Test UdockerCLI().do_load()."""

        mock_msg.level = 0
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_miss.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["INFILE", "", "" "", "", ]
        mock_miss.return_value = False
        mock_dlocapi.return_value.load.return_value = []
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["INFILE", "", "" "", "", ]
        mock_miss.return_value = False
        mock_dlocapi.return_value.load.return_value = ["REPO", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_load(self.cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_08_do_import(self, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_chkimg, mock_miss, mock_get):
        """Test UdockerCLI().do_import()."""

        mock_msg.level = 0
        cmd_options = [False, False, "", False,
                       "INFILE", "IMAGE", "" "", "", ]
        mock_get.side_effect = ["", "", "", "", "", "", "", "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = cmd_options
        mock_chkimg.return_value = ("", "")
        mock_miss.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "")
        mock_miss.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_miss.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_miss.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_import(self.cmdp)
        self.assertEqual(status, 0)

    def test_09_do_export(self):
        """Test UdockerCLI().do_export()."""
        pass

    @patch('udocker.container.localrepo.LocalRepository.get_container_id', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.Msg')
    def test_10_do_clone(self, mock_msg, mock_dlocapi, mock_get, mock_contid):
        """Test UdockerCLI().do_clone()."""

        mock_msg.level = 0
        mock_get.side_effect = ["name", "P1", "" "", "", ]
        mock_contid.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_clone(self.cmdp)
        self.assertEqual(status, 1)
        self.assertTrue(mock_msg.return_value.err.called)

        mock_get.side_effect = ["name", "P1", "" "", "", ]
        mock_contid.return_value = "1"
        mock_dlocapi.return_value.clone_container.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_clone(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_msg.return_value.out.called)
        self.assertTrue(mock_dlocapi.return_value.clone_container.called)

        mock_get.side_effect = ["name", "P1", "" "", "", ]
        mock_contid.return_value = ""
        mock_dlocapi.return_value.clone_container.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_clone(self.cmdp)
        self.assertEqual(status, 1)
        self.assertTrue(mock_msg.return_value.err.called_with("Error: cloning"))

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cli.getpass')
    @patch('udocker.cli.input')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_11_do_login(self, mock_msg, mock_dioapi, mock_dlocapi,
                         mock_ks, mock_rinput, mock_gpass, mock_get):
        """Test UdockerCLI().do_login()."""

        mock_msg.level = 0
        mock_get.side_effect = ["user", "pass", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_login(self.cmdp)
        self.assertEqual(status, 1)
        self.assertFalse(mock_rinput.called)
        self.assertFalse(mock_gpass.called)

        mock_rinput.reset_mock()
        mock_gpass.reset_mock()
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_login(self.cmdp)
        self.assertEqual(status, 1)
        self.assertTrue(mock_rinput.called)
        self.assertTrue(mock_gpass.called)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_login(self.cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_12_do_logout(self, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_get):
        """Test UdockerCLI().do_logout()."""

        mock_msg.level = 0
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = 1
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_logout(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["ALL", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = 1
        mock_ks.return_value.erase.return_value = 0
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_logout(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_ks.return_value.erase.called)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = 0
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_logout(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_ks.return_value.delete.called)

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_13_do_pull(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                        mock_chkimg, mock_miss, mock_get):
        """Test UdockerCLI().do_pull()."""

        mock_msg.level = 0
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_miss.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_miss.return_value = False
        mock_dioapi.return_value.get.return_value = []
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(self.cmdp)
        self.assertEqual(status, 1)

        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_miss.return_value = False
        mock_dioapi.return_value.get.return_value = ["F1", "F2", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_pull(self.cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._create')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_14_do_create(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_create, mock_miss, mock_get):
        """Test UdockerCLI().do_create()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_create(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_create(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = "CONTAINER_ID"
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_create(self.cmdp)
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

    # TODO: need to re-implement the test, mock execution_mode, not engine
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._get_run_options')
    @patch('udocker.engine.proot.PRootEngine')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    @patch('udocker.cli.os.path.realpath')
    def test_17_do_run(self, mock_realpath, mock_msg, mock_dioapi, mock_dlocapi,
                       mock_ks, mock_eng, mock_getopt, mock_miss, mock_get):
        """Test UdockerCLI().do_run()."""

        mock_msg.level = 0
        mock_realpath.return_value = "/tmp"
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_run(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        self.conf['location'] = "/"
        mock_eng.return_value.run.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_run(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        self.conf['location'] = "/"
        mock_eng.return_value.run.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_run(self.cmdp)
        self.assertEqual(status, 1)

        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "--rm" "", "", ]
        # self.conf['location'] = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = True
        # mock_del.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(self.cmdp)
        # self.assertFalse(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "--rm" "", "", ]
        # self.conf['location'] = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = False
        # mock_del.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(self.cmdp)
        # # self.assertTrue(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = ""
        # mock_eng.return_value.run.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(self.cmdp)
        # self.assertFalse(status)
        #
        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(self.cmdp)
        # self.assertTrue(status)
        #
        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "NAME", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(self.cmdp)
        # self.assertTrue(status)
        #
        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "NAME", ]
        # self.conf['location'] = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = False
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_run(self.cmdp)
        # self.assertFalse(status)

    @patch('udocker.container.localrepo.LocalRepository.get_layers', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.isprotected_imagerepo', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_imagerepos', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_18_do_images(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_miss, mock_get, mock_getimg, mock_isprotimg, mock_getlayers):
        """Test UdockerCLI().do_images()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_images(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_getimg.return_values = []
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_images(self.cmdp)
        self.assertEqual(status, 0)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_getimg.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_isprotimg.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_images(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_isprotimg.called)

        mock_miss.return_value = False
        mock_get.side_effect = ["LONG", "", "" "", "", ]
        mock_getimg.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_isprotimg.return_value = True
        mock_getlayers.return_value = []
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_images(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_getlayers.called)

    @patch('udocker.container.localrepo.LocalRepository.iswriteable_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.isprotected_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_containers_list', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_19_do_ps(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                      mock_miss, mock_get, mock_contlist, mock_isprotcont, mock_iswrtcont):
        """Test UdockerCLI().do_ps()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_ps(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_contlist.return_value = []
        udoc = UdockerCLI(self.local, self.conf)
        udoc.do_ps(self.cmdp)
        self.assertTrue(mock_contlist.called)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_contlist.return_value = [("ID", "NAME", ""), ]
        mock_isprotcont.return_value = True
        mock_iswrtcont.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        udoc.do_ps(self.cmdp)
        self.assertTrue(mock_isprotcont.called)

    @patch('udocker.container.localrepo.LocalRepository.isprotected_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_container_id', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_20_do_rm(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                      mock_miss, mock_get, mock_contid, mock_isprotcont):
        """Test UdockerCLI().do_rm()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rm(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rm(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["X", "12", "" "", "", ]
        mock_contid.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rm(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["X", "1", "" "", "", ]
        mock_contid.return_value = "1"
        mock_isprotcont.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rm(self.cmdp)
        self.assertEqual(status, 1)

        # TODO: fix test
        # mock_miss.return_value = False
        # mock_get.side_effect = ["X", "1", "" "", "", ]
        # mock_contid.return_value = "1"
        # mock_isprotcont.return_value = False
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_rm(self.cmdp)
        # self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.isprotected_imagerepo', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_21_do_rmi(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                       mock_chkimg, mock_miss, mock_get, mock_isprotimg):
        """Test UdockerCLI().do_rmi()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rmi(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rmi(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_isprotimg.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rmi(self.cmdp)
        self.assertEqual(status, 1)

        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "", ]
        # mock_chkimg.return_value = ("IMAGE", "TAG")
        # mock_isprotimg.return_value = False
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_rmi(self.cmdp)
        # self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.protect_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_container_id', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_22_do_protect(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                           mock_chkimg, mock_miss, mock_get, mock_contid, mock_protcont):
        """Test UdockerCLI().do_protect()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_protect(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_protcont.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_protect(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_protcont.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_protect(self.cmdp)
        self.assertEqual(status, 0)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        mock_contid.return_value = ""
        mock_protcont.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_protect(self.cmdp)
        self.assertEqual(status, 1)

        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "", ]
        # mock_chkimg.return_value = ("IMAGE", "TAG")
        # mock_contid.return_value = ""
        # mock_protcont.return_value = True
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_protect(self.cmdp)
        # self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.unprotect_imagerepo', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.unprotect_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_container_id', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_23_do_unprotect(self, mock_msg, mock_dioapi, mock_dlocapi,
                             mock_ks, mock_chkimg, mock_miss, mock_get,
                             mock_contid, mock_uprotcont, mock_uprotimg):
        """Test UdockerCLI().do_unprotect()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_unprotect(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_uprotcont.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_unprotect(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_uprotcont.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_unprotect(self.cmdp)
        self.assertEqual(status, 0)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = ""
        mock_uprotimg.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_unprotect(self.cmdp)
        self.assertEqual(status, 0)
        self.assertTrue(mock_uprotimg.called)

    @patch('udocker.container.localrepo.LocalRepository.set_container_name', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.get_container_id', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_24_do_name(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                        mock_chkimg, mock_miss, mock_get, mock_contid,
                        mock_setcont):
        """Test UdockerCLI().do_name()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_name(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = ""
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_name(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_setcont.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_name(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_contid.return_value = "123"
        mock_setcont.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_name(self.cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.del_container_name', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_25_do_rmname(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                          mock_chkimg, mock_miss, mock_get, mock_delcontname):
        """Test UdockerCLI().do_rmname()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rmname(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_delcontname.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rmname(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_delcontname.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_rmname(self.cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.get_container_id', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.ContainerStructure')
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.ContainerStructure.get_container_attr')
    @patch('udocker.cli.Msg')
    def test_26_do_inspect(self, mock_msg, mock_contattr, mock_dlocapi,
                           mock_ks, mock_chkimg, mock_cstruct, mock_miss,
                           mock_get, mock_contid):
        """Test UdockerCLI().do_inspect()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_inspect(self.cmdp)
        self.assertEqual(status, 1)

        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "", ]
        # mock_chkimg.return_value = ("IMAGE", "TAG")
        # mock_contid.return_value = "123"
        # mock_contattr.return_value = ("", "")
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_inspect(self.cmdp)
        # self.assertEqual(status, 1)

        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "PRINT", "" "", "", ]
        # mock_chkimg.return_value = ("IMAGE", "TAG")
        # mock_contid.return_value = "123"
        # mock_contattr.return_value = ("DIR", "")
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_inspect(self.cmdp)
        # self.assertEqual(status, 0)

        # mock_miss.return_value = False
        # mock_get.side_effect = ["", "", "" "", "", ]
        # mock_chkimg.return_value = ("IMAGE", "TAG")
        # mock_contid.return_value = "123"
        # mock_contattr.return_value = ("", "JSON")
        # udoc = UdockerCLI(self.local, self.conf)
        # status = udoc.do_inspect(self.cmdp)
        # self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.verify_image', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.cd_imagerepo', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerCLI._check_imagespec')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_27_do_verify(self, mock_msg, mock_dioapi, mock_dlocapi,
                          mock_ks, mock_chkimg, mock_miss, mock_get,
                          mock_cdimgrepo, mock_verifyimg):
        """Test UdockerCLI().do_verify()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_verify(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "")
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_verify(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cdimgrepo.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_verify(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = False
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cdimgrepo.return_value = True
        mock_verifyimg.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_verify(self.cmdp)
        self.assertEqual(status, 0)

    @patch('udocker.container.localrepo.LocalRepository.isprotected_container', autospec=True)
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.ExecutionMode')
    @patch('udocker.cli.KeyStore')
    @patch('udocker.cli.DockerLocalFileAPI')
    @patch('udocker.cli.DockerIoAPI')
    @patch('udocker.cli.Msg')
    def test_28_do_setup(self, mock_msg, mock_dioapi, mock_dlocapi, mock_ks,
                         mock_exec, mock_miss, mock_get, mock_cdcont,
                         mock_isprotcont):
        """Test UdockerCLI().do_setup()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_cdcont.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_setup(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_cdcont.return_value = True
        mock_exec.set_mode.return_value = False
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_setup(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        mock_cdcont.return_value = True
        mock_exec.set_mode.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_setup(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = True
        mock_get.side_effect = ["", "P1", "" "", "", ]
        mock_cdcont.return_value = True
        mock_isprotcont.return_value = True
        mock_exec.set_mode.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_setup(self.cmdp)
        self.assertEqual(status, 1)

        mock_miss.return_value = True
        mock_get.side_effect = ["", "P1", "" "", "", ]
        mock_cdcont.return_value = True
        mock_isprotcont.return_value = False
        mock_exec.set_mode.return_value = True
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_setup(self.cmdp)
        self.assertEqual(status, 1)

    @patch('udocker.cmdparser.CmdParser.get', autospec=True)
    @patch('udocker.cmdparser.CmdParser.missing_options', autospec=True)
    @patch('udocker.cli.UdockerTools')
    @patch('udocker.cli.Msg')
    def test_29_do_install(self, mock_msg, mock_utools, mock_miss, mock_get):
        """Test UdockerCLI().do_install()."""

        mock_msg.level = 0
        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_install(self.cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called)

        mock_miss.return_value = True
        mock_get.side_effect = ["", "--purge", "" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_install(self.cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(False))

        mock_miss.return_value = True
        mock_get.side_effect = ["", "--purge", "--force" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_install(self.cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

        mock_miss.return_value = True
        mock_get.side_effect = ["", "", "--force" "", "", ]
        udoc = UdockerCLI(self.local, self.conf)
        status = udoc.do_install(self.cmdp)
        # self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

    @patch('udocker.cli.Msg')
    def test_30_do_listconf(self, mock_msg):
        """Test UdockerCLI().do_listconf()."""
        udoc = UdockerCLI(self.local, self.conf)
        udoc.do_help()
        self.assertTrue(mock_msg.return_value.out.called)

    def test_31_do_version(self):
        """Test UdockerCLI().do_version()."""
        udoc = UdockerCLI(self.local, self.conf)
        version = udoc.do_version()
        self.assertIsNotNone(version)

    @patch('udocker.cli.Msg')
    def test_32_do_help(self, mock_msg):
        """Test UdockerCLI().do_help()."""
        udoc = UdockerCLI(self.local, self.conf)
        udoc.do_help()
        self.assertTrue(mock_msg.return_value.out.called)


if __name__ == '__main__':
    main()
