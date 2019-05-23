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

    def tearDown(self):
        pass

    @patch('udocker.tools.GetURL')
    def test_01_init(self, mock_geturl):
        """Test UdockerTools() constructor."""
        self.conf['tmpdir'] = "/tmp"
        self.conf['tarball'] = "/tmp/xxx"
        self.conf['installinfo'] = "/tmp/xxx"
        self.conf['tarball_release'] = "0.0.0"
        self.local.bindir = "/bindir"
        utools = UdockerTools(self.local, self.conf)
        self.assertEqual(utools.localrepo, self.local)
        self.assertTrue(mock_geturl.called)

    @patch('udocker.tools.FileUtil.getdata')
    def test_02__version_isequal(self, mock_getdata):
        """Test UdockerTools._version_isequal()."""
        mock_getdata.return_value = "0.0.0"
        self.conf['tarball_release'] = "0.0.0"
        utools = UdockerTools(self.local, self.conf)
        status = utools._version_isequal("versionfile")
        self.assertTrue(status)

        mock_getdata.return_value = "0.0.0"
        self.conf['tarball_release'] = "1.1.1"
        utools = UdockerTools(self.local, self.conf)
        status = utools._version_isequal("versionfile")
        self.assertFalse(status)

    @patch.object(UdockerTools, '_version_isequal')
    def test_03_is_available(self, mock_version_isequal):
        """Test UdockerTools.is_available()."""
        mock_version_isequal.return_value = False
        utools = UdockerTools(self.local, self.conf)
        status = utools.is_available()
        self.assertFalse(status)

        mock_version_isequal.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools.is_available()
        self.assertTrue(status)

    @patch('udocker.tools.GetURL.get')
    @patch('udocker.tools.FileUtil')
    def test_04__download(self, mock_futil, mock_gurl):
        """Test UdockerTools.download()."""
        utools = UdockerTools(self.local, self.conf)
        utools.curl = mock_gurl
        utools._tarball = "http://node.domain/filename.tgz"
        hdr = CurlHeader()
        hdr.data["X-ND-HTTPSTATUS"] = "200"
        hdr.data["X-ND-CURLSTATUS"] = 0
        mock_futil.return_value.mktmp.return_value = "tmptarball"
        mock_gurl.get.return_value = (hdr, "")
        status = utools._download(utools._tarball)
        self.assertEqual(status, "tmptarball")

        hdr.data["X-ND-HTTPSTATUS"] = "400"
        hdr.data["X-ND-CURLSTATUS"] = 1
        status = utools._download(utools._tarball)
        self.assertEqual(status, "")

    @patch('udocker.tools.os.path.realpath')
    @patch('udocker.tools.os.path.exists')
    @patch('udocker.tools.os.path.isfile')
    @patch.object(UdockerTools, '_download')
    def test_05__get_file(self, mock_downl, mock_isfile,
                          mock_exists, mock_rpath):
        """Test UdockerTools._get_file()."""
        location = ['http://node.domain/f.tgz']
        mock_downl.return_value = 'f.tgz'
        mock_isfile.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools._get_file(location)
        self.assertEqual(status, ('f.tgz', 'http://node.domain/f.tgz'))

        location = ['/bb/c/f.tgz']
        mock_downl.return_value = 'f.tgz'
        mock_isfile.return_value = True
        mock_exists.return_value = True
        mock_rpath.return_value = '/bb/c/f.tgz'
        utools = UdockerTools(self.local, self.conf)
        status = utools._get_file(location)
        self.assertEqual(status, ('/bb/c/f.tgz', '/bb/c/f.tgz'))

    @patch('udocker.tools.os.path.isfile')
    @patch('udocker.tools.UdockerTools._version_isequal')
    @patch('udocker.tools.Msg')
    @patch('udocker.tools.subprocess.call')
    @patch('udocker.tools.FileUtil')
    def test_06__verify_version(self, mock_futil, mock_call,
                                mock_msg, mock_versioneq, mock_isfile):
        """Test UdockerTools._verify_version()."""
        mock_isfile.return_value = False
        mock_futil.return_value.mktmp.return_value = ""
        utools = UdockerTools(self.local, self.conf)
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)

        mock_msg.level = 0
        mock_call.return_value = 1
        mock_isfile.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)

        mock_call.return_value = 0
        mock_versioneq.return_value = False
        mock_isfile.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)

        mock_call.return_value = 0
        mock_versioneq.return_value = True
        mock_isfile.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools._verify_version("tarballfile")
        self.assertTrue(status)

    @patch('udocker.tools.FileUtil.remove')
    @patch('udocker.tools.os.listdir')
    def test_07_purge(self, mock_listdir, mock_remove):
        """Test UdockerTools.purge()."""
        mock_listdir.return_value = []
        utools = UdockerTools(self.local, self.conf)
        utools.purge()
        self.assertFalse(mock_remove.called)

        mock_listdir.return_value = ["F1", "F2"]
        utools = UdockerTools(self.local, self.conf)
        utools.purge()
        self.assertTrue(mock_remove.called)

    @patch('udocker.tools.os.path.isfile')
    @patch.object(UdockerTools, '_install')
    @patch.object(UdockerTools, '_verify_version')
    @patch('udocker.tools.Msg')
    @patch('udocker.tools.subprocess.call')
    def test_08__install(self, mock_call, mock_msg,
                         mock_ver_version, mock_ins, mock_isfile):
        """Test UdockerTools._install()."""
        self.local.bindir = ""
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_ver_version.return_value = False
        mock_ins.return_value = False
        mock_isfile.return_value = False
        utools = UdockerTools(self.local, self.conf)
        status = utools._install("tarballfile")
        self.assertFalse(status)

        mock_call.return_value = 0
        mock_ver_version.return_value = True
        mock_ins.return_value = True
        mock_isfile.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools._install("tarballfile")
        self.assertTrue(status)

    @patch('udocker.tools.Msg.out')
    def test_09__instructions(self, mock_msgout):
        """Test UdockerTools._instructions()."""
        utools = UdockerTools(self.local, self.conf)
        utools._instructions()
        self.assertTrue(mock_msgout.called)

    def test_10__get_mirrors(self):
        """Test UdockerTools._get_mirrors()."""
        pass

    def test_11_get_installinfo(self):
        """Test UdockerTools.get_installinfo()."""
        pass

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
    def test_12_install(self, mock_is, mock_down, mock_instr, mock_ver,
                         mock_install, mock_geturl, mock_remove,
                         mock_msg, mock_exists, mock_isfile,
                         mock_mktmp):
        """Test UdockerTools.install()"""
        # IS AVAILABLE NO DOWNLOAD
        self.local.topdir = "/home/user/.udocker"
        mock_msg.level = 0
        mock_mktmp.return_value = "filename_tmp"
        mock_is.return_value = True
        utools = UdockerTools(self.local, self.conf)
        status = utools.install()
        self.assertTrue(status)

        # NO AUTOINSTALL
        mock_is.return_value = False
        utools = UdockerTools(self.local, self.conf)
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = self.conf['tarball_release']
        utools._autoinstall = False
        status = utools.install()
        self.assertEqual(status, None)

        # NO TARBALL
        mock_is.return_value = False
        utools = UdockerTools(self.local, self.conf)
        utools._tarball = ""
        utools._autoinstall = True
        status = utools.install()
        self.assertFalse(status)

        # _download fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_down.return_value = ""
        utools = UdockerTools(self.local, self.conf)
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = self.conf['tarball_release']
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(status)

        # _download ok _verify_version fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = False
        mock_isfile.return_value = False
        utools = UdockerTools(self.local, self.conf)
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = self.conf['tarball_release']
        status = utools.install()
        #self.assertTrue(mock_instr.called)
        #self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)

        # _download ok _verify_version ok install ok
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = True
        mock_isfile.return_value = True
        utools = UdockerTools(self.local, self.conf)
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = self.conf['tarball_release']
        utools._installinfo = "installinfo.txt"
        utools._install_json = dict()
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(status)

        # _download ok _verify_version ok install fail
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = False
        utools = UdockerTools(self.local, self.conf)
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = self.conf['tarball_release']
        utools._installinfo = "installinfo.txt"
        utools._install_json = dict()
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_remove.called)
        self.assertFalse(status)

        # file not exists no download
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_exists.return_value = False
        utools = UdockerTools(self.local, self.conf)
        utools._install_json = dict()
        utools._tarball = "filename.tgz"
        utools._tarball_release = self.conf['tarball_release']
        utools._installinfo = "installinfo.txt"
        utools._tarball_file = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        # self.assertFalse(mock_remove.called)
        self.assertFalse(status)


if __name__ == '__main__':
    main()
