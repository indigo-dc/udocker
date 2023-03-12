#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""
import pytest
import tarfile
from tarfile import TarInfo
from udocker.config import Config
from udocker.utils.curl import CurlHeader
from udocker.tools import UdockerTools


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def get_url(mocker):
    mock_geturl = mocker.patch('udocker.tools.GetURL')
    return mock_geturl


@pytest.fixture
def utools(mocker, lrepo, get_url):
    return UdockerTools(lrepo)


@pytest.fixture
def cnf():
    Config().getconf()
    return Config()


def test_01__instructions(mocker, utools):
    """Test01 UdockerTools()._instructions()."""
    mock_msg = mocker.patch('udocker.tools.MSG.info')

    utools._instructions()
    assert mock_msg.call_count == 2


def test_02__version2int(utools):
    """Test02 UdockerTools()._version2int()."""
    out = utools._version2int("2.4")
    assert out == 2004000


data_verok = (([None, None], 0, '', False),
              (['2.4', '1.3'], 2, '2.4', True),
              (['1.4', '2.3'], 2, '1.4', False))


@pytest.mark.parametrize("side_v2i,cnt_v2i,pin,expected", data_verok)
def test_04__version_isok(mocker, utools, side_v2i, cnt_v2i, pin, expected):
    """Test04 UdockerTools()._version_isok()."""
    mock_ver2int = mocker.patch.object(UdockerTools, '_version2int', side_effect=side_v2i)

    out = utools._version_isok(pin)
    assert out == expected
    assert mock_ver2int.call_count == cnt_v2i


def test_05_is_available(mocker, utools, lrepo):
    """Test05 UdockerTools().is_available()."""
    lrepo.return_value.libdir = '/cont/ROOT/lib'
    mock_fuget = mocker.patch('udocker.tools.FileUtil.getdata', return_value="2.3\n")
    mock_verok = mocker.patch.object(UdockerTools, '_version_isok', return_value=True)

    out = utools.is_available()
    assert out
    mock_fuget.assert_called()
    mock_verok.assert_called()


def test_06_purge(mocker, utools):
    """Test06 UdockerTools().purge()."""
    mock_lsdir = mocker.patch('os.listdir', side_effect=[["f1", "f2"], ["f3", "f4"], ["f5", "f6"]])
    mock_logdeb = mocker.patch('udocker.tools.LOG.debug')
    mock_fureg = mocker.patch('udocker.tools.FileUtil.register_prefix',
                              side_effect=[None, None, None, None, None, None])
    mock_furm = mocker.patch('udocker.tools.FileUtil.remove',
                             side_effect=[None, None, None, None, None, None])

    utools.purge()
    assert mock_lsdir.call_count == 3
    assert mock_fureg.call_count == 6
    assert mock_furm.call_count == 6
    assert mock_logdeb.call_count == 6


data_downl = (('file1', 'HTTP/1.1 200 OK', 0, 0, 'file1'),
              ('', 'HTTP/1.1 200 OK', 1, 0, '/tmp/tmpf'),
              ('', 'HTTP/1.1 401 FAIL', 1, 1, ''))


@pytest.mark.parametrize("fout,hdr_status,cnt_mktmp,cnt_rm,expected", data_downl)
def test_07__download(mocker, utools, get_url, fout, hdr_status, cnt_mktmp, cnt_rm, expected):
    """Test07 UdockerTools()._download()."""
    hdr = CurlHeader()
    hdr.data["X-ND-HTTPSTATUS"] = hdr_status
    mock_fumktmp = mocker.patch('udocker.tools.FileUtil.mktmp', return_value="/tmp/tmpf")
    get_url.return_value.get.return_value = (hdr, "content type...")
    mock_furm = mocker.patch('udocker.tools.FileUtil.remove')

    out = utools._download("https://down/file1", fout)
    assert out == expected
    assert mock_fumktmp.call_count == cnt_mktmp
    get_url.return_value.get.assert_called()
    assert mock_furm.call_count == cnt_rm


# @patch('udocker.tools.os.path.isfile')
# @patch('udocker.tools.os.path.realpath')
# @patch('udocker.tools.os.path.exists')
# @patch.object(UdockerTools, '_download')
# def test_08__get_file(self, mock_downl, mock_exists, mock_rpath, mock_isfile):
#     """Test08 UdockerTools()._get_file()."""
#     url = ""
#     mock_downl.return_value = ""
#     mock_exists.return_value = False
#     mock_isfile.return_value = False
#     utools = UdockerTools(self.local)
#     status = utools._get_file(url)
#     self.assertFalse(mock_downl.called)
#     self.assertTrue(mock_exists.called)
#     self.assertEqual(status, "")

#     url = "https://down/file"
#     mock_downl.return_value = "/tmp/file"
#     mock_exists.return_value = True
#     mock_isfile.return_value = True
#     mock_rpath.return_value = "/tmp/file"
#     utools = UdockerTools(self.local)
#     status = utools._get_file(url)
#     self.assertTrue(mock_downl.called)
#     self.assertTrue(mock_exists.called)
#     self.assertTrue(mock_isfile.called)
#     self.assertEqual(status, "/tmp/file")

# @patch.object(UdockerTools, '_version_isok')
# @patch('udocker.tools.FileUtil.remove')
# @patch('udocker.tools.FileUtil.getdata')
# @patch('udocker.tools.os.path.basename')
# @patch('udocker.tools.FileUtil.mktmpdir')
# @patch('udocker.tools.os.path.isfile')
# def test_09__verify_version(self, mock_isfile, mock_fumktmp, mock_osbase, mock_fugetdata,
#                             mock_furm, mock_versionok):
#     """Test09 UdockerTools()._verify_version()."""
#     tball = "/home/udocker.tar"
#     mock_isfile.return_value = False
#     utools = UdockerTools(self.local)
#     status = utools._verify_version(tball)
#     self.assertTrue(mock_isfile.called)
#     self.assertEqual(status, (False, ""))

#     tball = "/home/udocker.tar"
#     mock_isfile.return_value = True
#     mock_fumktmp.return_value = ""
#     utools = UdockerTools(self.local)
#     status = utools._verify_version(tball)
#     self.assertTrue(mock_isfile.called)
#     self.assertTrue(mock_fumktmp.called)
#     self.assertEqual(status, (False, ""))

#     tball = "/home/udocker.tar"
#     tinfo1 = TarInfo("udocker_dir/lib/VERSION")
#     tinfo2 = TarInfo("a")
#     mock_isfile.return_value = True
#     mock_fumktmp.return_value = "/home/tmp"
#     mock_osbase.return_value = "VERSION"
#     mock_fugetdata.return_value = "1.2.7"
#     mock_furm.return_value = None
#     mock_versionok.return_value = True
#     with patch.object(tarfile, 'open', autospec=True) as open_mock:
#         open_mock.return_value.getmembers.return_value = [tinfo2, tinfo1]
#         open_mock.return_value.extract.return_value = None
#         utools = UdockerTools(self.local)
#         status = utools._verify_version(tball)
#         self.assertEqual(status, (True, "1.2.7"))
#         self.assertTrue(mock_furm.called)

# @patch.object(UdockerTools, '_clean_install')
# @patch('udocker.tools.os.path.basename')
# @patch('udocker.tools.os.path.basename')
# @patch('udocker.tools.FileUtil')
# @patch('udocker.tools.os.path.isfile')
# def test_10__install(self, mock_isfile, mock_futil, mock_osbase, mock_cleaninstall):
#     """Test10 UdockerTools()._install()."""
#     tfile = ""
#     mock_isfile.return_value = False
#     utools = UdockerTools(self.local)
#     status = utools._install(tfile)
#     self.assertFalse(status)

#     tinfo1 = TarInfo("udocker_dir/bin/ls")
#     tinfo2 = TarInfo("udocker_dir/lib/lib1")
#     tfile = "udocker.tar"
#     mock_isfile.return_value = True
#     mock_futil.return_value.chmod.return_value = None
#     mock_futil.return_value.rchmod.side_effect = [None, None, None, None, None, None]
#     mock_osbase.side_effect = ["ls", "ls", "lib1", "lib1", "doc", "doc1"]
#     self.local.create_repo.return_value = None
#     with patch.object(tarfile, 'open', autospec=True) as open_mock:
#         open_mock.return_value.getmembers.side_effect = [[tinfo1, tinfo2],
#                                                             [tinfo1, tinfo2],
#                                                             [tinfo1, tinfo2]]
#         open_mock.return_value.extract.side_effect = [None, None]
#         utools = UdockerTools(self.local)
#         status = utools._install(tfile)
#         self.assertTrue(status)
#         self.assertTrue(mock_futil.called)
#         self.assertTrue(mock_futil.return_value.rchmod.call_count, 4)

# def test_11__get_mirrors(self):
#     """Test11 UdockerTools()._get_mirrors()."""
#     mirrors = "https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz"
#     utools = UdockerTools(self.local)
#     status = utools._get_mirrors(mirrors)
#     self.assertEqual(status, [mirrors])

# @patch.object(UdockerTools, '_get_file')
# @patch.object(UdockerTools, '_get_mirrors')
# @patch('udocker.tools.json.load')
# def test_12_get_installinfo(self, mock_jload, mock_mirr, mock_getf):
#     """Test12 UdockerTools().get_installinfo()."""
#     Config.conf['installinfo'] = "/home/info.json"
#     res = {"tarversion": "1.2.7"}
#     mock_jload.return_value = {"tarversion": "1.2.7"}
#     mock_mirr.return_value = ["/home/info.json"]
#     mock_getf.return_value = "info.json"
#     subuid_line = StringIO('{"tarversion": "1.2.7"}')
#     with patch(BOPEN) as mopen:
#         mopen.return_value.__iter__ = (lambda self: iter(subuid_line.readline, ''))
#         utools = UdockerTools(self.local)
#         status = utools.get_installinfo()
#         self.assertEqual(status, res)

# @patch.object(UdockerTools, '_install')
# @patch.object(UdockerTools, '_verify_version')
# @patch.object(UdockerTools, '_get_file')
# @patch.object(UdockerTools, '_get_mirrors')
# @patch('udocker.tools.FileUtil.remove')
# def test_13__install_logic(self, mock_furm, mock_getmirr, mock_getfile, mock_ver, mock_install):
#     """Test13 UdockerTools()._install_logic()."""
#     mock_furm.return_value = None
#     mock_getmirr.return_value = "https://down.pt/udocker-1.2.7.tar.gz"
#     mock_getfile.return_value = "udocker-1.2.7.tar.gz"
#     mock_ver.return_value = (True, "1.2.7")
#     mock_install.return_value = True
#     utools = UdockerTools(self.local)
#     status = utools._install_logic(False)
#     self.assertTrue(status)
#     self.assertTrue(mock_getmirr.called)
#     self.assertTrue(mock_getfile.called)
#     self.assertTrue(mock_ver.called)
#     self.assertTrue(mock_install.called)

#     mock_furm.return_value = None
#     mock_getmirr.return_value = "https://down.pt/udocker-1.2.7.tar.gz"
#     mock_getfile.return_value = "udocker-1.2.7.tar.gz"
#     mock_ver.return_value = (False, "")
#     mock_install.return_value = True
#     utools = UdockerTools(self.local)
#     status = utools._install_logic(True)
#     self.assertTrue(status)

#     mock_furm.return_value = None
#     mock_getmirr.return_value = "https://down.pt/udocker-1.2.7.tar.gz"
#     mock_getfile.return_value = "udocker-1.2.7.tar.gz"
#     mock_ver.return_value = (False, "")
#     mock_install.return_value = True
#     utools = UdockerTools(self.local)
#     status = utools._install_logic(False)
#     self.assertFalse(status)

# @patch.object(UdockerTools, 'get_installinfo')
# @patch.object(UdockerTools, '_install_logic')
# @patch.object(UdockerTools, 'is_available')
# def test_14_install(self, mock_isavail, mock_instlog, mock_getinfo):
#     """Test14 UdockerTools().install()."""
#     Config.conf['autoinstall'] = True
#     Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
#     Config.conf['tarball_release'] = "1.2.7"
#     Config.conf['installretry'] = 2
#     mock_isavail.return_value = True
#     utools = UdockerTools(self.local)
#     status = utools.install(False)
#     self.assertTrue(status)
#     self.assertTrue(mock_isavail.called)

#     Config.conf['autoinstall'] = False
#     Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
#     Config.conf['tarball_release'] = "1.2.7"
#     Config.conf['installretry'] = 2
#     mock_isavail.return_value = False
#     utools = UdockerTools(self.local)
#     status = utools.install(False)
#     self.assertEqual(status, None)
#     self.assertFalse(utools._autoinstall)

#     Config.conf['autoinstall'] = False
#     Config.conf['tarball'] = ""
#     Config.conf['tarball_release'] = "1.2.7"
#     Config.conf['installretry'] = 2
#     mock_isavail.return_value = True
#     utools = UdockerTools(self.local)
#     status = utools.install(False)
#     self.assertTrue(status)
#     self.assertEqual(utools._tarball, "")

#     Config.conf['autoinstall'] = True
#     Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
#     Config.conf['tarball_release'] = "1.2.7"
#     Config.conf['installretry'] = 2
#     mock_isavail.return_value = False
#     mock_instlog.side_effect = [False, True]
#     mock_getinfo.side_effect = [None, None]
#     utools = UdockerTools(self.local)
#     status = utools.install(False)
#     self.assertTrue(status)
#     self.assertTrue(mock_instlog.call_count, 2)
#     self.assertTrue(mock_getinfo.call_count, 2)

#     Config.conf['autoinstall'] = True
#     Config.conf['tarball'] = "udocker-1.2.7.tar.gz"
#     Config.conf['tarball_release'] = "1.2.7"
#     Config.conf['installretry'] = 2
#     mock_isavail.return_value = False
#     mock_instlog.side_effect = [False, False]
#     mock_getinfo.side_effect = [None, None]
#     utools = UdockerTools(self.local)
#     status = utools.install(False)
#     self.assertFalse(status)

# @patch('udocker.tools.json.load')
# @patch('udocker.tools.LOG')
# @patch('udocker.tools.os.path.isfile')
# @patch.object(UdockerTools, '_get_file')
# @patch.object(UdockerTools, '_get_mirrors')
# def test_15__get_metadata(self, mock_mirr, mock_file, mock_isfile, mock_log, mock_jload):
#     """Test15 UdockerTools()._get_metadata()."""
#     mjson = [{
#         "module": "proot",
#         "version": "5.1.0",
#         "arch": "arm",
#         "os": "Centos",
#         "os_ver": "7",
#         "kernel_ver": "4.7.0",
#         "dependencies": ["udocker"],
#         "digit_signature": "",
#         "uid": "12345",
#         "fname": "proot-arm",
#         "sha256sum": "1234567",
#         "urls": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/bin/proot-arm"
#         ],
#         "docs_url": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/proot_docs.tgz"
#         ]
#     }]
#     mock_mirr.return_value = "https://download.ncg.ingrid.pt/webdav/udocker/metadata.json"
#     mock_file.return_value = "metadata.json"
#     mock_jload.return_value = mjson
#     mock_isfile.return_value = False
#     fjson_line = StringIO(str(mjson))
#     with patch(BOPEN) as mopen:
#         mopen.return_value = fjson_line
#         utools = UdockerTools(self.local)
#         status = utools._get_metadata(False)
#         self.assertTrue(mock_log.info.called)
#         self.assertFalse(mock_log.error.called)

#     mock_jload.side_effect = KeyError("fail")
#     utools = UdockerTools(self.local)
#     status = utools._get_metadata(False)
#     self.assertTrue(mock_log.error.called)

# @patch('udocker.tools.LOG')
# def test_16__match_mod(self, mock_log):
#     """Test16 UdockerTools()._match_mod()."""
#     mjson = [{
#         "module": "proot",
#         "version": "5.1.0",
#         "arch": "arm",
#         "os": "Centos",
#         "os_ver": "7",
#         "kernel_ver": "4.7.0",
#         "dependencies": ["udocker"],
#         "digit_signature": "",
#         "uid": "12345",
#         "fname": "proot-arm",
#         "sha256sum": "1234567",
#         "urls": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/bin/proot-arm"
#         ],
#         "docs_url": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/proot_docs.tgz"
#         ]
#     }]
#     utools = UdockerTools(self.local)
#     status = utools._match_mod("runc", "x86_64", "Ubuntu", "16.04", mjson)
#     self.assertFalse(mock_log.debug.called)
#     self.assertEqual(status, [])

#     utools = UdockerTools(self.local)
#     status = utools._match_mod("proot", "arm", "Centos", "7", mjson)
#     self.assertTrue(mock_log.debug.called)
#     self.assertEqual(status, mjson[0]["urls"])

# @patch('udocker.tools.LOG')
# @patch('udocker.tools.OSInfo')
# @patch.object(UdockerTools, '_match_mod')
# @patch.object(UdockerTools, '_get_metadata')
# def test_17_select_tarnames(self, mock_meta, mock_match, mock_osinfo, mock_log):
#     """Test17 UdockerTools().select_tarnames()."""
#     mjson = [{
#         "module": "proot",
#         "version": "5.1.0",
#         "arch": "arm",
#         "os": "Centos",
#         "os_ver": "7",
#         "kernel_ver": "4.7.0",
#         "dependencies": ["udocker"],
#         "digit_signature": "",
#         "uid": "12345",
#         "fname": "proot-arm",
#         "sha256sum": "1234567",
#         "urls": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/bin/proot-arm"
#         ],
#         "docs_url": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/proot_docs.tgz"
#         ]
#     },
#     {
#         "module": "libfakechroot",
#         "version": "4.3.0",
#         "arch": "arm",
#         "os": "Centos",
#         "os_ver": "7",
#         "kernel_ver": "4.7.0",
#         "dependencies": ["udocker"],
#         "digit_signature": "",
#         "uid": "542433",
#         "fname": "libfakechroot-arm.so",
#         "sha256sum": "7483r932",
#         "urls": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/lib/libfakechroot-arm.so"
#         ],
#         "docs_url": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/proot_docs.tgz"
#         ]
#     }]
#     res = ["https://download.ncg.ingrid.pt/webdav/udocker/engines/bin/proot-arm",
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/lib/libfakechroot-arm.so"]
#     mock_meta.return_value = mjson
#     utools = UdockerTools(self.local)
#     status = utools.select_tarnames(["12345"])
#     self.assertTrue(mock_log.debug.called)
#     self.assertEqual(status, [["https://download.ncg.ingrid.pt/webdav/udocker/engines/bin/proot-arm"]])

#     mock_meta.return_value = mjson
#     mock_match.return_value = mjson[0]["urls"]
#     mock_osinfo.return_value.arch.return_value = "amd64"
#     mock_osinfo.return_value.osdistribution.return_value = ("linux", "4.8.1")
#     utools = UdockerTools(self.local)
#     status = utools.select_tarnames([])
#     self.assertTrue(mock_log.debug.called)
#     self.assertTrue(mock_osinfo.return_value.arch.called)
#     self.assertTrue(mock_osinfo.return_value.osdistribution.called)
# #        self.assertEqual(status, [res])

# @patch('udocker.tools.MSG')
# @patch.object(UdockerTools, '_get_metadata')
# def test_18_show_metadata(self, mock_meta, mock_msg):
#     """Test18 UdockerTools().show_metadata()."""
#     mjson = [{
#         "module": "proot",
#         "version": "5.1.0",
#         "arch": "arm",
#         "os": "Centos",
#         "os_ver": "7",
#         "kernel_ver": "4.7.0",
#         "dependencies": ["udocker"],
#         "digit_signature": "",
#         "uid": "12345",
#         "fname": "proot-arm",
#         "sha256sum": "1234567",
#         "urls": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/bin/proot-arm"
#         ],
#         "docs_url": [
#             "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/proot_docs.tgz"
#         ]
#     }]
#     mock_meta.return_value = mjson
#     utools = UdockerTools(self.local)
#     status = utools.show_metadata(False)
#     self.assertTrue(status)
#     self.assertTrue(mock_msg.info.called)

#     mock_meta.return_value = []
#     utools = UdockerTools(self.local)
#     status = utools.show_metadata(False)
#     self.assertFalse(status)
#     self.assertTrue(mock_msg.info.called)
