#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""
import json
import os
import tarfile
import stat

import pytest

from udocker.config import Config
from udocker.tools import UdockerTools
from udocker.utils.curl import CurlHeader
from udocker.utils.fileutil import FileUtil

MOD1 = {
    "uid": 1,
    "module": "crun",
    "tarball": "crun-x86_64.tgz",
    "version": "1.6",
    "arch": "x86_64",
    "os": 'null',
    "os_ver": 'null',
    "kernel_ver": "",
    "sha256sum": "4907b4005436686e453297f7e011ddb655c410429f711d787546f5ecceb03048",
    "installdir": "bin/",
    "fname": "crun-x86_64",
    "docs": "COPYING.crun",
    "urls": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/tarballs/crun-x86_64.tgz",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/tarballs/crun-x86_64.tgz"
    ],
    "dependencies": [],
    "docs_url": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/COPYING.crun",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/docs/COPYING.crun"
    ]
}

MOD2 = {
    "uid": 9,
    "module": "proot",
    "tarball": "proot-x86_64-4_8_0.tgz",
    "version": "5.1.1",
    "arch": "x86_64",
    "os": 'null',
    "os_ver": 'null',
    "kernel_ver": ">=4.8.0",
    "sha256sum": "1a926182aa16cc7ba77e278851a62f33995e2515e01c7a99932bb6e7f853b0a9",
    "installdir": "bin/",
    "fname": "proot-x86_64-4_8_0",
    "docs": "COPYING.proot",
    "urls": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/tarballs/proot-x86_64-4_8_0.tgz",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/tarballs/proot-x86_64-4_8_0.tgz"
    ],
    "dependencies": [],
    "docs_url": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/COPYING.proot",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/docs/COPYING.proot"
    ]
}

MOD3 = {
    "uid": 13,
    "module": "patchelf",
    "tarball": "patchelf-x86_64.tgz",
    "version": "0.9",
    "arch": "x86_64",
    "os": 'null',
    "os_ver": 'null',
    "kernel_ver": "",
    "sha256sum": "9acf2db637365bf10379bc3e51658a6f0d3303156457f7827b04d3f9f32f7e6a",
    "installdir": "bin/",
    "fname": "patchelf-x86_64",
    "docs": "COPYING.patchelf",
    "urls": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/tarballs/patchelf-x86_64.tgz",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/tarballs/patchelf-x86_64.tgz"
    ],
    "dependencies": [],
    "docs_url": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/COPYING.patchelf",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/docs/COPYING.patchelf"
    ]
}

MOD4 = {
    "uid": 16,
    "module": "libfakechroot",
    "tarball": "libfakechroot-x86_64.tgz",
    "version": "2.18",
    "arch": "x86_64",
    "os": 'null',
    "os_ver": 'null',
    "kernel_ver": "",
    "sha256sum": "c4280e0e3b3fa5ba6d94be0d43a2379d9d4390f08c96adc83cf4ba6be939d757",
    "installdir": "lib/",
    "fname": "",
    "docs": "LIC-COPY-fakechroot.tgz",
    "urls": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/tarballs/libfakechroot-x86_64.tgz",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/tarballs/libfakechroot-x86_64.tgz"
    ],
    "dependencies": [
        "patchelf-x86_64.tgz"
    ],
    "docs_url": [
        "https://download.ncg.ingrid.pt/webdav/udocker/engines/doc/LIC-COPY-fakechroot.tgz",
        "https://github.com/LIP-Computing/udocker_tools/raw/main/docs/LIC-COPY-fakechroot.tgz"
    ]
}


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def get_url(mocker):
    mock_geturl = mocker.patch('udocker.tools.GetURL')
    return mock_geturl


@pytest.fixture
def utools(lrepo, get_url):
    return UdockerTools(lrepo)


@pytest.fixture
def cnf():
    Config().getconf()
    return Config()


@pytest.fixture
def logger(mocker):
    mock_log = mocker.patch('udocker.tools.LOG')
    return mock_log


@pytest.fixture
def mock_tarfile(mocker):
    class MockTarFile:
        def __init__(self, getnames_return=None, getmembers_return=None):
            self.getnames_return = getnames_return
            self.getmembers_return = getmembers_return

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def getnames(self):
            return self.getnames_return

        def getmembers(self):
            return self.getmembers_return

        def extractall(self, path=""):
            pass

    def create_mock_tarfile(getnames_return=None, getmembers_return=None):
        return MockTarFile(getnames_return, getmembers_return)

    mocker.patch('tarfile.open', side_effect=create_mock_tarfile)
    return create_mock_tarfile


def test_01__instructions(mocker, utools):
    """Test01 UdockerTools()._instructions()."""
    mock_msg = mocker.patch('udocker.tools.MSG.info')
    utools._instructions()
    assert mock_msg.call_count == 2

@pytest.mark.parametrize("version, expected", [
    ("2.4.3", 2004003),
    ("2.4", 2004000),
    ("2", 2000000),
    ("", 0),
    ("2.a.3", 2000003),
    ("version2.4", 4000),
    ("2.4.3.1", 2004003)
])
def test_02__version2int(utools, version, expected):
    """Test02 UdockerTools()._version2int()."""
    out = utools._version2int(version)
    assert out == expected


@pytest.mark.parametrize("given_version, required_version, expected_result", [
    ("2.4.3", "2.4.3", True),
    ("2.4.4", "2.4.3", True),
    ("2.4.2", "2.4.3", False),
    ("", "2.4.3", False),
    ("2.4.3", "", False),
    ("invalid", "2.4.3", False),
])
def test_03_version_isok(utools, mocker, given_version, required_version, expected_result):
    """Test03 UdockerTools()._version_isok()."""
    mocker.patch.object(utools, '_tarball_release', required_version)
    result = utools._version_isok(given_version)
    assert result == expected_result


data_downl = (('file1', 'HTTP/1.1 200 OK', 0, 0, 'file1'),
              ('', 'HTTP/1.1 200 OK', 1, 0, '/tmp/tmpf'),
              ('', 'HTTP/1.1 401 FAIL', 1, 1, ''))


@pytest.mark.parametrize("fout,hdr_status,cnt_mktmp,cnt_rm,expected", data_downl)
def test_04__download(mocker, utools, get_url, fout, hdr_status, cnt_mktmp, cnt_rm, expected):
    """Test04 UdockerTools()._download()."""
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


data_getfile = (('', None, 0, False, 1, None, 0, False, 0, 0, '', ''),
                ('https://down/f1', 'f1', 1, False, 0, None, 0, True, 1, 0, '', 'f1'),
                ('/tmp/f1', '', 0, True, 1, 'f1', 1, True, 1, 0, '', 'f1'),
                ('/tmp/f1', '', 0, True, 1, 'f1', 1, True, 1, 1, 'someout', 'f1')
                )


@pytest.mark.parametrize('url,mdownl,cdownl,mexists,cexists,mrpath,crpath,misfile,cisfile,cshucp,fout,expected',
                         data_getfile)
def test_05__get_file(mocker, utools, url, mdownl, cdownl, mexists, cexists, mrpath, crpath,
                      misfile, cisfile, cshucp, fout, expected):
    """Test05 UdockerTools()._get_file()."""
    mock_downl = mocker.patch.object(UdockerTools, '_download', return_value=mdownl)
    mock_exists = mocker.patch('udocker.tools.os.path.exists', return_value=mexists)
    mock_rpath = mocker.patch('udocker.tools.os.path.realpath', return_value=mrpath)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile', return_value=misfile)
    mock_shucp = mocker.patch('udocker.tools.shutil.copy2')
    out = utools._get_file(url, fout)
    assert out == expected
    assert mock_downl.call_count == cdownl
    assert mock_exists.call_count == cexists
    assert mock_rpath.call_count == crpath
    assert mock_isfile.call_count == cisfile
    assert mock_shucp.call_count == cshucp


@pytest.mark.parametrize("tarball_file, is_file, mktmpdir, expected_result", [
    ("valid_tarball.tar.gz", True, '/tmp/tmpdir', (True, "1.0.0")),
    ("valid_tarball.tar.gz", True, None, (False, "")),
    ("missing_tarball.tar.gz", False, '/tmp/tmpdir', (False, "")),
    ("invalid_tarball.tar.gz", True, '/tmp/tmpdir', (False, "")),
])
def test_06__verify_version(mocker, utools, tarball_file, is_file, mktmpdir, expected_result):
    """Test06 UdockerTools()._verify_version()."""
    mock_tarfile = mocker.Mock()
    mock_tarfile_open = mocker.patch('tarfile.open', return_value=mock_tarfile)

    if tarball_file.startswith("invalid"):
        mock_tarfile_open.side_effect = tarfile.TarError
    else:
        mock_member = mocker.Mock()
        mock_member.name = "udocker_dir/lib/VERSION"
        mock_tarfile.getmembers.return_value = [mock_member]

    mocker.patch.object(UdockerTools, '_version_isok', return_value=True)
    mocker.patch('os.path.isfile', return_value=is_file)
    mocker.patch.object(FileUtil, 'mktmpdir', return_value=mktmpdir)

    if tarball_file.startswith("valid"):
        mocker.patch.object(FileUtil, 'getdata', return_value="1.0.0")

    result = utools._verify_version(tarball_file)
    assert result == expected_result


def test_07__clean_install(mocker, utools, lrepo):
    """Test07 UdockerTools()._clean_install()."""
    lrepo.bindir = '/test/bindir'
    lrepo.libdir = '/test/libdir'
    lrepo.docdir = '/test/docdir'

    tar_members = [
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    ]

    tar_members[0].name = 'udocker_dir/bin/executable1'
    tar_members[1].name = 'udocker_dir/lib/library1'
    tar_members[2].name = 'udocker_dir/doc/document1'

    mock_tfile = mocker.Mock()
    mock_tfile.getmembers.return_value = tar_members

    mock_fileutil = mocker.patch('udocker.tools.FileUtil')
    mock_remove = mock_fileutil.return_value.remove

    utools._clean_install(mock_tfile)

    expected_calls = [
        mocker.call('/test/bindir/executable1'),
        mocker.call('/test/libdir/library1'),
        mocker.call('/test/docdir/document1'),
    ]

    mock_fileutil.assert_has_calls(expected_calls, any_order=True)
    assert mock_remove.mock_calls == [mocker.call(recursive=True)] * 3
    assert mock_remove.call_count == 3


def test_08__get_mirrors(mocker, utools):
    """Test08 UdockerTools()._get_mirrors()."""
    mirrors = "https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz"
    out = utools._get_mirrors(mirrors)
    assert out == [mirrors]


def test_09_get_metadata(mocker, utools):
    """Test09 UdockerTools().get_metadata()."""
    mirrors = ['https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz']
    metajson = [MOD1]

    mock_fjson = mocker.mock_open(read_data=str(metajson))
    mocker.patch("builtins.open", mock_fjson)
    mock_getmirr = mocker.patch.object(UdockerTools, '_get_mirrors', return_value=mirrors)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile')
    mock_jload = mocker.patch('udocker.tools.json.load', return_value=metajson)
    mock_getfile = mocker.patch.object(UdockerTools, '_get_file', return_value=mock_fjson)
    resout = utools.get_metadata(True)
    assert resout == metajson
    mock_getmirr.assert_called()
    mock_jload.assert_called()
    mock_getfile.assert_called()


def test_10_get_metadata(mocker, utools):
    """Test10 UdockerTools().get_metadata()."""
    mirrors = ['https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz']
    mock_fjson = mocker.mock_open()
    mock_fjson.side_effect = OSError
    mock_getmirr = mocker.patch.object(UdockerTools, '_get_mirrors', return_value=mirrors)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile')
    mock_getfile = mocker.patch.object(UdockerTools, '_get_file')
    resout = utools.get_metadata(True)
    assert resout == []
    mock_getmirr.assert_called()
    mock_getfile.assert_called()


data_sel = (([1], [], [False, False], [MOD1]),
            ([], ['proot'], [False, True], [MOD2]),
            ([], [], [True, False], [MOD2, MOD3, MOD4]))


@pytest.mark.parametrize('list_uid,list_names,sekgreat,expected', data_sel)
def test_11__select_modules(mocker, utools, list_uid, list_names, sekgreat, expected):
    """Test11 UdockerTools()._select_modules()."""
    metajson = [MOD1, MOD2, MOD3, MOD4]
    mock_getmeta = mocker.patch.object(UdockerTools, 'get_metadata', return_value=metajson)
    mock_hinfo = mocker.patch('udocker.tools.HostInfo')
    mock_hinfo.return_value.arch.return_value = 'x86_64'
    mock_hinfo.return_value.oskernel_isgreater.side_effect = sekgreat
    resout = utools._select_modules(list_uid, list_names)
    assert resout == expected


data_vsha = (([MOD1, MOD2], [MOD1["sha256sum"], MOD2["sha256sum"]], True),
             ([MOD1, MOD2], [MOD1["sha256sum"], 'xxxx'], False))


@pytest.mark.parametrize('lmods,lsha,expected', data_vsha)
def test_12_verify_sha(mocker, utools, lmods, lsha, expected):
    """Test12 UdockerTools().verify_sha()."""
    mock_sha = mocker.patch('udocker.tools.ChkSUM.sha256', side_effect=lsha)
    resout = utools.verify_sha(lmods, 'udocker/tar')
    assert resout == expected
    assert mock_sha.call_count == 2


data_downtar = ((True, True, 2, True),
                (False, False, 0, False))


@pytest.mark.parametrize('vsha,force,cgetfile,expected', data_downtar)
def test_13_download_tarballs(mocker, utools, vsha, force, cgetfile, expected):
    """Test13 UdockerTools().download_tarballs()."""
    lmods = [MOD1, MOD2]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_getfile = mocker.patch.object(UdockerTools, '_get_file',
                                       side_effect=[False, True, False, False])
    mock_vsha = mocker.patch.object(UdockerTools, 'verify_sha', return_value=vsha)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile', side_effect=[True, True, True, True])
    resout = utools.download_tarballs('dumlist', 'dstdir', 'srcloc', force)
    assert resout == expected
    mock_selmod.assert_called()
    mock_vsha.assert_called()
    assert mock_getfile.call_count == cgetfile


data_deltar = (([1], 1, 0),
               ([], 0, 1))


@pytest.mark.parametrize('listuid,cselmod,cgetmeta', data_deltar)
def test_14_delete_tarballs(mocker, utools, listuid, cselmod, cgetmeta):
    """Test14 UdockerTools().delete_tarballs()."""
    lmods = [MOD1, MOD2]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_getmeta = mocker.patch.object(UdockerTools, 'get_metadata', return_value=lmods)
    mock_pexists = mocker.patch('udocker.tools.os.path.exists', side_effect=[True, True])
    mock_rm = mocker.patch('udocker.tools.os.remove', side_effect=[None, None])
    resout = utools.delete_tarballs(listuid, 'moddir')
    assert resout
    assert mock_selmod.call_count == cselmod
    assert mock_getmeta.call_count == cgetmeta
    assert mock_pexists.call_count == 2
    assert mock_rm.call_count == 2


def test_15_delete_tarballs(mocker, utools):
    """Test15 UdockerTools().delete_tarballs()."""
    lmods = [MOD1]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_getmeta = mocker.patch.object(UdockerTools, 'get_metadata', return_value=lmods)
    mock_pexists = mocker.patch('udocker.tools.os.path.exists', return_value=True)
    mock_rm = mocker.patch('udocker.tools.os.remove', side_effect=OSError)
    resout = utools.delete_tarballs([1], 'moddir')
    assert not resout
    mock_selmod.assert_called()
    mock_getmeta.assert_not_called()
    mock_pexists.assert_called()
    mock_rm.assert_called()


data_downlic = ((False, [False, True], 0, True),
                (True, [True, False], 1, True),
                (True, [False, False], 1, False))


@pytest.mark.parametrize('force,mgetfile,cgetfile,expected', data_downlic)
def test_16_download_licenses(mocker, utools, force, mgetfile, cgetfile, expected):
    """Test16 UdockerTools().download_licenses()."""
    lmods = [MOD1]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_getfile = mocker.patch.object(UdockerTools, '_get_file', side_effect=mgetfile)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile', side_effect=[True, True])
    resout = utools.download_licenses('dstdir', 'srcloc', force)
    assert resout == expected
    mock_selmod.assert_called()
    assert mock_getfile.call_count == cgetfile


data_showmeta = ((True, 18), (False, 2))


@pytest.mark.parametrize('long,cmsg', data_showmeta)
def test_17_show_metadata(mocker, utools, long, cmsg):
    """Test17 UdockerTools().show_metadata()."""
    mock_msg = mocker.patch('udocker.tools.MSG.info')
    assert utools.show_metadata([MOD1], long)
    assert mock_msg.call_count == cmsg


# data_instlog = (([MOD1], False, True),
#                 ([MOD4], True, True))

@pytest.mark.parametrize("list_uid, top_dir, tar_dir, force, expect_success, log_info, log_error", [
    (["uid1"], "/top/dir", "/tar/dir", False, True, "installing tarfile", ""),
    (["uid2"], "", "/tar/dir", True, False, "", "failed to install module"),
    (["uid3"], "", "/tar/dir", False, True, "", "")
])
def test_18_installmod_logic(mocker, utools, logger, mock_tarfile, list_uid, top_dir, tar_dir, force, expect_success,
                             log_info, log_error):
    """Test18 UdockerTools._installmod_logic()."""
    if expect_success:
        mock_tarfile_instance = mock_tarfile(["file1", "file2"] if expect_success else [],
                                             [mocker.Mock(), mocker.Mock()] if expect_success else [])
        mocker.patch('tarfile.open', return_value=mock_tarfile_instance)
    else:
        mocker.patch('tarfile.open', side_effect=tarfile.TarError)

    mocker.patch.object(utools, '_select_modules', return_value=[{"tarball": "module.tgz", "installdir": "bin/"}])
    mocker.patch.object(os.path, 'isfile', return_value=not expect_success)
    mocker.patch.object(FileUtil, 'rchmod')
    mocker.patch.object(utools, '_clean_install')

    result = utools._installmod_logic(list_uid, top_dir, tar_dir, force)

    if expect_success:
        assert result is True
        if log_info:
            assert logger.info.called
            assert log_info in logger.info.call_args[0][0]
    else:
        if log_error:
            assert logger.error.called
            assert log_error in logger.error.call_args[0][0]

@pytest.mark.parametrize("force, licenses_exist, expected_result, raises_error, log_error, log_info, log_debug", [
    (True, False, True, False, "", "installing licenses", ""),
    (False, True, True, False, "", "", "licenses already installed"),
    (False, False, True, False, "", "installing licenses", ""),
    (True, False, False, True, "failed to install licenses", "", ""),
])
def test_19_install_licenses(mocker, utools, mock_tarfile, logger, force, licenses_exist, expected_result, raises_error,
                             log_error, log_info, log_debug):
    """Test19 UdockerTools()._install_licenses()."""
    mod_all = {"docs": "license.tgz"}
    tar_dir = "/tar/dir"
    top_dir = "/some/dir"

    mocker.patch('os.path.isfile', return_value=licenses_exist)

    if raises_error:
        mocker.patch('tarfile.open', side_effect=tarfile.TarError)

    mocker.patch.object(FileUtil, 'rchmod')

    if raises_error:
        result = utools._install_licenses(mod_all, top_dir, tar_dir, force)
        logger.error.called
        assert log_error in logger.error.call_args[0][0]
    else:
        result = utools._install_licenses(mod_all, top_dir, tar_dir, force)
        if log_debug:
            assert logger.debug.called
            assert log_debug in logger.debug.call_args[0][0]
        elif log_info:
            assert logger.info.called
            assert log_info in logger.info.call_args[0][0]

    assert result == expected_result


def test_20_install_modules(mocker, utools):
    """Test20 UdockerTools().install_modules()."""
    lmods = [MOD1]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_downtar = mocker.patch.object(UdockerTools, 'download_tarballs')
    mock_inst = mocker.patch.object(UdockerTools, '_instructions')
    utools._installretry = 1
    utools._autoinstall = False
    resout = utools.install_modules([1], 'inst_dir', 'tar_dir', False)
    assert not resout
    mock_selmod.assert_called()
    mock_downtar.assert_not_called()
    mock_inst.assert_not_called()


def test_21_install_modules(mocker, utools):
    """Test21 UdockerTools().install_modules()."""
    lmods = [MOD1]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_downtar = mocker.patch.object(UdockerTools, 'download_tarballs', return_value=True)
    mock_downlic = mocker.patch.object(UdockerTools, 'download_licenses', return_value=True)
    mock_instlog = mocker.patch.object(UdockerTools, '_installmod_logic', return_value=True)
    mock_instlic = mocker.patch.object(UdockerTools, '_install_licenses', return_value=True)
    mock_inst = mocker.patch.object(UdockerTools, '_instructions')
    utools._installretry = 1
    resout = utools.install_modules([1], 'inst_dir', 'tar_dir', True)
    assert resout
    mock_selmod.assert_called()
    mock_downtar.assert_called()
    mock_downlic.assert_called()
    mock_instlog.assert_called()
    mock_instlic.assert_called()
    mock_inst.assert_not_called()


def test_22_install_modules(mocker, utools):
    """Test22 UdockerTools().install_modules()."""
    lmods = [MOD1]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_downtar = mocker.patch.object(UdockerTools, 'download_tarballs', return_value=False)
    mock_downlic = mocker.patch.object(UdockerTools, 'download_licenses', return_value=False)
    mock_instlog = mocker.patch.object(UdockerTools, '_installmod_logic', return_value=True)
    mock_instlic = mocker.patch.object(UdockerTools, '_install_licenses', return_value=True)
    mock_inst = mocker.patch.object(UdockerTools, '_instructions')
    utools._installretry = 1
    resout = utools.install_modules([1], 'inst_dir', 'tar_dir', True)
    assert not resout
    mock_selmod.assert_called()
    mock_downtar.assert_called()
    mock_downlic.assert_called()
    mock_instlog.assert_called()
    mock_instlic.assert_called()
    mock_inst.assert_called()


def test_23_get_modules(mocker, utools):
    """Test23 UdockerTools().get_modules()."""
    lmods = [MOD1, MOD2]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile', return_value=True)
    mock_jload = mocker.patch('udocker.tools.json.load', return_value=lmods)
    mock_jfile = mocker.mock_open(read_data=str(lmods))
    mocker.patch("builtins.open", mock_jfile)
    resout = utools.get_modules([], 'show', 'mod_dir')
    assert resout == lmods
    mock_isfile.assert_called()
    mock_jload.assert_called()
    mock_selmod.assert_not_called()


def test_24_get_modules(mocker, utools):
    """Test24 UdockerTools().get_modules()."""
    lmods = [MOD1, MOD2]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_isfile = mocker.patch('udocker.tools.os.path.isfile', return_value=True)
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = utools.get_modules([], 'show', 'mod_dir')
    assert resout == []
    mock_isfile.assert_called()
    mock_selmod.assert_not_called()

@pytest.mark.parametrize("action, list_uid, expected_result, write_error", [
    ('update', ['uid1'], {MOD1['uid'], MOD2['uid']}, False),  # Update action, add a new module
    ('delete', ['uid1'], {MOD2['uid']}, False),               # Delete action, remove an existing module
    ('update', ['uid1'], set(), True),                        # Update action, but file write fails
])
def test_25_get_modules(mocker, utools, logger, action, list_uid, expected_result, write_error):
    """Test25 UdockerTools().get_modules()."""
    lmods = [MOD2]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=[MOD1])
    mock_isfile = mocker.patch.object(os.path, 'isfile', return_value=True)
    mock_jload = mocker.patch.object(json, 'load', return_value=lmods)
    mock_jdump = mocker.patch.object(json, 'dump')
    mock_jfile = mocker.mock_open(read_data=str(lmods))
    mocker.patch("builtins.open", mock_jfile)

    if write_error:
        mock_jfile.side_effect = OSError

    utools.get_modules(list_uid, action, 'mod_dir')
    mock_isfile.assert_called_once()
    if not write_error:
        mock_jload.assert_called_once()

    if action == 'update' and not write_error:
        mock_selmod.assert_called_with(list_uid, [])
        if not write_error:
            actual_uids = {mod['uid'] for mod in mock_jdump.call_args[0][0]}
            assert actual_uids == expected_result
    elif action == 'delete' and not write_error:
        mock_selmod.assert_called_with(list_uid, [])
        if not write_error:
            actual_uids = {mod['uid'] for mod in mock_jdump.call_args[0][0]}
            assert actual_uids == expected_result

def test_26_rm_module(mocker, utools):
    """Test26 UdockerTools().rm_module()."""
    lmods = [MOD1, MOD4]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_getmod = mocker.patch.object(UdockerTools, 'get_modules')
    mock_futil = mocker.patch('udocker.tools.FileUtil')
    mock_futil.return_value.register_prefix.side_effect = [None, None]
    mock_futil.return_value.remove.side_effect = [None, None]
    resout = utools.rm_module(['dummy'], '')
    assert resout
    mock_selmod.assert_called()
    assert mock_futil.return_value.register_prefix.call_count == 2
    assert mock_futil.return_value.remove.call_count == 2
    mock_getmod.assert_not_called()

def test_27_rm_module(mocker, utools):
    """Test27 UdockerTools().rm_module() empty list_uid."""
    mock_getmod = mocker.patch.object(UdockerTools, 'get_modules', return_value=[])
    mock_oslistdir = mocker.patch('os.listdir', return_value=['file1', 'file2'])
    mock_futil = mocker.patch('udocker.tools.FileUtil')
    mock_futil.return_value.register_prefix.side_effect = [None, None]
    mock_futil.return_value.remove.side_effect = [None, None]

    resout = utools.rm_module([], '')
    assert resout
    mock_getmod.assert_called()
    mock_oslistdir.assert_called_once_with(utools.localrepo.docdir)
    assert mock_futil.return_value.register_prefix.call_count == 2
    assert mock_futil.return_value.remove.call_count == 2

def test_28_rm_module(mocker, utools):
    """Test28 UdockerTools().rm_module() non-empty list_uid and prefix."""
    lmods = [MOD1, MOD4]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_futil_register_prefix = mocker.patch.object(FileUtil, 'register_prefix')
    mock_futil_remove = mocker.patch.object(FileUtil, 'remove')

    prefix = '/custom/prefix'
    resout = utools.rm_module(['dummy'], prefix)
    assert resout
    mock_selmod.assert_called()
    assert mock_futil_register_prefix.call_count == len(lmods)
    assert mock_futil_remove.call_count == len(lmods)

def test_29_rm_module(mocker, utools):
    """Test29 UdockerTools().rm_module() no modules selected."""
    lmods = [{'installdir': 'unknown/', 'fname': 'unknown_file'}]
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)

    resout = utools.rm_module(['dummy'], '')
    assert not resout
    mock_selmod.assert_called()

# def test_26_rm_module(mocker, utools):
#     """Test26 UdockerTools().rm_module()."""
#     lmods = [MOD1]
#     mock_selmod = mocker.patch.object(UdockerTools, '_select_modules')
#     mock_getmod = mocker.patch.object(UdockerTools, 'get_modules', return_value=lmods)
#     mock_lsdir = mocker.patch('udocker.tools.os.listdir', return_value='some_lic')
#     mock_futilreg = mocker.patch('udocker.tools.FileUtil.register_prefix',
#                                  side_effect=[None, None])
#     mock_futilrm = mocker.patch('udocker.tools.FileUtil.remove', side_effect=[None, None])
#     resout = utools.rm_module([], '')
#     assert resout
#     mock_selmod.assert_called()
#     assert mock_futilreg.call_count == 3
#     assert mock_futilrm.call_count == 3
#     mock_getmod.assert_not_called()
