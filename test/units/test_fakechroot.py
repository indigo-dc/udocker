#!/usr/bin/env python
"""
udocker unit tests: FakechrootEngine
"""
import configparser
import os
import pytest
import random

from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.execmode import ExecutionMode
from udocker.config import Config

XMODE = ["P1", "P2"]


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    return mocker.patch('udocker.container.localrepo.LocalRepository')


@pytest.fixture(autouse=True)
@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture
def ufake(localrepo, mock_exec_mode, container_id):
    fakeroot = FakechrootEngine(localrepo, mock_exec_mode)
    fakeroot.container_id = container_id
    fakeroot.container_dir = "/tmp"
    return fakeroot


@pytest.fixture
def mock_os_path_exists(mocker):
    return mocker.patch('udocker.engine.fakechroot.os.path.exists')


@pytest.fixture
def osinfo(mocker):
    return mocker.patch('udocker.helper.osinfo.OSInfo')


@pytest.fixture
def mock_osinfo_osdistribution(mocker):
    return mocker.patch('udocker.helper.osinfo.OSInfo.osdistribution', return_value=('linux', '4.8.1'))


@pytest.fixture
def mock_fileutil_find_file_in_dir(mocker):
    return mocker.patch('udocker.utils.fileutil.FileUtil.find_file_in_dir')


@pytest.fixture
def mock_setup_container_user_noroot(mocker):
    return mocker.patch('udocker.engine.fakechroot.ExecutionEngineCommon._setup_container_user_noroot')


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch('udocker.engine.fakechroot.LOG')


@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_01__init(ufake):
    """Test01 FakechrootEngine Constructor."""
    assert ufake._fakechroot_so == ""
    assert ufake._elfpatcher is None
    assert ufake._recommend_expand_symlinks is False


select_fakechroot_so_data = (
    ("", [True, True, True, True, True, True], ("linux", "4.8.1"), "/tmp/libfakechroot.so"),
    ("", [False, True, True, True, True, True], ("linux", "4.8.1"), "/tmp/libfakechroot.so"),
    ("", [False, False, False, False, False, False], ("linux", "4.8.1"), "/tmp/libfakechroot.so"),
    ("/s/fake1", [False, True, True, True, True, True], ("linux", "4.8.1"), "/tmp/libfakechroot.so"),
    ("/s/fake1", [True, True, True, True, True, True], ("linux", "4.8.1"), "/tmp/libfakechroot.so"),
    (["/s/fake1", ], [False, True, True, True, True, True], ("linux", "4.8.1"), "/tmp/libfakechroot.so"),
    (["/s/fake1", ], [False, True, True, True, True, True], ("Alpine", "4.8.1"), "/tmp/libfakechroot.so"),
)


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('fakechroot_so,os_exist,os_info,expected', select_fakechroot_so_data)
def test_02_select_fakechroot_so(ufake, fakechroot_so, os_exist, mock_os_path_exists, expected, os_info, osinfo,
                                 mock_fileutil_find_file_in_dir):
    """Test02 FakechrootEngine.select_fakechroot_so."""

    Config.conf['fakechroot_so'] = fakechroot_so
    mock_os_path_exists.side_effect = os_exist
    osinfo.return_value.osdistribution.return_value = os_info
    mock_fileutil_find_file_in_dir.return_value = "/tmp/libfakechroot.so"

    select = ufake.select_fakechroot_so()
    assert select == expected


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('user', ["user1", "root"])
def test_03__setup_container_user(ufake, mock_setup_container_user_noroot, user):
    """Test03 FakechrootEngine._setup_container_user()."""
    ufake._setup_container_user(user=user)
    assert mock_setup_container_user_noroot.call_count == 1


@pytest.mark.parametrize('user', [("user1", 0), ("root", 1), ("0", 1), ("", 0)])
@pytest.mark.parametrize('xmode', XMODE)
def test_04__uid_check(ufake, user, mock_logger, mocker):
    """Test04 FakechrootEngine._uid_check()."""
    ufake.opt["user"] = user[0]
    ufake._uid_check()
    assert mock_logger.warning.call_count == user[1]
    if user[1] > 0:
        assert mock_logger.warning.call_args_list == [mocker.call("this engine does not support execution as root")]
    ufake.opt.pop("user")
    mock_logger.warning.call_count == 0

    # @patch('udocker.engine.fakechroot.os.path.isdir')
    # @patch('udocker.engine.fakechroot.os.path.realpath')


@pytest.mark.parametrize('xmode', XMODE)
def test_05__get_volume_bindings(ufake, mocker):
    """Test05 FakechrootEngine._get_volume_bindings()."""
    ufake.opt["vol"] = ()
    status = ufake._get_volume_bindings()
    assert status == ('', '')
    #
    # mock_rpath.side_effect = ["/tmp", "/bin"]
    # mock_isdir.side_effect = [True, False, True]
    # ufake = FakechrootEngine(self.local, self.xmode)
    # dtmp = os.path.realpath("/tmp")
    # dbin = os.path.realpath("/bin")
    # ufake.opt["vol"] = (dtmp, dbin)
    # status = ufake._get_volume_bindings()
    # if status[1].startswith(dtmp):
    #     self.assertEqual(status, ('', dtmp + '!' + dtmp + ':' + dbin + '!' + dbin))
    # else:
    #     self.assertEqual(status, ('', dbin + '!' + dbin + ':' + dtmp + '!' + dtmp))


@pytest.mark.parametrize('xmode', XMODE)
def test_06__get_access_filesok(ufake):
    """Test06 FakechrootEngine._get_access_filesok()."""
    Config.conf['access_files'] = ("/sys/infin",)
    ufake.opt["vol"] = ("/tmp",)
    out = ufake._get_access_filesok()
    assert out == "/sys/infin"


@pytest.mark.parametrize('xmode', XMODE)
def test_07__fakechroot_env_set(ufake):
    """Test07 FakechrootEngine._fakechroot_env_set()."""
    ufake._fakechroot_env_set()


@pytest.mark.parametrize('xmode', XMODE)
def test_08__run_invalid_options(ufake):
    """Test08 FakechrootEngine._run_invalid_options()"""
    ufake._run_invalid_options()


@pytest.mark.parametrize('xmode', XMODE)
def test_09__run_add_script_support(ufake):
    """Test09 FakechrootEngine._run_add_script_support()"""
    ufake._run_add_script_support("/bin/ls")


run_data = (
    ("/bin/bash", ""),
    ("/bin/bash", ""),
)

@pytest.fixture
def mock_elphpatcher(mocker):
    return mocker.patch('udocker.engine.fakechroot.ElfPatcher')


@pytest.mark.parametrize('xmode', XMODE)
def test_10_run(ufake, container_id, xmode, mock_elphpatcher):
    """Test10 FakechrootEngine.run()."""
    #ufake._check_arch = lambda: True
    ufake._run_init = lambda container_id: "/bin/bash"
    ufake.exec_mode.get_mode = lambda: xmode
    ufake._elfpatcher = mock_elphpatcher
    ufake.run(container_id)


# from unittest import TestCase, main
# from unittest.mock import patch, Mock
# from udocker.config import Config

# import collections
# collections.Callable = collections.abc.Callable
#
#
# class FakechrootEngineTestCase(TestCase):
#     """Docker container execution engine using Fakechroot
#     Provides a chroot like environment to run containers.
#     Uses Fakechroot as chroot alternative.
#     Inherits from ContainerEngine class
#     """
#
#     def setUp(self):
#         LOG.setLevel(100)
#         Config().getconf()
#         Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
#         Config().conf['cmd'] = "/bin/bash"
#         Config().conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
#                                                     ["taskset", "-c", "%s", ])
#         Config().conf['valid_host_env'] = "HOME"
#         Config().conf['username'] = "user"
#         Config().conf['userhome'] = "/"
#         Config().conf['oskernel'] = "4.8.13"
#         Config().conf['location'] = ""
#
#         str_local = 'udocker.container.localrepo.LocalRepository'
#         self.lrepo = patch(str_local)
#         self.local = self.lrepo.start()
#         self.mock_lrepo = Mock()
#         self.local.return_value = self.mock_lrepo
#
#         str_exmode = 'udocker.engine.execmode.ExecutionMode'
#         self.execmode = patch(str_exmode)
#         self.xmode = self.execmode.start()
#         self.mock_execmode = Mock()
#         self.xmode.return_value = self.mock_execmode
#
#     def tearDown(self):
#         self.lrepo.stop()
#         self.execmode.stop()
#
#     def test_01__init(self):
#         """Test01 FakechrootEngine Constructor."""
#         ufake = FakechrootEngine(self.local, self.xmode)
#         self.assertEqual(ufake._fakechroot_so, "")
#         self.assertIsNone(ufake._elfpatcher)
#
#     @patch('udocker.engine.fakechroot.sys.exit')
#     @patch('udocker.engine.fakechroot.OSInfo')
#     @patch('udocker.engine.fakechroot.os.path.realpath')
#     @patch('udocker.engine.fakechroot.os.path.exists')
#     @patch('udocker.engine.fakechroot.FileUtil')
#     def test_02_select_fakechroot_so(self, mock_futil, mock_exists,
#                                      mock_rpath, mock_osinfo, mock_sysex):
#         """Test02 FakechrootEngine.select_fakechroot_so."""
#         Config().conf['fakechroot_so'] = "/s/fake1"
#         mock_exists.return_value = True
#         mock_rpath.return_value = "/s/fake1"
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake.select_fakechroot_so()
#         self.assertEqual(out, "/s/fake1")
#
#         Config().conf['fakechroot_so'] = ""
#         mock_exists.return_value = True
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake.select_fakechroot_so()
#         self.assertEqual(out, "/libfakechroot.so")
#
#         Config().conf['fakechroot_so'] = ""
#         mock_exists.return_value = False
#         mock_osinfo.return_value.arch.return_value = "amd64"
#         mock_osinfo.return_value.osdistribution.return_value = ("linux", "4.8.1")
#         mock_futil.return_value.find_file_in_dir.return_value = ""
#         mock_sysex.return_value = 1
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake.select_fakechroot_so()
#         self.assertTrue(mock_sysex.called)
#         self.assertTrue(mock_futil.called)
#
#         Config().conf['fakechroot_so'] = ""
#         mock_exists.return_value = False
#         mock_osinfo.return_value.arch.return_value = "amd64"
#         mock_osinfo.return_value.osdistribution.return_value = ("linux", "4.8.1")
#         mock_futil.return_value.find_file_in_dir.return_value = "/libfakechroot.so"
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake.select_fakechroot_so()
#         self.assertTrue(mock_futil.called)
#         self.assertEqual(out, "/libfakechroot.so")
#
#         Config().conf['fakechroot_so'] = ""
#         mock_exists.return_value = False
#         mock_osinfo.return_value.arch.return_value = "i386"
#         mock_osinfo.return_value.osdistribution.return_value = ("linux", "4.8.1")
#         mock_futil.return_value.find_file_in_dir.return_value = "/libfakechroot.so"
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake.select_fakechroot_so()
#         self.assertTrue(mock_futil.called)
#         self.assertEqual(out, "/libfakechroot.so")
#
#         Config().conf['fakechroot_so'] = ""
#         mock_exists.return_value = False
#         mock_osinfo.return_value.arch.return_value = "arm64"
#         mock_osinfo.return_value.osdistribution.return_value = ("linux", "4.8.1")
#         mock_futil.return_value.find_file_in_dir.return_value = "/libfakechroot.so"
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake.select_fakechroot_so()
#         self.assertTrue(mock_futil.called)
#         self.assertEqual(out, "/libfakechroot.so")
#
#     @patch('udocker.engine.fakechroot.ExecutionEngineCommon._setup_container_user_noroot')
#     def test_03__setup_container_user(self, mock_cmm):
#         """Test03 FakechrootEngine._setup_container_user()."""
#         mock_cmm.return_value = True
#         ufake = FakechrootEngine(self.local, self.xmode)
#         status = ufake._setup_container_user("someuser")
#         self.assertTrue(mock_cmm.called)
#         self.assertTrue(status)
#
#     @patch('udocker.engine.fakechroot.LOG')
#     def test_04__uid_check(self, mock_log):
#         """Test04 FakechrootEngine._uid_check()."""
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.opt["user"] = "0"
#         ufake._uid_check()
#         self.assertTrue(mock_log.warning.called)
#
#     @patch('udocker.engine.fakechroot.os.path.isdir')
#     @patch('udocker.engine.fakechroot.os.path.realpath')
#     def test_05__get_volume_bindings(self, mock_rpath, mock_isdir):
#         """Test05 FakechrootEngine._get_volume_bindings()."""
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.opt["vol"] = ()
#         status = ufake._get_volume_bindings()
#         self.assertEqual(status, ('', ''))
#
#         mock_rpath.side_effect = ["/tmp", "/bin"]
#         mock_isdir.side_effect = [True, False, True]
#         ufake = FakechrootEngine(self.local, self.xmode)
#         dtmp = os.path.realpath("/tmp")
#         dbin = os.path.realpath("/bin")
#         ufake.opt["vol"] = (dtmp, dbin)
#         status = ufake._get_volume_bindings()
#         if status[1].startswith(dtmp):
#             self.assertEqual(status, ('', dtmp+'!'+dtmp+':'+dbin+'!'+dbin))
#         else:
#             self.assertEqual(status, ('', dbin+'!'+dbin+':'+dtmp+'!'+dtmp))
#
#     @patch('udocker.engine.fakechroot.os.path.exists')
#     @patch('udocker.engine.fakechroot.FileUtil.cont2host')
#     def test_06__get_access_filesok(self, mock_cont2host, mock_exists):
#         """Test06 FakechrootEngine._get_access_filesok()."""
#         Config.conf['access_files'] = ("/sys/infin",)
#         mock_cont2host.return_value = "/c/sys/infin"
#         mock_exists.return_value = False
#         ufake = FakechrootEngine(self.local, self.xmode)
#         out = ufake._get_access_filesok()
#         self.assertEqual(out, "")
#
#         Config.conf['access_files'] = ("/sys/infin",)
#         mock_cont2host.return_value = "/c/sys/infin"
#         mock_exists.return_value = True
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.opt["vol"] = ("/tmp",)
#         out = ufake._get_access_filesok()
#         self.assertTrue(mock_cont2host.called)
#         self.assertTrue(mock_exists.called)
#         self.assertEqual(out, "/sys/infin")
#
#     @patch.object(FakechrootEngine, '_get_volume_bindings')
#     @patch.object(FakechrootEngine, 'select_fakechroot_so')
#     @patch.object(FakechrootEngine, '_get_access_filesok')
#     @patch.object(FakechrootEngine, '_is_volume')
#     @patch('udocker.engine.fakechroot.os.path.realpath')
#     @patch('udocker.engine.fakechroot.ElfPatcher')
#     @patch('udocker.engine.fakechroot.FileUtil')
#     def test_07__fakechroot_env_set(self, mock_futil, mock_elf, mock_rpath, mock_isvol, mock_fok,
#                                     mock_sel, mock_getvol):
#         """Test07 FakechrootEngine._fakechroot_env_set()."""
#         Config.conf['fakechroot_expand_symlinks'] = None
#         mock_getvol.return_value = ('v1:v2', 'm1:m2')
#         mock_sel.return_value = '/ROOT/lib/libfakechroot.so'
#         mock_fok.return_value = "/sys/infin"
#         mock_rpath.return_value = '/bin/fake.so'
#         mock_elf.return_value.get_ld_library_path.return_value = '/a'
#         mock_elf.return_value.get_container_loader.return_value = '/ROOT/elf'
#         mock_futil.return_value.find_file_in_dir.return_value = True
#         mock_isvol.return_value = False
#         self.xmode.get_mode.return_value = 'F1'
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake._elfpatcher = mock_elf
#         ufake._fakechroot_env_set()
#         self.assertTrue(self.xmode.get_mode.called)
#         self.assertTrue(mock_getvol.called)
#         self.assertTrue(mock_sel.called)
#         self.assertTrue(mock_fok.called)
#         self.assertTrue(mock_rpath.called)
#         self.assertTrue(mock_isvol.called)
#
#         Config.conf['fakechroot_expand_symlinks'] = None
#         mock_getvol.return_value = ('v1:v2', 'm1:m2')
#         mock_sel.return_value = '/ROOT/lib/libfakechroot.so'
#         mock_fok.return_value = "/sys/infin"
#         mock_rpath.return_value = '/bin/fake.so'
#         mock_elf.return_value.get_ld_library_path.return_value = '/a'
#         mock_elf.return_value.select_patchelf.return_value = '/ROOT/elf'
#         mock_elf.return_value.get_patch_last_time.return_value = '/ROOT/elf'
#         mock_elf.return_value.get_container_loader.return_value = '/ROOT/elf'
#         mock_futil.return_value.find_file_in_dir.return_value = True
#         mock_isvol.return_value = False
#         self.xmode.get_mode.return_value = 'F4'
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake._elfpatcher = mock_elf
#         ufake._fakechroot_env_set()
#         self.assertTrue(mock_getvol.called)
#         self.assertTrue(mock_sel.called)
#         self.assertTrue(mock_fok.called)
#         self.assertTrue(mock_rpath.called)
#         self.assertTrue(mock_isvol.called)
#
#     @patch('udocker.engine.fakechroot.LOG')
#     def test_08__run_invalid_options(self, mock_log):
#         """Test08 FakechrootEngine._run_invalid_options()"""
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.opt['netcoop'] = False
#         ufake.opt['portsmap'] = True
#         ufake._run_invalid_options()
#         self.assertTrue(mock_log.warning.called)
#
#         ufake.opt['netcoop'] = True
#         ufake.opt['portsmap'] = False
#         ufake._run_invalid_options()
#         self.assertTrue(mock_log.warning.called)
#
#     @patch('udocker.engine.fakechroot.FileUtil.get1stline')
#     @patch('udocker.engine.fakechroot.FileUtil.cont2host')
#     @patch('udocker.engine.fakechroot.FileUtil.find_exec')
#     @patch('udocker.engine.fakechroot.OSInfo.get_filetype')
#     def test_09__run_add_script_support(self, mock_ftype, mock_findexe, mock_cont2host, mock_1stl):
#         """Test09 FakechrootEngine._run_add_script_support()"""
#         mock_ftype.return_value = "/bin/ls: ELF, x86-64, static"
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.opt["cmd"] = [""]
#         status = ufake._run_add_script_support("/bin/ls")
#         self.assertEqual(status, [])
#
#         mock_ftype.return_value = "/bin/ls: xxx, x86-64, yyy"
#         mock_findexe.side_effect = ["ls", ""]
#         ufake = FakechrootEngine(self.local, self.xmode)
#         status = ufake._run_add_script_support("/bin/ls")
#         self.assertEqual(status, ["/ls"])
#
#         mock_ftype.return_value = "/bin/ls: xxx, x86-64, yyy"
#         mock_findexe.side_effect = ["", "ls"]
#         mock_cont2host.return_value = "/bin/ls"
#         mock_1stl.return_value = ""
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.container_root = "/ROOT"
#         status = ufake._run_add_script_support("/bin/ls")
#         self.assertEqual(status, ["/ROOT/ls"])
#
#     @patch('udocker.engine.fakechroot.FileUtil.cont2host')
#     @patch.object(FakechrootEngine, '_run_banner')
#     @patch.object(FakechrootEngine, '_run_add_script_support')
#     @patch.object(FakechrootEngine, '_set_cpu_affinity')
#     @patch.object(FakechrootEngine, '_run_env_cleanup_list')
#     @patch.object(FakechrootEngine, '_fakechroot_env_set')
#     @patch.object(FakechrootEngine, '_run_env_set')
#     @patch.object(FakechrootEngine, '_run_invalid_options')
#     @patch.object(FakechrootEngine, '_run_init')
#     @patch.object(FakechrootEngine, '_uid_check')
#     @patch('udocker.engine.fakechroot.subprocess.call')
#     @patch('udocker.engine.fakechroot.ElfPatcher')
#     def test_10_run(self, mock_elfp, mock_call, mock_uidc, mock_rinit, mock_rinval, mock_renv,
#                     mock_fakeenv, mock_renvclean, mock_setaff, mock_raddsup, mock_runban, mock_c2h):
#         """Test10 FakechrootEngine.run()."""
#         mock_uidc.return_value = None
#         mock_rinit.return_value = ""
#         ufake = FakechrootEngine(self.local, self.xmode)
#         status = ufake.run("12345")
#         self.assertEqual(status, 2)
#
#         mock_uidc.return_value = None
#         mock_rinit.return_value = '/bin/exec'
#         mock_rinval.return_value = None
#         self.xmode.get_mode.return_value = 'F1'
#         mock_elfp.return_value.check_container_path.return_value = False
#         mock_renv.return_value = None
#         mock_fakeenv.return_value = None
#         mock_renvclean.return_value = None
#         mock_setaff.return_value = ['1', '2']
#         mock_elfp.return_value.get_container_loader.return_value = '/ROOT/xx'
#         mock_raddsup.return_value = ['/ROOT/xx.sh']
#         mock_runban.return_value = None
#         mock_c2h.return_value = "/cont/ROOT"
#         mock_call.return_value = 0
#         ufake = FakechrootEngine(self.local, self.xmode)
#         ufake.opt["cmd"] = [""]
#         status = ufake.run("12345")
#         self.assertEqual(status, 0)
#         self.assertTrue(mock_uidc.called)
#         self.assertTrue(mock_rinit.called)
#         self.assertTrue(mock_call.called)
#
#
# if __name__ == '__main__':
#     main()
