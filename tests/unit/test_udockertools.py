#!/usr/bin/env python
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

from udocker.tools import UdockerTools
from udocker.utils.curl import CurlHeader
from udocker.config import Config

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class UdockerToolsTestCase(unittest.TestCase):
    """Test UdockerTools() download and setup of tools needed by udocker."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.utils.curl.GetURL')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.config.Config')
    def test_01_init(self, mock_config, mock_localrepo, mock_geturl):
        """Test UdockerTools() constructor."""
        Config = mock_config
        Config.tmpdir = "/tmp"
        Config.tarball = "/tmp/xxx"
        Config.installinfo = "/tmp/xxx"
        Config._tarball_release = "0.0.0"
        localrepo = mock_localrepo
        localrepo.bindir = "/bindir"
        utools = UdockerTools(localrepo)
        self.assertEqual(utools.localrepo, localrepo)

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
    unittest.main()
