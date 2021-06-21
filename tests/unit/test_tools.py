#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""

import tarfile
from tarfile import TarInfo
from unittest import TestCase, main
from unittest.mock import Mock, patch
from io import StringIO
from udocker.config import Config
from udocker.utils.curl import CurlHeader
from udocker.tools import UdockerTools

BUILTINS = "builtins"
BOPEN = BUILTINS + '.open'


class UdockerToolsTestCase(TestCase):
    """Test UdockerTools()."""

    def setUp(self):
        Config().getconf()
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    @patch('udocker.tools.GetURL')
    def test_01_init(self, mock_geturl):
        """Test01 UdockerTools() constructor."""
        mock_geturl.return_value = None
        utools = UdockerTools(self.local)
        self.assertTrue(mock_geturl.called)
        self.assertEqual(utools.localrepo, self.local)

    @patch('udocker.tools.Msg')
    def test_02__instructions(self, mock_msg):
        """Test02 UdockerTools()._instructions()."""
        utools = UdockerTools(self.local)
        utools._instructions()
        self.assertTrue(mock_msg.return_value.out.call_count, 2)

    def test_03__version2int(self):
        """Test03 UdockerTools()._version2int()."""
        utools = UdockerTools(self.local)
        status = utools._version2int("2.4")
        self.assertEqual(status, 2004000)

    def test_04__version_isok(self):
        """Test04 UdockerTools()._version_isok()."""
        Config.conf['tarball_release'] = "1.3"
        utools = UdockerTools(self.local)
        status = utools._version_isok("2.4")
        self.assertTrue(status)

        Config.conf['tarball_release'] = "2.3"
        utools = UdockerTools(self.local)
        status = utools._version_isok("1.4")
        self.assertFalse(status)

    @patch('udocker.tools.FileUtil.getdata')
    def test_05_is_available(self, mock_fuget):
        """Test05 UdockerTools().is_available()."""
        Config.conf['tarball_release'] = "2.3"
        mock_fuget.return_value = "2.3\n"
        utools = UdockerTools(self.local)
        status = utools.is_available()
        self.assertTrue(status)

    @patch('udocker.tools.FileUtil.remove')
    @patch('udocker.tools.FileUtil.register_prefix')
    @patch('udocker.tools.os.listdir')
    def test_06_purge(self, mock_lsdir, mock_fureg, mock_furm):
        """Test06 UdockerTools().purge()."""
        mock_lsdir.side_effect = [["f1", "f2"],
                                  ["f3", "f4"],
                                  ["f5", "f6"]]
        mock_fureg.side_effect = [None, None, None, None, None, None]
        mock_furm.side_effect = [None, None, None, None, None, None]
        utools = UdockerTools(self.local)
        utools.purge()
        self.assertTrue(mock_lsdir.call_count, 3)
        self.assertTrue(mock_fureg.call_count, 4)
        self.assertTrue(mock_furm.call_count, 4)

    @patch('udocker.tools.GetURL.get')
    @patch('udocker.tools.FileUtil.remove')
    @patch('udocker.tools.FileUtil.mktmp')
    def test_07__download(self, mock_fumktmp, mock_furm, mock_geturl):
        """Test07 UdockerTools()._download()."""
        url = "https://down/file"
        hdr = CurlHeader()
        hdr.data["X-ND-HTTPSTATUS"] = "HTTP/1.1 200 OK"
        mock_fumktmp.return_value = "/tmp/tmpf"
        mock_furm.return_value = None
        mock_geturl.return_value = (hdr, "content type...")
        utools = UdockerTools(self.local)
        status = utools._download(url)
        self.assertTrue(mock_fumktmp.called)
        self.assertEqual(status, "/tmp/tmpf")

        url = "https://down/file"
        hdr = CurlHeader()
        hdr.data["X-ND-HTTPSTATUS"] = "HTTP/1.1 401 FAIL"
        mock_fumktmp.return_value = "/tmp/tmpf"
        mock_furm.return_value = None
        mock_geturl.return_value = (hdr, "content type...")
        utools = UdockerTools(self.local)
        status = utools._download(url)
        self.assertTrue(mock_furm.called)
        self.assertEqual(status, "")

    @patch('udocker.tools.os.path.isfile')
    @patch('udocker.tools.os.path.realpath')
    @patch('udocker.tools.os.path.exists')
    @patch.object(UdockerTools, '_download')
    def test_08__get_file(self, mock_downl, mock_exists, mock_rpath,
                          mock_isfile):
        """Test08 UdockerTools()._get_file()."""
        url = ""
        mock_downl.return_value = ""
        mock_exists.return_value = False
        mock_isfile.return_value = False
        utools = UdockerTools(self.local)
        status = utools._get_file(url)
        self.assertFalse(mock_downl.called)
        self.assertTrue(mock_exists.called)
        self.assertEqual(status, "")

        url = "https://down/file"
        mock_downl.return_value = "/tmp/file"
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_rpath.return_value = "/tmp/file"
        utools = UdockerTools(self.local)
        status = utools._get_file(url)
        self.assertTrue(mock_downl.called)
        self.assertTrue(mock_exists.called)
        self.assertTrue(mock_isfile.called)
        self.assertEqual(status, "/tmp/file")

    @patch.object(UdockerTools, '_version_isok')
    @patch('udocker.tools.FileUtil.remove')
    @patch('udocker.tools.FileUtil.getdata')
    @patch('udocker.tools.os.path.basename')
    @patch('udocker.tools.FileUtil.mktmpdir')
    @patch('udocker.tools.os.path.isfile')
    def test_09__verify_version(self, mock_isfile, mock_fumktmp,
                                mock_osbase, mock_fugetdata,
                                mock_furm, mock_versionok):
        """Test09 UdockerTools()._verify_version()."""
        tball = "/home/udocker.tar"
        mock_isfile.return_value = False
        utools = UdockerTools(self.local)
        status = utools._verify_version(tball)
        self.assertTrue(mock_isfile.called)
        self.assertEqual(status, (False, ""))

        tball = "/home/udocker.tar"
        mock_isfile.return_value = True
        mock_fumktmp.return_value = ""
        utools = UdockerTools(self.local)
        status = utools._verify_version(tball)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_fumktmp.called)
        self.assertEqual(status, (False, ""))

        tball = "/home/udocker.tar"
        tinfo1 = TarInfo("udocker_dir/lib/VERSION")
        tinfo2 = TarInfo("a")
        mock_isfile.return_value = True
        mock_fumktmp.return_value = "/home/tmp"
        mock_osbase.return_value = "VERSION"
        mock_fugetdata.return_value = "1.2.7"
        mock_furm.return_value = None
        mock_versionok.return_value = True
        with patch.object(tarfile, 'open', autospec=True) as open_mock:
            open_mock.return_value.getmembers.return_value = [tinfo2, tinfo1]
            open_mock.return_value.extract.return_value = None
            utools = UdockerTools(self.local)
            status = utools._verify_version(tball)
            self.assertEqual(status, (True, "1.2.7"))
            self.assertTrue(mock_furm.called)

    @patch('udocker.tools.os.path.basename')
    @patch('udocker.tools.FileUtil')
    @patch('udocker.tools.os.path.isfile')
    def test_10__install(self, mock_isfile, mock_futil,
                         mock_osbase):
        """Test10 UdockerTools()._install()."""
        tfile = ""
        mock_isfile.return_value = False
        utools = UdockerTools(self.local)
        status = utools._install(tfile)
        self.assertFalse(status)

        tinfo1 = TarInfo("udocker_dir/bin/ls")
        tinfo2 = TarInfo("udocker_dir/lib/lib1")
        tfile = "udocker.tar"
        mock_isfile.return_value = True
        mock_futil.return_value.chmod.return_value = None
        mock_futil.return_value.rchmod.side_effect = [None, None, None,
                                                      None, None, None]
        mock_osbase.side_effect = ["ls", "ls", "lib1", "lib1", "doc", "doc1"]
        self.local.create_repo.return_value = None
        with patch.object(tarfile, 'open', autospec=True) as open_mock:
            open_mock.return_value.getmembers.side_effect = [[tinfo1, tinfo2],
                                                             [tinfo1, tinfo2],
                                                             [tinfo1, tinfo2]]
            open_mock.return_value.extract.side_effect = [None, None]
            utools = UdockerTools(self.local)
            status = utools._install(tfile)
            self.assertTrue(status)
            self.assertTrue(mock_futil.called)
            self.assertTrue(mock_futil.return_value.rchmod.call_count, 4)

    def test_11__get_mirrors(self):
        """Test11 UdockerTools()._get_mirrors()."""
        mirrors = "https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz"
        utools = UdockerTools(self.local)
        status = utools._get_mirrors(mirrors)
        self.assertEqual(status, [mirrors])

    @patch.object(UdockerTools, '_get_file')
    @patch.object(UdockerTools, '_get_mirrors')
    @patch('udocker.tools.json.load')
    def test_12_get_installinfo(self, mock_jload, mock_mirr, mock_getf):
        """Test12 UdockerTools().get_installinfo()."""
        Config.conf['installinfo'] = "/home/info.json"
        res = {"tarversion": "1.2.7"}
        mock_jload.return_value = {"tarversion": "1.2.7"}
        mock_mirr.return_value = ["/home/info.json"]
        mock_getf.return_value = "info.json"
        subuid_line = StringIO('{"tarversion": "1.2.7"}')
        with patch(BOPEN) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(subuid_line.readline, ''))
            utools = UdockerTools(self.local)
            status = utools.get_installinfo()
            self.assertEqual(status, res)

    @patch.object(UdockerTools, '_install')
    @patch.object(UdockerTools, '_verify_version')
    @patch.object(UdockerTools, '_get_file')
    @patch.object(UdockerTools, '_get_mirrors')
    @patch('udocker.tools.FileUtil.remove')
    def test_13__install_logic(self, mock_furm, mock_getmirr, mock_getfile,
                               mock_verversion, mock_install):
        """Test13 UdockerTools()._install_logic()."""
        mock_furm.return_value = None
        mock_getmirr.return_value = "https://down.pt/udocker-1.2.7.tar.gz"
        mock_getfile.return_value = "udocker-1.2.7.tar.gz"
        mock_verversion.return_value = (True, "1.2.7")
        mock_install.return_value = True
        utools = UdockerTools(self.local)
        status = utools._install_logic(False)
        self.assertTrue(status)
        self.assertTrue(mock_getmirr.called)
        self.assertTrue(mock_getfile.called)
        self.assertTrue(mock_verversion.called)
        self.assertTrue(mock_install.called)

        mock_furm.return_value = None
        mock_getmirr.return_value = "https://down.pt/udocker-1.2.7.tar.gz"
        mock_getfile.return_value = "udocker-1.2.7.tar.gz"
        mock_verversion.return_value = (False, "")
        mock_install.return_value = True
        utools = UdockerTools(self.local)
        status = utools._install_logic(True)
        self.assertTrue(status)

        mock_furm.return_value = None
        mock_getmirr.return_value = "https://down.pt/udocker-1.2.7.tar.gz"
        mock_getfile.return_value = "udocker-1.2.7.tar.gz"
        mock_verversion.return_value = (False, "")
        mock_install.return_value = True
        utools = UdockerTools(self.local)
        status = utools._install_logic(False)
        self.assertFalse(status)

    @patch('udocker.tools.Msg')
    @patch.object(UdockerTools, 'get_installinfo')
    @patch.object(UdockerTools, '_install_logic')
    @patch.object(UdockerTools, 'is_available')
    def test_14_install(self, mock_isavail, mock_instlog,
                        mock_getinfo, mock_msg):
        """Test14 UdockerTools().install()."""
        mock_msg.level = 0
        Config.conf['autoinstall'] = True
        Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
        Config.conf['tarball_release'] = "1.2.7"
        Config.conf['installretry'] = 2
        mock_isavail.return_value = True
        utools = UdockerTools(self.local)
        status = utools.install(False)
        self.assertTrue(status)
        self.assertTrue(mock_isavail.called)

        Config.conf['autoinstall'] = False
        Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
        Config.conf['tarball_release'] = "1.2.7"
        Config.conf['installretry'] = 2
        mock_isavail.return_value = False
        utools = UdockerTools(self.local)
        status = utools.install(False)
        self.assertEqual(status, None)
        self.assertFalse(utools._autoinstall)

        Config.conf['autoinstall'] = False
        Config.conf['tarball'] = ""
        Config.conf['tarball_release'] = "1.2.7"
        Config.conf['installretry'] = 2
        mock_isavail.return_value = True
        utools = UdockerTools(self.local)
        status = utools.install(False)
        self.assertTrue(status)
        self.assertEqual(utools._tarball, "")

        Config.conf['autoinstall'] = True
        Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
        Config.conf['tarball_release'] = "1.2.7"
        Config.conf['installretry'] = 2
        mock_isavail.return_value = False
        mock_instlog.side_effect = [False, True]
        mock_getinfo.side_effect = [None, None]
        utools = UdockerTools(self.local)
        status = utools.install(False)
        self.assertTrue(status)
        self.assertTrue(mock_instlog.call_count, 2)
        self.assertTrue(mock_getinfo.call_count, 2)

        Config.conf['autoinstall'] = True
        Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
        Config.conf['tarball_release'] = "1.2.7"
        Config.conf['installretry'] = 2
        mock_isavail.return_value = False
        mock_instlog.side_effect = [False, False]
        mock_getinfo.side_effect = [None, None]
        utools = UdockerTools(self.local)
        status = utools.install(False)
        self.assertFalse(status)


if __name__ == '__main__':
    main()
