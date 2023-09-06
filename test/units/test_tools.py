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


data_downl = (('file1', 'HTTP/1.1 200 OK', 0, 0, 'file1'),
              ('', 'HTTP/1.1 200 OK', 1, 0, '/tmp/tmpf'),
              ('', 'HTTP/1.1 401 FAIL', 1, 1, ''))


@pytest.mark.parametrize("fout,hdr_status,cnt_mktmp,cnt_rm,expected", data_downl)
def test_03__download(mocker, utools, get_url, fout, hdr_status, cnt_mktmp, cnt_rm, expected):
    """Test03 UdockerTools()._download()."""
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


data_getfile = (('', None, 0, False, 1, None, 0, False, 0, ''),
                ('https://down/f1', 'f1', 1, False, 0, None, 0, True, 1, 'f1'),
                ('/tmp/f1', '', 0, True, 1, 'f1', 1, True, 1, 'f1'))


PARAM = ("url,ret_downl,cnt_downl,ret_exists,cnt_exists,ret_rpath,"
         "cnt_rpath,ret_isfile,cnt_isfile,expected")
@pytest.mark.parametrize(PARAM, data_getfile)
def test_08__get_file(mocker, utools, url, ret_downl, cnt_downl, ret_exists, cnt_exists,
                      ret_rpath, cnt_rpath, ret_isfile, cnt_isfile, expected):
    """Test08 UdockerTools()._get_file()."""
    mock_downl = mocker.patch.object(UdockerTools, '_download', return_value=ret_downl)
    mock_exists = mocker.patch('udocker.tools.os.path.exists', return_value=ret_exists)
    mock_rpath = mocker.patch('udocker.tools.os.path.realpath', return_value=ret_rpath)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile', return_value=ret_isfile)

    out = utools._get_file(url)
    assert out == expected
    assert mock_downl.call_count == cnt_downl
    assert mock_exists.call_count == cnt_exists
    assert mock_rpath.call_count == cnt_rpath
    assert mock_isfile.call_count == cnt_isfile


# def test_13__clean_install(mocker, utools, lrepo):
#     """Test13 UdockerTools()._clean_install()."""
#     tfile = [TarInfo("udocker_dir/bin/ls"), TarInfo("udocker_dir/lib/lib1"),
#              TarInfo("udocker_dir/doc/f.txt")]
#     lrepo.bindir.return_value = '/bin'
#     lrepo.libdir.return_value = '/lib'
#     lrepo.docdir.return_value = '/doc'
#     mock_osbase = mocker.patch('os.path.basename',
#                                side_effect=['udocker_dir', 'udocker_dir', 'udocker_dir'])
#     mock_furegpref = mocker.patch('udocker.tools.FileUtil.register_prefix',
#                                   side_effect=[None, None, None])
#     mock_furm = mocker.patch('udocker.tools.FileUtil.remove',
#                              side_effect=[None, None, None])

#     utools._clean_install(tfile)
#     assert mock_osbase.call_count == 3
#     lrepo.bindir.assert_called()
#     lrepo.libdir.assert_called()
#     lrepo.docdir.assert_called()
#     assert mock_furegpref.call_count == 3
#     assert mock_furm.call_count == 3

    # with patch.object(tarfile, 'open', autospec=True) as open_mock:
    #     open_mock.side_effect = tfile
    #     utools._clean_install(open_mock)
    #     assert mock_osbase.call_count == 3
    #     lrepo.bindir.assert_called()
    #     lrepo.libdir.assert_called()
    #     lrepo.docdir.assert_called()
    #     assert mock_furegpref.call_count == 3
    #     assert mock_furm.call_count == 3


# def test_13__install(mocker, utools):
#     """Test13 UdockerTools()._install(). tar does not exist"""
#     tfile = "some.tar"
#     mock_isfile = mocker.patch('os.path.isfile', return_value=False)
#     mock_fuchmod = mocker.patch('udocker.tools.FileUtil.chmod')
#     out = utools._install(tfile)
#     assert not out
#     mock_isfile.assert_called()
#     mock_fuchmod.assert_not_called()


# def test_14__install(mocker, utools, lrepo):
#     """Test14 UdockerTools()._install(). tar does not open"""
#     tfile = "some.tar"
#     mock_isfile = mocker.patch('os.path.isfile', return_value=True)
#     mock_fuchmod = mocker.patch('udocker.tools.FileUtil.chmod')
#     lrepo.return_value.create_repo.return_value = None
#     mock_tarfile = mocker.mock_open()
#     mopen = mocker.patch("tarfile.open", mock_tarfile)
#     mopen.side_effect = tarfile.TarError
#     out = utools._install(tfile)
#     assert not out
#     mock_isfile.assert_called()
#     mock_fuchmod.assert_called()
#     lrepo.create_repo.assert_called()


# def test_15__install(mocker, utools, lrepo):
#     """Test15 UdockerTools()._install(). tar exists and opens"""
#     tfile = "some.tar"
#     mock_isfile = mocker.patch('os.path.isfile', return_value=True)
#     mock_fuchmod = mocker.patch('udocker.tools.FileUtil.chmod')
#     lrepo.return_value.create_repo.return_value = None
#     mock_tarfile = mocker.mock_open()
#     mopen = mocker.patch("tarfile.open", mock_tarfile)

#     out = utools._install(tfile)
#     assert not out
#     mock_isfile.assert_called()
#     mock_fuchmod.assert_called()
#     lrepo.create_repo.assert_called()


def test_16__get_mirrors(mocker, utools):
    """Test16 UdockerTools()._get_mirrors()."""
    mirrors = "https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz"
    out = utools._get_mirrors(mirrors)
    assert out == [mirrors]

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
