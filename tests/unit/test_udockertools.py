#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""

import sys
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
        self.conf['tmpdir'] = "/tmp"
        self.conf['tarball'] = "/tmp/xxx"
        self.conf['installinfo'] = "/tmp/xxx"
        self.conf['tarball_release'] = "0.0.0"
        self.local.bindir = "/bindir"
        self.assertEqual(self.utools.localrepo, self.local)

    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_02__version_isequal(self, mock_getdata, mock_localrepo):
        """Test UdockerTools._version_isequal()."""
        mock_getdata.return_value = "0.0.0"
        self.utools._tarball_release = "0.0.0"
        status = self.utools._version_isequal("versionfile")
        self.assertTrue(status)
        #
        mock_getdata.return_value = "0.0.0"
        self.utools._tarball_release = "1.1.1"
        status = self.utools._version_isequal("versionfile")
        self.assertFalse(status)

    @patch('udocker.tools.UdockerTools._version_isequal')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_02_is_available(self, mock_localrepo, mock_version_isequal):
        """Test UdockerTools.is_available()."""
        mock_version_isequal.return_value = False
        status = self.utools.is_available()
        self.assertFalse(status)
        #
        mock_version_isequal.return_value = True
        status = self.utools.is_available()
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.FileUtil.mktmp')
    @patch('udocker.tools.os.path.isfile')
    @patch('udocker.tools.os.path.exists')
    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.tools.UdockerTools.__init__')
    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch('udocker.utils.curl.GetURL')
    @patch.object(UdockerTools, '_install')
    @patch.object(UdockerTools, '_verify_version')
    @patch.object(UdockerTools, '_instructions')
    @patch.object(UdockerTools, '_download')
    @patch.object(UdockerTools, 'is_available')
    def test_03__install(self, mock_is, mock_down, mock_instr, mock_ver,
                         mock_install, mock_geturl, mock_remove, mock_init,
                         mock_localrepo, mock_msg, mock_exists, mock_isfile,
                         mock_mktmp):
        """Test UdockerTools.install()"""
        mock_msg.level = 0
        mock_mktmp.return_value = "filename_tmp"
        mock_init.return_value = None
        self.utools.localrepo = mock_localrepo
        self.utools.curl = mock_geturl
        self.utools.localrepo.topdir = "/home/user/.udocker"
        CurlHeader()
        # IS AVAILABLE NO DOWNLOAD
        mock_is.return_value = True
        status = self.utools.install()
        self.assertTrue(status)
        # NO AUTOINSTALL
        mock_is.return_value = False
        self.utools._tarball = "http://node.domain/filename.tgz"
        self.utools._tarball_release = self.conf['tarball_release']
        self.utools._autoinstall = False
        status = self.utools.install()
        self.assertEqual(status, None)
        # NO TARBALL
        mock_is.return_value = False
        self.utools._tarball = ""
        self.utools._autoinstall = True
        status = self.utools.install()
        self.assertFalse(status)
        # _download fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        self.utools._tarball = "http://node.domain/filename.tgz"
        self.utools._tarball_release = self.conf['tarball_release']
        mock_down.return_value = ""
        status = self.utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(status)
        # _download ok _verify_version fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        self.utools._tarball = "http://node.domain/filename.tgz"
        self.utools._tarball_release = self.conf['tarball_release']
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = False
        mock_isfile.return_value = False
        status = self.utools.install()
        #self.assertTrue(mock_instr.called)
        #self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)
        # _download ok _verify_version ok install ok
        mock_instr.reset_mock()
        mock_is.return_value = False
        self.utools._tarball = "http://node.domain/filename.tgz"
        self.utools._tarball_release = self.conf['tarball_release']
        self.utools._installinfo = "installinfo.txt"
        self.utools._install_json = dict()
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = True
        mock_isfile.return_value = True
        status = self.utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(status)
        # _download ok _verify_version ok install fail
        mock_instr.reset_mock()
        mock_is.return_value = False
        self.utools._tarball = "http://node.domain/filename.tgz"
        self.utools._tarball_release = self.conf['tarball_release']
        self.utools._installinfo = "installinfo.txt"
        self.utools._install_json = dict()
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = False
        status = self.utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_remove.called)
        self.assertFalse(status)
        # file not exists no download
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_exists.return_value = False
        self.utools._install_json = dict()
        self.utools._tarball = "filename.tgz"
        self.utools._tarball_release = self.conf['tarball_release']
        self.utools._installinfo = "installinfo.txt"
        self.utools._tarball_file = ""
        status = self.utools.install()
        self.assertTrue(mock_instr.called)
        # self.assertFalse(mock_remove.called)
        self.assertFalse(status)

    @patch('udocker.utils.curl.GetURL')
    @patch('udocker.utils.fileutil.FileUtil.mktmp')
    @patch('udocker.tools.UdockerTools.__init__')
    def test_04__download(self, mock_init, mock_mktmp, mock_gurl):
        """Test UdockerTools.download()."""
        mock_init.return_value = None
        self.utools.curl = mock_gurl
        self.utools._tarball = "http://node.domain/filename.tgz"
        hdr = CurlHeader()
        hdr.data["X-ND-HTTPSTATUS"] = "200"
        hdr.data["X-ND-CURLSTATUS"] = 0
        mock_mktmp.return_value = "tmptarball"
        mock_gurl.get.return_value = (hdr, "")
        status = self.utools._download(self.utools._tarball)
        self.assertEqual(status, "tmptarball")
        #
        hdr.data["X-ND-HTTPSTATUS"] = "400"
        hdr.data["X-ND-CURLSTATUS"] = 1
        status = self.utools._download(self.utools._tarball)
        self.assertEqual(status, "")

    @patch('udocker.tools.os.path.isfile')
    @patch('udocker.tools.UdockerTools._version_isequal')
    @patch('udocker.msg.Msg')
    @patch('udocker.tools.subprocess.call')
    @patch('udocker.utils.fileutil.FileUtil')
    @patch('udocker.tools.UdockerTools.__init__')
    def test_04__verify_version(self, mock_init, mock_futil, mock_call,
                                mock_msg, mock_versioneq, mock_isfile):
        """Test UdockerTools._verify_version()."""
        mock_init.return_value = None
        mock_isfile.return_value = False
        mock_futil.return_value.mktmp.return_value = ""
        status = self.utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_isfile.return_value = True
        status = self.utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = False
        mock_isfile.return_value = True
        status = self.utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = True
        mock_isfile.return_value = True
        status = self.utools._verify_version("tarballfile")
        self.assertTrue(status)

    @patch('udocker.tools.os.path.isfile')
    @patch('udocker.tools.UdockerTools._install')
    @patch('udocker.tools.UdockerTools._verify_version')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.msg.Msg')
    @patch('udocker.tools.subprocess.call')
    @patch('udocker.tools.UdockerTools.__init__')
    def test_04__install(self, mock_init, mock_call, mock_msg, mock_local,
                         mock_ver_version, mock_ins, mock_isfile):
        """Test UdockerTools._install()."""
        mock_init.return_value = None
        self.utools.localrepo = mock_local
        mock_local.bindir = ""
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_ver_version.return_value = False
        mock_ins.return_value = False
        mock_isfile.return_value = False
        status = self.utools._install("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_ver_version.return_value = True
        mock_ins.return_value = True
        mock_isfile.return_value = True
        status = self.utools._install("tarballfile")
        self.assertTrue(status)

    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch('udocker.tools.os.listdir')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_05_purge(self, mock_localrepo, mock_listdir, mock_remove):
        """Test UdockerTools.purge()."""
        mock_listdir.return_value = []
        self.utools.purge()
        self.assertFalse(mock_remove.called)
        #
        mock_listdir.return_value = ["F1", "F2"]
        self.utools.purge()
        self.assertTrue(mock_remove.called)

    @patch('udocker.msg.Msg.out')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__instructions(self, mock_localrepo, mock_msgout):
        """Test UdockerTools._instructions()."""
        self.utools._instructions()
        self.assertTrue(mock_msgout.called)


if __name__ == '__main__':
    main()
