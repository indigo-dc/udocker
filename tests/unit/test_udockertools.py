#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""

import sys
import os
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.tools import UdockerTools
from udocker.utils.curl import CurlHeader
from udocker.config import Config
from udocker.container.localrepo import LocalRepository

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
        self.conf = Config().getconf()
        self.local = LocalRepository(self.conf)
        self.utools = UdockerTools(self.local, self.conf)

    def tearDown(self):
        pass

    @patch('udocker.utils.curl.GetURL')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_localrepo, mock_geturl):
        """Test UdockerTools() constructor."""
        self.conf.tmpdir = "/tmp"
        self.conf.tarball = "/tmp/xxx"
        self.conf.installinfo = "/tmp/xxx"
        self.conf._tarball_release = "0.0.0"
        self.local.bindir = "/bindir"
        self.assertEqual(self.utools.localrepo, self.local)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_02__version_isequal(self, mock_getdata, mock_localrepo):
        """Test UdockerTools._version_isequal()."""
        mock_getdata.return_value = "0.0.0"
        utools = UdockerTools(mock_localrepo)
        utools._tarball_release = "0.0.0"
        status = utools._version_isequal("versionfile")
        self.assertTrue(status)
        #
        mock_getdata.return_value = "0.0.0"
        utools = UdockerTools(mock_localrepo)
        utools._tarball_release = "1.1.1"
        status = utools._version_isequal("versionfile")
        self.assertFalse(status)

    @mock.patch('udocker.tools.UdockerTools._version_isequal')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02_is_available(self, mock_localrepo, mock_version_isequal):
        """Test UdockerTools.is_available()."""
        mock_version_isequal.return_value = False
        utools = UdockerTools(mock_localrepo)
        status = utools.is_available()
        self.assertFalse(status)
        #
        mock_version_isequal.return_value = True
        utools = UdockerTools(mock_localrepo)
        status = utools.is_available()
        self.assertTrue(status)

    @mock.patch('udocker.utils.fileutil.FileUtil.mktmp')
    @mock.patch('os.path.isfile')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.tools.UdockerTools.__init__')
    @mock.patch('udocker.utils.fileutil.FileUtil.remove')
    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch.object(UdockerTools, '_install')
    @mock.patch.object(UdockerTools, '_verify_version')
    @mock.patch.object(UdockerTools, '_instructions')
    @mock.patch.object(UdockerTools, '_download')
    @mock.patch.object(UdockerTools, 'is_available')
    def test_03__install(self, mock_is, mock_down, mock_instr, mock_ver,
                         mock_install, mock_geturl, mock_remove, mock_init,
                         mock_localrepo, mock_msg, mock_exists, mock_isfile,
                         mock_mktmp):
        """Test UdockerTools.install()"""
        mock_msg.level = 0
        mock_mktmp.return_value = "filename_tmp"
        mock_init.return_value = None
        utools = UdockerTools(mock_localrepo)
        utools.localrepo = mock_localrepo
        utools.curl = mock_geturl
        utools.localrepo.topdir = "/home/user/.udocker"
        CurlHeader()
        # IS AVAILABLE NO DOWNLOAD
        mock_is.return_value = True
        status = utools.install()
        self.assertTrue(status)
        # NO AUTOINSTALL
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = Config.tarball_release
        utools._autoinstall = False
        status = utools.install()
        self.assertEqual(status, None)
        # NO TARBALL
        mock_is.return_value = False
        utools._tarball = ""
        utools._autoinstall = True
        status = utools.install()
        self.assertFalse(status)
        # _download fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = Config.tarball_release
        mock_down.return_value = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(status)
        # _download ok _verify_version fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = Config.tarball_release
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = False
        mock_isfile.return_value = False
        status = utools.install()
        #self.assertTrue(mock_instr.called)
        #self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)
        # _download ok _verify_version ok install ok
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = Config.tarball_release
        utools._installinfo = "installinfo.txt"
        utools._install_json = dict()
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = True
        mock_isfile.return_value = True
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(status)
        # _download ok _verify_version ok install fail
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = Config.tarball_release
        utools._installinfo = "installinfo.txt"
        utools._install_json = dict()
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = False
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_remove.called)
        self.assertFalse(status)
        # file not exists no download
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_exists.return_value = False
        utools._install_json = dict()
        utools._tarball = "filename.tgz"
        utools._tarball_release = Config.tarball_release
        utools._installinfo = "installinfo.txt"
        utools._tarball_file = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(mock_remove.called)
        self.assertFalse(status)

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.utils.fileutil.FileUtil.mktmp')
    @mock.patch('udocker.tools.UdockerTools.__init__')
    def test_04__download(self, mock_init, mock_mktmp, mock_gurl):
        """Test UdockerTools.download()."""
        mock_init.return_value = None
        utools = UdockerTools(None)
        utools.curl = mock_gurl
        utools._tarball = "http://node.domain/filename.tgz"
        hdr = CurlHeader()
        hdr.data["X-ND-HTTPSTATUS"] = "200"
        hdr.data["X-ND-CURLSTATUS"] = 0
        mock_mktmp.return_value = "tmptarball"
        mock_gurl.get.return_value = (hdr, "")
        status = utools._download(utools._tarball)
        self.assertEqual(status, "tmptarball")
        #
        hdr.data["X-ND-HTTPSTATUS"] = "400"
        hdr.data["X-ND-CURLSTATUS"] = 1
        status = utools._download(utools._tarball)
        self.assertEqual(status, "")

    @mock.patch('os.path.isfile')
    @mock.patch('udocker.tools.UdockerTools._version_isequal')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('subprocess.call')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.tools.UdockerTools.__init__')
    def test_04__verify_version(self, mock_init, mock_futil, mock_call,
                                mock_msg, mock_versioneq, mock_isfile):
        """Test UdockerTools._verify_version()."""
        mock_init.return_value = None
        mock_isfile.return_value = False
        utools = UdockerTools(None)
        mock_futil.return_value.mktmp.return_value = ""
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = False
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = True
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertTrue(status)

    @mock.patch('os.path.isfile')
    @mock.patch('udocker.tools.UdockerTools._install')
    @mock.patch('udocker.tools.UdockerTools._verify_version')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('subprocess.call')
    @mock.patch('udocker.tools.UdockerTools.__init__')
    def test_04__install(self, mock_init, mock_call, mock_msg, mock_local,
                         mock_ver_version, mock_ins, mock_isfile):
        """Test UdockerTools._install()."""
        mock_init.return_value = None
        utools = UdockerTools(None)
        utools.localrepo = mock_local
        mock_local.bindir = ""
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_ver_version.return_value = False
        mock_ins.return_value = False
        mock_isfile.return_value = False
        status = utools._install("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_ver_version.return_value = True
        mock_ins.return_value = True
        mock_isfile.return_value = True
        status = utools._install("tarballfile")
        self.assertTrue(status)

    @mock.patch('udocker.utils.fileutil.FileUtil.remove')
    @mock.patch('os.listdir')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05_purge(self, mock_localrepo, mock_listdir, mock_remove):
        """Test UdockerTools.purge()."""
        mock_listdir.return_value = []
        utools = UdockerTools(mock_localrepo)
        utools.purge()
        self.assertFalse(mock_remove.called)
        #
        mock_listdir.return_value = ["F1", "F2"]
        utools = UdockerTools(mock_localrepo)
        utools.purge()
        self.assertTrue(mock_remove.called)

    @mock.patch('udocker.msg.Msg.out')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__instructions(self, mock_localrepo, mock_msgout):
        """Test UdockerTools._instructions()."""
        utools = UdockerTools(mock_localrepo)
        utools._instructions()
        self.assertTrue(mock_msgout.called)


if __name__ == '__main__':
    main()
