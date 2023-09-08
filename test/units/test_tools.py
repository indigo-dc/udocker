#!/usr/bin/env python
"""
udocker unit tests: UdockerTools
"""
import pytest
import tarfile
from tarfile import TarFile, TarInfo
from udocker.config import Config
from udocker.utils.curl import CurlHeader
from udocker.tools import UdockerTools


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
def utools(mocker, lrepo, get_url):
    return UdockerTools(lrepo)


@pytest.fixture
def cnf():
    Config().getconf()
    return Config()


@pytest.fixture
def logger(mocker):
    mock_log = mocker.patch('udocker.tools.LOG')
    return mock_log


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


data_getfile = (('', None, 0, False, 1, None, 0, False, 0, 0, '', ''),
                ('https://down/f1', 'f1', 1, False, 0, None, 0, True, 1, 0, '', 'f1'),
                ('/tmp/f1', '', 0, True, 1, 'f1', 1, True, 1, 0, '', 'f1'),
                ('/tmp/f1', '', 0, True, 1, 'f1', 1, True, 1, 1, 'someout', 'f1')
                )


@pytest.mark.parametrize('url,mdownl,cdownl,mexists,cexists,mrpath,crpath,misfile,cisfile,cshucp,fout,expected', data_getfile)
def test_04__get_file(mocker, utools, url, mdownl, cdownl, mexists, cexists, mrpath, crpath,
                      misfile, cisfile, cshucp, fout, expected):
    """Test04 UdockerTools()._get_file()."""
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


# def test_05__clean_install(mocker, utools, lrepo):
#     """Test05 UdockerTools()._clean_install()."""
#     lrepo.bindir.return_value = '/bin'
#     lrepo.libdir.return_value = '/lib'
#     lrepo.docdir.return_value = '/doc'
#     # mock_osbase = mocker.patch('udocker.tools.os.path.basename',
#     #                            side_effect=['udocker_dir', 'udocker_dir', 'udocker_dir'])
#     mock_furegpref = mocker.patch('udocker.tools.FileUtil.register_prefix',
#                                   side_effect=[None, None, None])
#     mock_furm = mocker.patch('udocker.tools.FileUtil.remove', side_effect=[None, None, None])
#     with tarfile.TarFile('', mode='w') as tfile:
#         tfile.add('udocker_dir/bin/crun', arcname='crun')
#         tfile.add('udocker_dir/lib/libfchroot.so', arcname='libfchroot.so')
#         tfile.add('udocker_dir/doc/license.txt', arcname='license.txt')

#     utools._clean_install(tfile)
#     # assert mock_osbase.call_count == 3
#     lrepo.bindir.assert_called()
#     lrepo.libdir.assert_called()
#     lrepo.docdir.assert_called()
#     assert mock_furegpref.call_count == 3
#     assert mock_furm.call_count == 3


#     # tfile = TarFile(name='sometar')
#     # tfile.addfile(TarInfo("udocker_dir/bin/crun"))
#     # tfile.addfile(TarInfo("udocker_dir/lib/libfchroot.so"))
#     # tfile.addfile(TarInfo("udocker_dir/doc/license.txt"))

#     tfile = [TarInfo("udocker_dir/bin/crun"), TarInfo("udocker_dir/lib/libfchroot.so"),
#              TarInfo("udocker_dir/doc/license.txt")]

#     # mock_tfile = mocker.patch('udocker.tools.tarfile.TarFile.getmembers', return_value=tfile)

#     lrepo.bindir.return_value = '/bin'
#     lrepo.libdir.return_value = '/lib'
#     lrepo.docdir.return_value = '/doc'
#     mock_osbase = mocker.patch('udocker.tools.os.path.basename',
#                                side_effect=['udocker_dir', 'udocker_dir', 'udocker_dir'])
#     mock_furegpref = mocker.patch('udocker.tools.FileUtil.register_prefix',
#                                   side_effect=[None, None, None])
#     mock_furm = mocker.patch('udocker.tools.FileUtil.remove', side_effect=[None, None, None])


#     # utools._clean_install(mock_tfile)
#     # assert mock_osbase.call_count == 3
#     # lrepo.bindir.assert_called()
#     # lrepo.libdir.assert_called()
#     # lrepo.docdir.assert_called()
#     # assert mock_furegpref.call_count == 3
#     # assert mock_furm.call_count == 3

#     with mocker.patch.object(tarfile, 'open', autospec=True) as open_mock:
#         open_mock.return_value.getmembers.return_value = tfile
#         utools._clean_install(open_mock)
#         assert mock_osbase.call_count == 3
#         lrepo.bindir.assert_called()
#         lrepo.libdir.assert_called()
#         lrepo.docdir.assert_called()
#         assert mock_furegpref.call_count == 3
#         assert mock_furm.call_count == 3


def test_06__get_mirrors(mocker, utools):
    """Test06 UdockerTools()._get_mirrors()."""
    mirrors = "https://download.ncg.ingrid.pt/udocker-1.2.7.tar.gz"
    out = utools._get_mirrors(mirrors)
    assert out == [mirrors]


def test_07_get_metadata(mocker, utools):
    """Test07 UdockerTools().get_metadata()."""
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


def test_08_get_metadata(mocker, utools):
    """Test08 UdockerTools().get_metadata()."""
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
def test_09__select_modules(mocker, utools, list_uid, list_names, sekgreat, expected):
    """Test09 UdockerTools()._select_modules()."""
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
def test_10_verify_sha(mocker, utools, lmods, lsha, expected):
    """Test10 UdockerTools().verify_sha()."""
    mock_sha = mocker.patch('udocker.tools.ChkSUM.sha256', side_effect=lsha)
    resout = utools.verify_sha(lmods, 'udocker/tar')
    assert resout == expected
    assert mock_sha.call_count == 2


data_downtar = ((True, True, 2, True),
                (False, False, 0, False))


@pytest.mark.parametrize('vsha,force,cgetfile,expected', data_downtar)
def test_11_download_tarballs(mocker, utools, vsha, force, cgetfile, expected):
    """Test11 UdockerTools().download_tarballs()."""
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
def test_12_delete_tarballs(mocker, utools, listuid, cselmod, cgetmeta):
    """Test12 UdockerTools().delete_tarballs()."""
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


def test_13_delete_tarballs(mocker, utools):
    """Test13 UdockerTools().delete_tarballs()."""
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
def test_14_download_licenses(mocker, utools, force, mgetfile, cgetfile, expected):
    """Test14 UdockerTools().download_licenses()."""
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
def test_15_show_metadata(mocker, utools, long, cmsg):
    """Test15 UdockerTools().show_metadata()."""
    mock_msg = mocker.patch('udocker.tools.MSG.info')
    assert utools.show_metadata([MOD1], long)
    assert mock_msg.call_count == cmsg


data_instlog = (([1], 1, 0),
               ([], 0, 1))


@pytest.mark.parametrize('lmods,force,expected', data_instlog)
def test_16__installmod_logic(mocker, utools, lmods, force, expected):
    """Test16 UdockerTools()._installmod_logic()."""
    mock_selmod = mocker.patch.object(UdockerTools, '_select_modules', return_value=lmods)
    mock_futil = mocker.patch('udocker.tools.FileUtil.rchmod', side_effect=[None, None])

    resout = utools._installmod_logic([1], 'top_dir', 'tar_dir', force)
    assert resout

