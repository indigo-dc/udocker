#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""

import sys
from unittest import TestCase, main
from udocker.tools import UdockerTools
from udocker.utils.curl import CurlHeader
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


class UdockerToolsTestCase(TestCase):
    """Test UdockerTools() download and setup of tools needed by udocker."""

    def setUp(self):
        Config().getconf()
        self.local = LocalRepository()

    def tearDown(self):
        pass

    @patch('udocker.tools.GetURL')
    def test_01_init(self, mock_geturl):
        """Test01 UdockerTools() constructor."""
        Config().conf['tmpdir'] = "/tmp"
        Config().conf['tarball'] = "/tmp/xxx"
        Config().conf['installinfo'] = "/tmp/xxx"
        Config().conf['tarball_release'] = "0.0.0"
        self.local.bindir = "/bindir"
        utools = UdockerTools(self.local)
        self.assertEqual(utools.localrepo, self.local)
        self.assertTrue(mock_geturl.called)

    # def test_02__instructions(self):
    #     """Test02 UdockerTools()._instructions."""

    # def test_03__version2int(self):
    #     """Test03 UdockerTools()._version2int."""

    # def test_04__version_isok(self):
    #     """Test04 UdockerTools()._version_isok."""

    # @patch.object(UdockerTools, '_version_isequal')
    # def test_05_is_available(self, mock_version_isequal):
    #     """Test05 UdockerTools.is_available()."""
    #     mock_version_isequal.return_value = False
    #     utools = UdockerTools(self.local)
    #     status = utools.is_available()
    #     self.assertFalse(status)

    #     mock_version_isequal.return_value = True
    #     utools = UdockerTools(self.local)
    #     status = utools.is_available()
    #     self.assertTrue(status)

    @patch('udocker.tools.FileUtil.remove')
    @patch('udocker.tools.os.listdir')
    def test_06_purge(self, mock_listdir, mock_remove):
        """Test06 UdockerTools.purge()."""
        mock_listdir.return_value = []
        utools = UdockerTools(self.local)
        utools.purge()
        self.assertFalse(mock_remove.called)

        mock_listdir.return_value = ["F1", "F2"]
        utools = UdockerTools(self.local)
        utools.purge()
        self.assertTrue(mock_remove.called)

    # @patch('udocker.tools.GetURL.get')
    # @patch('udocker.tools.FileUtil')
    # def test_07__download(self, mock_futil, mock_gurl):
    #     """Test07 UdockerTools._download()."""
    #     hdr = CurlHeader()
    #     hdr.data["X-ND-HTTPSTATUS"] = "200"
    #     hdr.data["X-ND-CURLSTATUS"] = 0
    #     mock_futil.return_value.mktmp.return_value = "tmptarball"
    #     mock_gurl.get.return_value = (hdr, "")
    #     utools = UdockerTools(self.local)
    #     utools.curl = mock_gurl
    #     utools._tarball = "http://node.domain/filename.tgz"
    #     status = utools._download(utools._tarball)
    #     self.assertEqual(status, "tmptarball")

    #     hdr.data["X-ND-HTTPSTATUS"] = "400"
    #     hdr.data["X-ND-CURLSTATUS"] = 1
    #     utools = UdockerTools(self.local)
    #     status = utools._download(utools._tarball)
    #     self.assertEqual(status, "")

    # @patch('udocker.tools.os.path.realpath')
    # @patch('udocker.tools.os.path.exists')
    # @patch('udocker.tools.os.path.isfile')
    # @patch.object(UdockerTools, '_download')
    # def test_08__get_file(self, mock_downl, mock_isfile,
    #                       mock_exists, mock_rpath):
    #     """Test08 UdockerTools._get_file()."""
    #     location = ['http://node.domain/f.tgz']
    #     mock_downl.return_value = 'f.tgz'
    #     mock_isfile.return_value = True
    #     utools = UdockerTools(self.local)
    #     status = utools._get_file(location)
    #     self.assertEqual(status, ('f.tgz', 'http://node.domain/f.tgz'))

    #     location = ['/bb/c/f.tgz']
    #     mock_downl.return_value = 'f.tgz'
    #     mock_isfile.return_value = True
    #     mock_exists.return_value = True
    #     mock_rpath.return_value = '/bb/c/f.tgz'
    #     utools = UdockerTools(self.local)
    #     status = utools._get_file(location)
    #     self.assertEqual(status, ('/bb/c/f.tgz', '/bb/c/f.tgz'))

    # @patch('udocker.tools.os.path.isfile')
    # @patch('udocker.tools.Msg')
    # @patch('udocker.tools.FileUtil')
    # def test_09__verify_version(self, mock_futil,
    #                             mock_msg, mock_isfile):
    #     """Test09 UdockerTools._verify_version()."""
    #     mock_isfile.return_value = False
    #     mock_futil.return_value.mktmp.return_value = ""
    #     utools = UdockerTools(self.local)
    #     status = utools._verify_version("tarballfile")
    #     self.assertFalse(status)

    #     mock_msg.level = 0
    #     mock_msg.VER = 4
    #     mock_isfile.return_value = True
    #     utools = UdockerTools(self.local)
    #     status = utools._verify_version("tarballfile")
    #     self.assertFalse(status)

    #     mock_isfile.return_value = True
    #     utools = UdockerTools(self.local)
    #     status = utools._verify_version("tarballfile")
    #     self.assertFalse(status)

    #     mock_isfile.return_value = True
    #     utools = UdockerTools(self.local)
    #     status = utools._verify_version("tarballfile")
    #     self.assertTrue(status)

    # @patch('udocker.tools.os.path.isfile')
    # @patch.object(UdockerTools, '_verify_version')
    # @patch('udocker.tools.Msg')
    # def test_10__install(self, mock_msg,
    #                      mock_ver_version, mock_isfile):
    #     """Test10 UdockerTools._install()."""
    #     self.local.bindir = ""
    #     mock_msg.level = 0
    #     mock_ver_version.return_value = False
    #     mock_isfile.return_value = False
    #     utools = UdockerTools(self.local)
    #     status = utools._install("tarballfile")
    #     self.assertFalse(status)

    #     mock_ver_version.return_value = True
    #     mock_isfile.return_value = True
    #     utools = UdockerTools(self.local)
    #     status = utools._install("tarballfile")
    #     self.assertTrue(status)

    # def test_11__get_mirrors(self):
    #     """Test11 UdockerTools._get_mirrors()."""

    # def test_12_get_installinfo(self):
    #     """Test12 UdockerTools.get_installinfo()."""

    # def test_13__install_logic(self):
    #     """Test12 UdockerTools._install_logic()."""

    @patch('udocker.tools.FileUtil.mktmp')
    @patch('udocker.tools.os.path.isfile')
    @patch('udocker.tools.os.path.exists')
    @patch('udocker.tools.Msg')
    @patch('udocker.tools.FileUtil.remove')
    @patch('udocker.tools.GetURL')
    @patch.object(UdockerTools, '_install')
    @patch.object(UdockerTools, '_verify_version')
    @patch.object(UdockerTools, '_instructions')
    @patch.object(UdockerTools, '_download')
    @patch.object(UdockerTools, 'is_available')
    def test_14_install(self, mock_is, mock_down, mock_instr, mock_ver,
                         mock_install, mock_geturl, mock_remove,
                         mock_msg, mock_exists, mock_isfile,
                         mock_mktmp):
        """Test14 UdockerTools.install()"""
        # IS AVAILABLE NO DOWNLOAD
        self.local.topdir = "/home/user/.udocker"
        mock_msg.level = 0
        mock_mktmp.return_value = "filename_tmp"
        mock_is.return_value = True
        utools = UdockerTools(self.local)
        status = utools.install()
        self.assertTrue(status)

        # NO AUTOINSTALL
        mock_is.return_value = False
        utools = UdockerTools(self.local)
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = Config().conf['tarball_release']
        utools._autoinstall = False
        status = utools.install()
        self.assertFalse(status)

        # NO TARBALL
        # mock_is.return_value = False
        # utools = UdockerTools(self.local)
        # utools._tarball = ""
        # utools._autoinstall = True
        # status = utools.install()
        # self.assertFalse(status)

        # _download fails
        # mock_instr.reset_mock()
        # mock_is.return_value = False
        # mock_down.return_value = ""
        # utools = UdockerTools(self.local)
        # utools._tarball = "http://node.domain/filename.tgz"
        # utools._tarball_release = Config().conf['tarball_release']
        # status = utools.install()
        # self.assertTrue(mock_instr.called)
        # self.assertFalse(status)

        # _download ok _verify_version fails
        # mock_instr.reset_mock()
        # mock_is.return_value = False
        # mock_down.return_value = "filename.tgz"
        # mock_ver.return_value = False
        # mock_isfile.return_value = False
        # utools = UdockerTools(self.local)
        # utools._tarball = "http://node.domain/filename.tgz"
        # utools._tarball_release = Config().conf['tarball_release']
        # status = utools.install()
        # self.assertTrue(mock_instr.called)
        # self.assertTrue(mock_futil.return_value.remove.called)
        # self.assertFalse(status)

        # _download ok _verify_version ok install ok
        # mock_instr.reset_mock()
        # mock_is.return_value = False
        # mock_down.return_value = "filename.tgz"
        # mock_ver.return_value = True
        # mock_install.return_value = True
        # mock_isfile.return_value = True
        # utools = UdockerTools(self.local)
        # utools._tarball = "http://node.domain/filename.tgz"
        # utools._tarball_release = Config().conf['tarball_release']
        # utools._installinfo = "installinfo.txt"
        # utools._install_json = dict()
        # status = utools.install()
        # self.assertTrue(mock_install.called)
        # self.assertTrue(status)

        # # _download ok _verify_version ok install fail
        # mock_instr.reset_mock()
        # mock_is.return_value = False
        # mock_down.return_value = "filename.tgz"
        # mock_ver.return_value = True
        # mock_install.return_value = False
        # utools = UdockerTools(self.local)
        # utools._tarball = "http://node.domain/filename.tgz"
        # utools._tarball_release = Config().conf['tarball_release']
        # utools._installinfo = "installinfo.txt"
        # utools._install_json = dict()
        # status = utools.install()
        # self.assertTrue(mock_install.called)
        # self.assertTrue(mock_instr.called)
        # self.assertTrue(mock_remove.called)
        # self.assertFalse(status)

        # # file not exists no download
        # mock_instr.reset_mock()
        # mock_is.return_value = False
        # mock_exists.return_value = False
        # utools = UdockerTools(self.local)
        # utools._install_json = dict()
        # utools._tarball = "filename.tgz"
        # utools._tarball_release = Config().conf['tarball_release']
        # utools._installinfo = "installinfo.txt"
        # utools._tarball_file = ""
        # status = utools.install()
        # self.assertTrue(mock_instr.called)
        # # self.assertFalse(mock_remove.called)
        # self.assertFalse(status)


if __name__ == '__main__':
    main()
